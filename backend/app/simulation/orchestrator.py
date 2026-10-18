import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from backend.app.database import async_session_maker
from backend.app.models.experiment import Experiment
from backend.app.models.synthetic_user import SyntheticUser
from backend.app.models.trajectory import TrajectoryStep
from backend.app.models.metrics import ExperimentMetrics
from backend.app.models.finding import FrictionFinding
from backend.app.simulation.population import PopulationGenerator
from backend.app.simulation.runner import SingleUserSimulationRunner
from backend.app.simulation.decision import get_llm_provider
from backend.app.analysis.metrics import MetricsCalculator
from backend.app.analysis.aggregation import FunnelAndHeatmapAggregator
from backend.app.analysis.anomaly import ConfusionAndFrictionDetector
from backend.app.simulation.events import event_bus

logger = logging.getLogger(__name__)

# In-memory tracking of active background simulation tasks
ACTIVE_TASKS = {}

class ExperimentOrchestrator:
    """Coordinates population generation, concurrent Playwright simulations, and automated analysis."""

    @classmethod
    async def start_experiment(cls, experiment_id: str, concurrency: Optional[int] = None):
        """Dispatches experiment execution in background asyncio task."""
        if experiment_id in ACTIVE_TASKS and not ACTIVE_TASKS[experiment_id].done():
            logger.warning(f"Experiment {experiment_id} is already running.")
            return

        task = asyncio.create_task(cls._execute_experiment_job(experiment_id, concurrency))
        ACTIVE_TASKS[experiment_id] = task

    @classmethod
    async def cancel_experiment(cls, experiment_id: str):
        """Cancels an ongoing experiment job."""
        if experiment_id in ACTIVE_TASKS:
            task = ACTIVE_TASKS[experiment_id]
            if not task.done():
                task.cancel()
        async with async_session_maker() as session:
            await session.execute(
                update(Experiment)
                .where(Experiment.id == experiment_id)
                .values(status="CANCELLED", completed_at=datetime.now(timezone.utc))
            )
            await session.commit()
        await event_bus.publish(experiment_id, {"type": "experiment_finish", "status": "CANCELLED"})

    @classmethod
    async def _execute_experiment_job(cls, experiment_id: str, concurrency_override: Optional[int] = None):
        logger.info(f"Starting execution job for experiment: {experiment_id}")
        try:
            async with async_session_maker() as session:
                stmt = select(Experiment).where(Experiment.id == experiment_id)
                res = await session.execute(stmt)
                experiment = res.scalar_one_or_none()
                if not experiment:
                    logger.error(f"Experiment {experiment_id} not found.")
                    return

                # Update status to RUNNING
                experiment.status = "RUNNING"
                experiment.started_at = datetime.now(timezone.utc)
                await session.commit()
                await event_bus.publish(experiment_id, {"type": "experiment_start", "status": "RUNNING"})

                # Generate synthetic users if not already present
                user_stmt = select(SyntheticUser).where(SyntheticUser.experiment_id == experiment_id)
                u_res = await session.execute(user_stmt)
                users = list(u_res.scalars().all())

                if not users:
                    users = PopulationGenerator.generate_population(
                        experiment_id=experiment.id,
                        population_size=experiment.population_size,
                        custom_distributions=experiment.population_distributions,
                        random_seed=experiment.random_seed,
                        initial_goal=experiment.task_definition.get("goal", "Complete task")
                    )
                    session.add_all(users)
                    await session.commit()

            # Concurrency limit
            concurrency = concurrency_override or experiment.concurrency or 5
            semaphore = asyncio.Semaphore(concurrency)
            llm_provider = get_llm_provider(experiment.model_configuration)

            async def run_worker(user_id: str):
                async with semaphore:
                    # Check if experiment was cancelled
                    async with async_session_maker() as check_sess:
                        exp_stat = (await check_sess.execute(select(Experiment.status).where(Experiment.id == experiment_id))).scalar()
                        if exp_stat == "CANCELLED":
                            return

                    # Load user and experiment
                    async with async_session_maker() as worker_sess:
                        u = (await worker_sess.execute(select(SyntheticUser).where(SyntheticUser.id == user_id))).scalar_one()
                        exp = (await worker_sess.execute(select(Experiment).where(Experiment.id == experiment_id))).scalar_one()
                        u.status = "RUNNING"
                        await worker_sess.commit()

                        runner = SingleUserSimulationRunner(u, exp, llm_provider)
                        trajectories = await runner.run()

                        # Save user status and trajectories
                        worker_sess.add_all(trajectories)
                        await worker_sess.commit()

            # Execute all users concurrently within semaphore
            user_ids = [u.id for u in users]
            tasks = [asyncio.create_task(run_worker(uid)) for uid in user_ids]
            await asyncio.gather(*tasks, return_exceptions=True)

            # Compute post-simulation metrics, funnel, heatmap, and friction findings
            async with async_session_maker() as session:
                exp_res = await session.execute(
                    select(Experiment)
                    .options(selectinload(Experiment.synthetic_users), selectinload(Experiment.trajectories))
                    .where(Experiment.id == experiment_id)
                )
                final_experiment = exp_res.scalar_one()

                # Calculate metrics
                final_users = final_experiment.synthetic_users
                final_trajectories = final_experiment.trajectories

                computed_metrics = MetricsCalculator.compute_metrics(
                    experiment_id=experiment_id,
                    users=final_users,
                    trajectories=final_trajectories
                )

                # Funnel and heatmap
                funnel = FunnelAndHeatmapAggregator.compute_funnel(final_users, final_trajectories)
                heatmap = FunnelAndHeatmapAggregator.compute_heatmap(final_trajectories)
                computed_metrics.funnel_steps = funnel
                computed_metrics.heatmap_data = heatmap

                session.add(computed_metrics)

                # Usability friction findings
                findings = ConfusionAndFrictionDetector.analyze_findings(
                    experiment_id=experiment_id,
                    users=final_users,
                    trajectories=final_trajectories
                )
                session.add_all(findings)

                # Mark experiment COMPLETED
                final_experiment.status = "COMPLETED"
                final_experiment.completed_at = datetime.now(timezone.utc)
                await session.commit()

            await event_bus.publish(experiment_id, {"type": "experiment_finish", "status": "COMPLETED"})
            logger.info(f"Experiment {experiment_id} successfully completed.")

        except asyncio.CancelledError:
            logger.info(f"Experiment {experiment_id} job was cancelled.")
            await event_bus.publish(experiment_id, {"type": "experiment_finish", "status": "CANCELLED"})
        except Exception as e:
            logger.error(f"Fatal error running experiment {experiment_id}: {str(e)}", exc_info=True)
            async with async_session_maker() as session:
                await session.execute(
                    update(Experiment)
                    .where(Experiment.id == experiment_id)
                    .values(status="FAILED", completed_at=datetime.now(timezone.utc))
                )
                await session.commit()
            await event_bus.publish(experiment_id, {"type": "experiment_finish", "status": "FAILED", "error": str(e)})
