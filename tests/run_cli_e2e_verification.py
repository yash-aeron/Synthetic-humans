import uvicorn
import threading
import time
import subprocess
import sys
import os

sys.path.insert(0, os.path.abspath("."))
from tests.fixtures.demo_app.server import app as demo_app

class UvicornServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=5066):
        super().__init__(daemon=True)
        self.server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="warning"))

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True

def main():
    print("[*] Starting local demo web application on port 5066...")
    server = UvicornServerThread(demo_app, host="127.0.0.1", port=5066)
    server.start()
    time.sleep(1.5)

    python_bin = sys.executable
    cmd = [
        python_bin,
        "scripts/synthetic_cli.py",
        "--url", "http://127.0.0.1:5066/",
        "--name", "E2E Production Usability Audit",
        "--population", "6",
        "--concurrency", "2",
        "--max-steps", "10",
        "--goal", "Purchase a laptop",
        "--export-report", "data/audit_report_e2e.md",
        "--export-json", "data/audit_results_e2e.json",
        "--threshold", "0.0"  # Verify regression gate passes with >= 0.0
    ]

    print(f"[*] Running CLI simulation: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("[stderr]:", result.stderr)

    server.stop()

    assert result.returncode == 0, f"CLI exited with non-zero code {result.returncode}"
    assert os.path.exists("data/audit_report_e2e.md"), "Audit report file was not generated"
    assert os.path.exists("data/audit_results_e2e.json"), "Audit JSON file was not generated"

    print("[SUCCESS] End-to-end CLI simulation and exports verified successfully!")

if __name__ == "__main__":
    main()
