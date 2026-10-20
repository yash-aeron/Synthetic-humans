import time
from typing import Dict, Any, Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

SUPPORTED_ACTIONS = [
    "CLICK",
    "TYPE",
    "SELECT",
    "SCROLL",
    "PRESS_KEY",
    "GO_BACK",
    "WAIT",
    "ABANDON"
]

class ActionExecutor:
    """Executes validated browser actions with safety checks and latency measurement."""

    @staticmethod
    async def execute_action(
        page: Page,
        action_type: str,
        target: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        params = parameters or {}
        start_time = time.perf_counter()
        result_status = "SUCCESS"
        error_msg = None

        if action_type not in SUPPORTED_ACTIONS:
            return {
                "result": "FAILED",
                "error": f"Unsupported action type: {action_type}",
                "resulting_url": page.url,
                "latency_ms": 0.0
            }

        if action_type == "ABANDON":
            return {
                "result": "SUCCESS",
                "error": None,
                "resulting_url": page.url,
                "latency_ms": 10.0
            }

        try:
            if action_type == "CLICK":
                # Wait briefly for selector and click
                locator = page.locator(target).first
                # Use click with short timeout to catch broken/hidden buttons
                await locator.click(timeout=3500)
                await page.wait_for_load_state("domcontentloaded", timeout=3000)

            elif action_type == "TYPE":
                locator = page.locator(target).first
                text_to_type = params.get("text", "")
                clear_first = params.get("clear", True)
                if clear_first:
                    await locator.fill(text_to_type, timeout=3500)
                else:
                    await locator.type(text_to_type, timeout=3500)

            elif action_type == "SELECT":
                locator = page.locator(target).first
                value = params.get("value", "")
                await locator.select_option(value, timeout=3500)

            elif action_type == "SCROLL":
                direction = params.get("direction", "down")
                delta_y = 400 if direction == "down" else -400
                await page.mouse.wheel(0, delta_y)
                await page.wait_for_timeout(300)

            elif action_type == "PRESS_KEY":
                key = params.get("key", "Enter")
                await page.keyboard.press(key)
                await page.wait_for_load_state("domcontentloaded", timeout=2000)

            elif action_type == "GO_BACK":
                await page.go_back(timeout=3500)
                await page.wait_for_load_state("domcontentloaded", timeout=2000)

            elif action_type == "WAIT":
                duration_ms = min(params.get("duration_ms", 1000), 5000)
                await page.wait_for_timeout(duration_ms)

        except PlaywrightTimeoutError:
            result_status = "FAILED"
            error_msg = f"Timeout executing {action_type} on target: {target}"
        except Exception as e:
            result_status = "FAILED"
            error_msg = f"Error executing {action_type} on target {target}: {str(e)}"

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "result": result_status,
            "error": error_msg,
            "resulting_url": page.url,
            "latency_ms": latency_ms
        }
