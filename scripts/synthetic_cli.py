#!/usr/bin/env python3
"""
Synthetic Humans - Automated CLI Usability & Behavioral Regression Engine

Enables running headless synthetic user experiments from the command line,
evaluating usability thresholds in CI/CD pipelines, and exporting audit reports.

Example:
    python scripts/synthetic_cli.py --url http://127.0.0.1:5055/ --population 10 --goal "Purchase a laptop" --threshold 0.70 --export-report report.md
"""

import argparse
import asyncio
import sys
import os
import json
import uuid
import time
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import init_db, async_session_maker
from backend.app.models.experiment import Experiment
from backend.app.models.synthetic_user import SyntheticUser
from backend.app.simulation.population import PopulationGenerator
from backend.app.simulation.orchestrator import ExperimentOrchestrator
from backend.app.browser.playwright_runner import browser_manager
from sqlalchemy import select
from sqlalchemy.orm import selectinload

def print_banner():
    banner = """
================================================================================
                    SYNTHETIC HUMANS - CLI RUNNER
       Behavioral User-Simulation & HCI Usability Testing Engine
================================================================================
"""
    print(banner)

async def run_cli_simulation(args):
    print_banner()
    print(f"[*] Initializing database and simulation engine...")
    await init_db()

    target_url = args.url
    allowed_origin = browser_manager.get_origin(target_url)
    exp_id = f"cli-{uuid.uuid4().hex[:12]}"

    task_definition = {
        "goal": args.goal,
        "success_conditions": [
            {"type": "url_contains", "value": args.success_keyword or "order-placed"},
            {"type": "text_present", "value": args.success_keyword or "confirmed"}
        ],
        "failure_conditions": [
            {"type": "url_contains", "value": "system-error"}
        ]
    }

    print(f"[*] Creating Experiment: '{args.name}'")
    print(f"    - Target URL:       {target_url}")
    print(f"    - Allowed Origin:   {allowed_origin}")
    print(f"    - Population Size:  {args.population} agents")
    print(f"    - Concurrency:      {args.concurrency}")
    print(f"    - Max Steps/Agent:  {args.max_steps}")
    print(f"    - Random Seed:      {args.seed}")
    print(f"    - Task Goal:        \"{args.goal}\"")

    async with async_session_maker() as session:
        exp = Experiment(
            id=exp_id,
            name=args.name,
            target_url=target_url,
            population_size=args.population,
            task_definition=task_definition,
            max_steps_per_user=args.max_steps,
            max_duration_seconds=args.max_duration,
            concurrency=args.concurrency,
            random_seed=args.seed,
            model_configuration={"provider": args.provider},
            is_authorized=True,
            allowed_origins=[allowed_origin]
        )
        session.add(exp)

        # Generate population
        users = PopulationGenerator.generate_population(
            experiment_id=exp_id,
            population_size=args.population,
            random_seed=args.seed,
            initial_goal=args.goal
        )
        session.add_all(users)
        await session.commit()

    print(f"[*] Population synthesized: {len(users)} persistent agents.")
    print(f"[*] Launching Playwright browser worker pool...")

    start_time = time.perf_counter()
    await ExperimentOrchestrator._execute_experiment_job(exp_id, concurrency_override=args.concurrency)
    elapsed = round(time.perf_counter() - start_time, 2)

    # Fetch results
    async with async_session_maker() as session:
        stmt = (
            select(Experiment)
            .options(
                selectinload(Experiment.synthetic_users).selectinload(SyntheticUser.trajectories),
                selectinload(Experiment.metrics),
                selectinload(Experiment.findings)
            )
            .where(Experiment.id == exp_id)
        )
        res = await session.execute(stmt)
        final_exp = res.scalar_one()

    m = final_exp.metrics
    users = final_exp.synthetic_users
    completed = sum(1 for u in users if u.status == "COMPLETED")
    abandoned = sum(1 for u in users if u.status == "ABANDONED")
    failed = sum(1 for u in users if u.status in ("FAILED", "TIMEOUT"))
    comp_rate = (completed / len(users)) if users else 0.0

    print("\n" + "=" * 80)
    print("                      SIMULATION EXECUTION RESULTS")
    print("=" * 80)
    print(f"Status:            {final_exp.status} (Finished in {elapsed}s)")
    print(f"Total Agents:      {len(users)}")
    print(f"Completed Tasks:   {completed} ({round(comp_rate * 100)}%)")
    print(f"Abandoned Tasks:   {abandoned} ({round((abandoned / len(users))*100)}%)")
    print(f"Failed / Timeout:  {failed} ({round((failed / len(users))*100)}%)")
    print(f"Avg Actions/User:  {m.average_actions if m else 0.0}")
    print(f"Avg Duration:      {m.average_task_duration if m else 0.0}s")
    print(f"Confusion Rate:    {round((m.confusion_rate * 100) if m else 0.0)}%")
    print(f"Retry Rate:        {round((m.retry_rate * 100) if m else 0.0)}%")

    print("\n" + "-" * 80)
    print("               DISCOVERED USABILITY FRICTION ANOMALIES")
    print("-" * 80)
    if not final_exp.findings:
        print("  [OK] No major friction bottlenecks detected.")
    else:
        for idx, f in enumerate(final_exp.findings, 1):
            print(f"  {idx}. [{f.severity}] {f.title}")
            print(f"     Category:       {f.category}")
            print(f"     Description:    {f.description}")
            print(f"     Recommendation: {f.recommendation}\n")

    # Export Report if requested
    if args.export_report:
        report_lines = [
            f"# Usability Audit Report - {final_exp.name}",
            f"- **Target URL:** {final_exp.target_url}",
            f"- **Population:** {len(users)} agents",
            f"- **Completion Rate:** {round(comp_rate * 100)}%",
            f"- **Abandonment Rate:** {round((abandoned / len(users))*100)}%",
            f"- **Avg Duration:** {m.average_task_duration if m else 0}s\n",
            "## Usability Friction Findings\n"
        ]
        for f in final_exp.findings:
            report_lines.append(f"### [{f.severity}] {f.title}\n{f.description}\n\n**Recommendation:** {f.recommendation}\n")
        with open(args.export_report, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        print(f"[*] Exported Markdown audit report to: {args.export_report}")

    # Export JSON if requested
    if args.export_json:
        export_dict = {
            "experiment_id": exp_id,
            "completion_rate": comp_rate,
            "metrics": {
                "average_duration": m.average_task_duration if m else 0,
                "confusion_rate": m.confusion_rate if m else 0
            },
            "findings": [{"severity": f.severity, "title": f.title} for f in final_exp.findings]
        }
        with open(args.export_json, "w", encoding="utf-8") as f:
            json.dump(export_dict, f, indent=2)
        print(f"[*] Exported JSON results to: {args.export_json}")

    await browser_manager.shutdown()

    # CI/CD Regression Gate Evaluation
    if args.threshold is not None:
        print("\n" + "=" * 80)
        print(f"CI/CD USABILITY REGRESSION GATE (Required Completion: {round(args.threshold * 100)}%)")
        print("=" * 80)
        if comp_rate >= args.threshold:
            print(f"  [PASS] Actual completion rate ({round(comp_rate * 100)}%) >= Threshold ({round(args.threshold * 100)}%)")
            return 0
        else:
            print(f"  [FAIL] Actual completion rate ({round(comp_rate * 100)}%) < Threshold ({round(args.threshold * 100)}%)")
            return 1

    return 0

def main():
    parser = argparse.ArgumentParser(description="Synthetic Humans CLI Usability Runner")
    parser.add_argument("--url", required=True, help="Target application URL")
    parser.add_argument("--name", default="CLI Usability Audit", help="Experiment name")
    parser.add_argument("--population", type=int, default=5, help="Number of simulated users")
    parser.add_argument("--goal", default="Purchase a laptop", help="High-level task goal")
    parser.add_argument("--success-keyword", default=None, help="Success keyword in URL or page text")
    parser.add_argument("--concurrency", type=int, default=3, help="Concurrent Playwright browser workers")
    parser.add_argument("--max-steps", type=int, default=15, help="Max steps per synthetic user")
    parser.add_argument("--max-duration", type=int, default=60, help="Max duration in seconds per user")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--provider", default="mock", help="Cognitive LLM provider: mock, openai, gemini")
    parser.add_argument("--threshold", type=float, default=None, help="Usability regression completion rate threshold (0.0 to 1.0)")
    parser.add_argument("--export-report", default=None, help="File path to save Markdown audit report")
    parser.add_argument("--export-json", default=None, help="File path to save JSON results")

    args = parser.parse_args()
    code = asyncio.run(run_cli_simulation(args))
    sys.exit(code)

if __name__ == "__main__":
    main()
