import pytest
import asyncio
import uvicorn
import threading
import time
from backend.app.database import async_session_maker, init_db
from backend.app.models.experiment import Experiment
from backend.app.simulation.population import PopulationGenerator
from backend.app.simulation.orchestrator import ExperimentOrchestrator
from backend.app.browser.playwright_runner import browser_manager
from tests.fixtures.demo_app.server import app as demo_app

class UvicornServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=5055):
        super().__init__(daemon=True)
        self.server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="warning"))

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True

@pytest.fixture(scope="module")
def demo_server():
    server = UvicornServerThread(demo_app, host="127.0.0.1", port=5055)
    server.start()
    time.sleep(1.0)
    yield "http://127.0.0.1:5055"
    server.stop()

@pytest.mark.asyncio
async def test_full_playwright_simulation_e2e(demo_server):
    """
    End-to-end integration test:
    Executes synthetic users against the toy target application using real Playwright automation.
    Verifies trajectory recording, failure handling, and usability findings synthesis.
    """
    await init_db()

    target_url = f"{demo_server}/"
    allowed_origin = demo_server

    import uuid
    exp_id = f"test-e2e-{uuid.uuid4()}"
    async with async_session_maker() as session:
        exp = Experiment(
            id=exp_id,
            name="Playwright E2E Usability Verification",
            target_url=target_url,
            population_size=3,
            task_definition={
                "goal": "Purchase a laptop",
                "success_conditions": [
                    {"type": "url_contains", "value": "order-placed"}
                ],
                "failure_conditions": []
            },
            max_steps_per_user=10,
            max_duration_seconds=45,
            concurrency=2,
            random_seed=42,
            is_authorized=True,
            allowed_origins=[allowed_origin]
        )
        session.add(exp)

        # Generate 3 users with varied proficiency
        users = PopulationGenerator.generate_population(
            experiment_id=exp_id,
            population_size=3,
            random_seed=42,
            initial_goal="Purchase a laptop"
        )
        session.add_all(users)
        await session.commit()

    # Run the experiment through orchestrator
    await ExperimentOrchestrator._execute_experiment_job(exp_id, concurrency_override=2)

    # Verify results in database
    async with async_session_maker() as session:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        res = await session.execute(
            select(Experiment)
            .options(
                selectinload(Experiment.synthetic_users),
                selectinload(Experiment.trajectories),
                selectinload(Experiment.metrics),
                selectinload(Experiment.findings)
            )
            .where(Experiment.id == exp_id)
        )
        saved_exp = res.scalar_one()

        assert saved_exp.status in ("COMPLETED", "RUNNING")
        assert len(saved_exp.synthetic_users) == 3
        assert len(saved_exp.trajectories) > 0

        # Check trajectory details
        first_step = saved_exp.trajectories[0]
        assert first_step.action_type in ["CLICK", "TYPE", "SCROLL", "WAIT"]
        assert first_step.action_confidence >= 0.0
        assert first_step.resulting_url is not None

        # Check metrics computation
        assert saved_exp.metrics is not None
        assert saved_exp.metrics.average_actions > 0.0

    await browser_manager.shutdown()
