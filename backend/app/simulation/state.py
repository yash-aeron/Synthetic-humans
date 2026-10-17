from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class PersistentUserState:
    def __init__(
        self,
        user_id: str,
        technical_proficiency: str = "INTERMEDIATE",
        patience: float = 0.5,
        risk_tolerance: float = 0.5,
        reading_behavior: str = "SCANNER",
        initial_goal: str = "",
        knowledge_state: Optional[Dict[str, Any]] = None,
        memory_state: Optional[Dict[str, Any]] = None,
        frustration_level: float = 0.0,
        confidence_level: float = 1.0
    ):
        self.user_id = user_id
        self.technical_proficiency = technical_proficiency
        self.patience = max(0.0, min(1.0, patience))
        self.risk_tolerance = max(0.0, min(1.0, risk_tolerance))
        self.reading_behavior = reading_behavior
        self.current_goal = initial_goal
        self.current_subgoal = "explore_landing"
        self.frustration_level = max(0.0, min(1.0, frustration_level))
        self.confidence_level = max(0.0, min(1.0, confidence_level))

        self.knowledge_state: Dict[str, Any] = knowledge_state or {
            "visited_urls": [],
            "discovered_elements": [],
            "identified_forms": [],
            "known_products": []
        }

        self.memory_state: Dict[str, Any] = memory_state or {
            "recent_actions": [],
            "recent_failures": [],
            "consecutive_failures": 0,
            "url_visit_counts": {},
            "loop_detected": False
        }

        self.action_history: List[Dict[str, Any]] = []
        self.status: str = "PENDING"

    @property
    def abandonment_threshold(self) -> float:
        # Lower patience means lower threshold to abandon
        # Experts have slightly lower patience for buggy apps
        base = 0.70
        if self.technical_proficiency == "EXPERT":
            base = 0.65
        elif self.technical_proficiency == "BEGINNER":
            base = 0.80 # Beginners tolerate more confusion before giving up
        return base * (0.6 + 0.4 * self.patience)

    def record_page_visit(self, url: str, page_title: str):
        visited = self.knowledge_state.setdefault("visited_urls", [])
        if not visited or visited[-1] != url:
            visited.append(url)

        visit_counts = self.memory_state.setdefault("url_visit_counts", {})
        visit_counts[url] = visit_counts.get(url, 0) + 1

        # Check for navigation loop (visited same URL 3+ times within last 6 actions)
        recent = [a.get("resulting_url") or a.get("url") for a in self.memory_state.get("recent_actions", [])[-6:]]
        if recent.count(url) >= 3:
            self.memory_state["loop_detected"] = True
            # Frustration spike on loop
            self.frustration_level = min(1.0, self.frustration_level + 0.15)
            self.confidence_level = max(0.0, self.confidence_level - 0.10)

    def register_action_result(
        self,
        action_type: str,
        target: str,
        result: str, # SUCCESS, FAILED, NOOP, ERROR
        resulting_url: str,
        error_message: Optional[str] = None
    ):
        consecutive_failures = self.memory_state.get("consecutive_failures", 0)

        # Update action history in working memory
        action_summary = {
            "action_type": action_type,
            "target": target,
            "result": result,
            "resulting_url": resulting_url,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        recent_actions = self.memory_state.setdefault("recent_actions", [])
        recent_actions.append(action_summary)
        if len(recent_actions) > 10:
            recent_actions.pop(0)

        if result in ("FAILED", "ERROR"):
            consecutive_failures += 1
            self.memory_state["consecutive_failures"] = consecutive_failures
            self.memory_state.setdefault("recent_failures", []).append({
                "action": action_type,
                "target": target,
                "error": error_message
            })

            # Frustration increases
            frustration_step = 0.12 * (1.5 - self.patience)
            self.frustration_level = min(1.0, self.frustration_level + frustration_step)
            self.confidence_level = max(0.0, self.confidence_level - 0.15)

        elif result == "NOOP":
            consecutive_failures += 1
            self.memory_state["consecutive_failures"] = consecutive_failures
            self.frustration_level = min(1.0, self.frustration_level + 0.08)
            self.confidence_level = max(0.0, self.confidence_level - 0.05)

        else: # SUCCESS
            # Action made progress
            self.memory_state["consecutive_failures"] = 0
            # Slight frustration reduction
            self.frustration_level = max(0.0, self.frustration_level - 0.05)
            self.confidence_level = min(1.0, self.confidence_level + 0.05)

    def should_abandon(self) -> bool:
        if self.frustration_level >= self.abandonment_threshold:
            return True
        if self.memory_state.get("consecutive_failures", 0) >= 5:
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frustration_level": round(self.frustration_level, 3),
            "confidence_level": round(self.confidence_level, 3),
            "current_goal": self.current_goal,
            "current_subgoal": self.current_subgoal,
            "knowledge_state": self.knowledge_state,
            "memory_state": self.memory_state,
            "status": self.status
        }
