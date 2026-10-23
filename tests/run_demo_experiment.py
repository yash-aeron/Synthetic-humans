import asyncio
import threading
import time
import uvicorn
import httpx
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.database import async_session_maker, init_db
from backend.app.models.experiment import Experiment
from backend.app.simulation.population import PopulationGenerator
from backend.app.simulation.orchestrator import ExperimentOrchestrator
from backend.app.browser.playwright_runner import browser_manager
from tests.fixtures.demo_app.server import app as demo_app

class TargetAppServerThread(threading.Thread):
    def __init__(self, host="127.0.0.1", port=5050):
        super().__init__(daemon=True)
        self.server = uvicorn.Server(uvicorn.Config(demo_app, host=host, port=port, log_level="warning"))

    def run(self):
        self.server.run()

async def run_100_user_demo():
    print("=================================================================")
    print(" SYNTHETIC HUMANS: BEHAVIORAL SIMULATION & USABILITY ENGINE")
    print(" Reproducible 100-User Demonstration Experiment")
    print("=================================================================\n")

    # 1. Start Toy Target Application on port 5050 if not running
    target_url = "http://127.0.0.1:5050/"
    try:
        httpx.get(target_url, timeout=1.0)
        print("[OK] Target application already running on port 5050.")
    except Exception:
        print("Starting target application 'Synthetix Hardware' on port 5050...")
        target_server = TargetAppServerThread()
        target_server.start()
        time.sleep(1.5)
        print("[OK] Target application online at http://127.0.0.1:5050/")

    # 2. Initialize Database Schema
    print("Initializing persistence engine...")
    await init_db()
    print("[OK] PostgreSQL/SQLite persistence schema ready.\n")

    # 3. Create Demonstration Experiment
    exp_id = "exp-demo-100-laptops"
    pop_size = 100
    concurrency = 5
    seed = 42

    print(f"Creating experiment '{exp_id}':")
    print(f"  * Population Size: {pop_size} persistent synthetic agents")
    print(f"  * Concurrency: {concurrency} parallel browser workers")
    print(f"  * Random Seed: {seed} (reproducible)")
    print(f"  * Target: {target_url}")
    print(f"  * Goal: Discover laptop catalog and place simulated order\n")

    async with async_session_maker() as session:
        # Check if exists, delete previous demo run for fresh clean state
        existing = (await session.execute(select(Experiment).where(Experiment.id == exp_id))).scalar_one_or_none()
        if existing:
            await session.delete(existing)
            await session.commit()

        experiment = Experiment(
            id=exp_id,
            name="100-Agent Laptop Checkout Usability Benchmark",
            description="Synthetic user simulation detecting checkout hurdles and navigation friction.",
            target_url=target_url,
            population_size=pop_size,
            task_definition={
                "goal": "Purchase a laptop",
                "success_conditions": [
                    {"type": "url_contains", "value": "order-placed"}
                ],
                "failure_conditions": []
            },
            population_distributions={
                "technical_proficiency": {
                    "BEGINNER": 0.40,
                    "INTERMEDIATE": 0.45,
                    "EXPERT": 0.15
                }
            },
            max_steps_per_user=12,
            max_duration_seconds=90,
            concurrency=concurrency,
            random_seed=seed,
            model_configuration={"provider": "mock"},
            status="CREATED",
            is_authorized=True,
            allowed_origins=["http://127.0.0.1:5050", "http://localhost:5050"]
        )
        session.add(experiment)

        # 4. Generate Population
        print("Synthesizing 100 persistent agents with cognitive and demographic traits...")
        users = PopulationGenerator.generate_population(
            experiment_id=exp_id,
            population_size=pop_size,
            random_seed=seed,
            initial_goal="Purchase a laptop"
        )
        session.add_all(users)
        await session.commit()
        print(f"[OK] Generated {len(users)} structured personas across BEGINNER (40%), INTERMEDIATE (45%), EXPERT (15%).\n")

    # 5. Run simulation
    print("Launching browser automation loop (Observe -> Decide -> Act -> Verify)...")
    sim_start = time.perf_counter()
    await ExperimentOrchestrator._execute_experiment_job(exp_id, concurrency_override=concurrency)
    sim_duration = round(time.perf_counter() - sim_start, 2)
    print(f"[OK] Simulation completed in {sim_duration}s across {pop_size} agents.\n")

    # 6. Retrieve and display findings
    async with async_session_maker() as session:
        stmt = (
            select(Experiment)
            .options(
                selectinload(Experiment.synthetic_users),
                selectinload(Experiment.trajectories),
                selectinload(Experiment.metrics),
                selectinload(Experiment.findings)
            )
            .where(Experiment.id == exp_id)
        )
        res = await session.execute(stmt)
        exp = res.scalar_one()

        m = exp.metrics
        print("=================================================================")
        print(" SIMULATION RESULTS & USABILITY FINDINGS")
        print("=================================================================")
        print(f"Experiment Status:       {exp.status}")
        print(f"Task Completion Rate:    {round(m.task_completion_rate * 100, 1)}%")
        print(f"Task Abandonment Rate:   {round(m.task_abandonment_rate * 100, 1)}%")
        print(f"Average Duration:        {m.average_task_duration}s (Median: {m.median_task_duration}s, p95: {m.p95_task_duration}s)")
        print(f"Average Actions Taken:   {m.average_actions}")
        print(f"Average Errors:          {m.average_errors}")
        print(f"Retry Rate:              {round(m.retry_rate * 100, 1)}%")
        print(f"Confusion Rate:          {round(m.confusion_rate * 100, 1)}%")
        print(f"Total Trajectory Steps:  {len(exp.trajectories)}\n")

        print("--- Technical Proficiency Breakdown ---")
        tech_segs = (m.segment_metrics or {}).get("technical_proficiency", {})
        for prof, data in tech_segs.items():
            print(f"  * {prof:<12}: Completion {round(data.get('completion_rate', 0)*100, 1)}% | Avg Duration: {data.get('avg_duration')}s | Avg Frustration: {data.get('avg_frustration')}")

        print("\n--- Detected Usability Friction Findings ---")
        if exp.findings:
            for idx, f in enumerate(exp.findings, 1):
                print(f"\nFinding #{idx} [{f.severity}] - {f.title}")
                print(f"Category:       {f.category}")
                print(f"Description:    {f.description}")
                print(f"Recommendation: {f.recommendation}")
        else:
            print("No high-severity friction points detected.")

        print("\n=================================================================")
        print(f"Dashboard Replay URL: http://localhost:3000/experiments/{exp_id}")
        print("=================================================================\n")

    await browser_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(run_100_user_demo())
