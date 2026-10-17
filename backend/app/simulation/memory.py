from typing import Dict, Any, List, Set, Optional

class UserCognitiveMemory:
    """Manages working memory, short-term history, and failure recall for a synthetic agent."""

    def __init__(self, working_memory_capacity: int = 7):
        self.capacity = working_memory_capacity
        self.failed_action_targets: Set[str] = set()
        self.attempted_clicks: List[str] = []
        self.recognized_errors: List[str] = []

    def record_attempt(self, target: str, action_type: str = "CLICK"):
        self.attempted_clicks.append(target)
        if len(self.attempted_clicks) > self.capacity:
            self.attempted_clicks.pop(0)

    def record_failure(self, target: str, reason: str):
        self.failed_action_targets.add(target)
        self.recognized_errors.append(reason)
        if len(self.recognized_errors) > 10:
            self.recognized_errors.pop(0)

    def is_recently_failed_target(self, target: str) -> bool:
        return target in self.failed_action_targets

    def count_repeated_clicks(self, target: str) -> int:
        return self.attempted_clicks.count(target)

    def reset_page_failures(self):
        """Allows retry when user transitions to a different page."""
        self.failed_action_targets.clear()
