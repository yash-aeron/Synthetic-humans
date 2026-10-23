import asyncio
import os
import sys
import httpx
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\aeron\.gemini\antigravity\brain\164172f1-507c-4a85-98e2-26aa4ae324d6"

async def main():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    print("[*] Checking backend experiments...")

    async with httpx.AsyncClient() as client:
        # Create a fresh live experiment to demonstrate full flow
        create_payload = {
            "name": "Synthetix Hardware - Behavioral Usability Audit",
            "target_url": "http://127.0.0.1:5050/",
            "description": "Autonomous population simulation auditing laptop purchasing workflow, checkout validation, and category navigation loops.",
            "population_size": 10,
            "task_definition": {
                "goal": "Purchase a laptop",
                "success_conditions": [
                    {"type": "url_contains", "value": "order-placed"},
                    {"type": "text_present", "value": "Order Confirmed"}
                ],
                "failure_conditions": [
                    {"type": "url_contains", "value": "system-error"}
                ]
            },
            "population_distributions": {
                "technical_proficiency": {
                    "BEGINNER": 0.40,
                    "INTERMEDIATE": 0.40,
                    "EXPERT": 0.20
                }
            },
            "max_steps_per_user": 12,
            "max_duration_seconds": 60,
            "concurrency": 3,
            "random_seed": 42,
            "is_authorized": True,
            "allowed_origins": ["http://127.0.0.1:5050"]
        }

        resp = await client.post("http://127.0.0.1:8000/api/experiments", json=create_payload)
        exp_data = resp.json()
        exp_id = exp_data["id"]
        print(f"[*] Created experiment: {exp_id}")

        # Start the experiment run
        run_resp = await client.post(f"http://127.0.0.1:8000/api/experiments/{exp_id}/run")
        print(f"[*] Started simulation: {run_resp.json()}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # 1. Capture Dashboard Experiments List
        print("[*] Navigating to Dashboard: http://127.0.0.1:3000/experiments")
        await page.goto("http://127.0.0.1:3000/experiments", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        dash_shot = os.path.join(ARTIFACT_DIR, "live_dashboard.png")
        await page.screenshot(path=dash_shot, full_page=True)
        print(f"[OK] Saved {dash_shot}")

        # 2. Capture Experiment Detail Live HUD while running
        print(f"[*] Navigating to Experiment Detail: http://127.0.0.1:3000/experiments/{exp_id}")
        await page.goto(f"http://127.0.0.1:3000/experiments/{exp_id}", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        detail_live_shot = os.path.join(ARTIFACT_DIR, "live_experiment_detail.png")
        await page.screenshot(path=detail_live_shot, full_page=True)
        print(f"[OK] Saved {detail_live_shot}")

        # Wait for simulation to finish
        print("[*] Waiting for agents to complete trajectories...")
        for _ in range(30):
            async with httpx.AsyncClient() as client:
                poll_resp = await client.get(f"http://127.0.0.1:8000/api/experiments/{exp_id}")
                st = poll_resp.json()["experiment"]["status"]
                print(f"    - Current status: {st}")
                if st in ("COMPLETED", "FAILED"):
                    break
            await asyncio.sleep(2)

        # 3. Capture Completed Metrics, Funnel & Friction Findings
        await page.reload(wait_until="networkidle")
        await page.wait_for_timeout(1000)
        detail_completed_shot = os.path.join(ARTIFACT_DIR, "completed_experiment_metrics.png")
        await page.screenshot(path=detail_completed_shot, full_page=True)
        print(f"[OK] Saved {detail_completed_shot}")

        # 4. Capture Population Explorer
        print(f"[*] Navigating to Population Explorer: http://127.0.0.1:3000/experiments/{exp_id}/users")
        await page.goto(f"http://127.0.0.1:3000/experiments/{exp_id}/users", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        pop_shot = os.path.join(ARTIFACT_DIR, "population_explorer.png")
        await page.screenshot(path=pop_shot, full_page=True)
        print(f"[OK] Saved {pop_shot}")

        # 5. Capture Interactive Trajectory Replay Player
        async with httpx.AsyncClient() as client:
            users_resp = await client.get(f"http://127.0.0.1:8000/api/experiments/{exp_id}/users")
            user_list = users_resp.json()
            # Pick a user with trajectories
            chosen_user = user_list[0]["id"] if user_list else "unknown"

        print(f"[*] Navigating to Trajectory Player: http://127.0.0.1:3000/experiments/{exp_id}/users/{chosen_user}")
        await page.goto(f"http://127.0.0.1:3000/experiments/{exp_id}/users/{chosen_user}", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        replay_shot = os.path.join(ARTIFACT_DIR, "interactive_trajectory_player.png")
        await page.screenshot(path=replay_shot, full_page=True)
        print(f"[OK] Saved {replay_shot}")

        await browser.close()

    print("[SUCCESS] All live demonstration screenshots captured and saved to artifact directory!")

if __name__ == "__main__":
    asyncio.run(main())
