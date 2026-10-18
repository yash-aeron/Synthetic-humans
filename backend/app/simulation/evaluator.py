from typing import Dict, Any, List, Optional
import re

class TaskEvaluator:
    """Evaluates whether synthetic user actions have satisfied structured task conditions."""

    @staticmethod
    def evaluate_condition(condition: Dict[str, Any], observation: Dict[str, Any]) -> bool:
        cond_type = condition.get("type", "").lower()
        val = str(condition.get("value", "")).lower()

        current_url = observation.get("url", "").lower()
        page_title = observation.get("page_title", "").lower()
        visible_text = observation.get("visible_text_summary", "").lower()
        elements = observation.get("interactive_elements", [])

        if cond_type == "url_contains":
            return val in current_url

        elif cond_type == "url_matches":
            try:
                return bool(re.search(val, current_url))
            except Exception:
                return val in current_url

        elif cond_type == "text_present":
            return val in visible_text or val in page_title

        elif cond_type == "element_visible":
            # Match selector, text, or id in interactive elements
            for el in elements:
                if (
                    val in el.get("selector", "").lower()
                    or val in el.get("text", "").lower()
                    or val in el.get("id", "").lower()
                ):
                    return True
            return False

        return False

    @classmethod
    def evaluate_task_status(
        cls,
        task_definition: Dict[str, Any],
        observation: Dict[str, Any],
        steps_taken: int,
        max_steps: int,
        duration_seconds: float,
        max_duration_seconds: float,
        user_abandoned: bool = False
    ) -> str:
        """
        Determines current outcome status:
        SUCCESS, PARTIAL_SUCCESS, ABANDONMENT, TIMEOUT, FAILURE, or IN_PROGRESS
        """
        if user_abandoned:
            return "ABANDONMENT"

        if duration_seconds >= max_duration_seconds or steps_taken >= max_steps:
            return "TIMEOUT"

        success_conditions = task_definition.get("success_conditions", [])
        failure_conditions = task_definition.get("failure_conditions", [])

        # Check explicit failure conditions
        for fc in failure_conditions:
            if cls.evaluate_condition(fc, observation):
                return "FAILURE"

        # Check success conditions
        if success_conditions:
            met_count = sum(1 for sc in success_conditions if cls.evaluate_condition(sc, observation))
            if met_count == len(success_conditions):
                return "SUCCESS"
            elif met_count > 0:
                # Still in progress unless steps exceeded
                return "PARTIAL_SUCCESS"

        return "IN_PROGRESS"
