import numpy as np
from typing import List, Dict, Any
from backend.app.models.synthetic_user import SyntheticUser
from backend.app.models.trajectory import TrajectoryStep
from backend.app.models.metrics import ExperimentMetrics

class MetricsCalculator:
    """Calculates quantitative population metrics and segment-level breakdowns."""

    @classmethod
    def compute_metrics(
        cls,
        experiment_id: str,
        users: List[SyntheticUser],
        trajectories: List[TrajectoryStep]
    ) -> ExperimentMetrics:
        total_users = len(users)
        if total_users == 0:
            return ExperimentMetrics(experiment_id=experiment_id)

        completed_count = sum(1 for u in users if u.status == "COMPLETED")
        abandoned_count = sum(1 for u in users if u.status == "ABANDONED")
        durations = [u.duration_seconds for u in users if u.duration_seconds > 0]
        step_counts = [u.steps_taken for u in users]
        error_counts = [u.error_count for u in users]

        completion_rate = round(completed_count / total_users, 4)
        abandonment_rate = round(abandoned_count / total_users, 4)

        avg_duration = round(float(np.mean(durations)), 2) if durations else 0.0
        med_duration = round(float(np.median(durations)), 2) if durations else 0.0
        p95_duration = round(float(np.percentile(durations, 95)), 2) if durations else 0.0

        avg_actions = round(float(np.mean(step_counts)), 2) if step_counts else 0.0
        avg_errors = round(float(np.mean(error_counts)), 2) if error_counts else 0.0

        # Trajectory-level metrics
        total_steps = len(trajectories)
        back_navs = sum(1 for t in trajectories if t.action_type == "GO_BACK")
        back_nav_rate = round(back_navs / total_steps, 4) if total_steps > 0 else 0.0

        # Retry rate: consecutive actions on the same target
        retries = 0
        user_trajectories: Dict[str, List[TrajectoryStep]] = {}
        for t in trajectories:
            user_trajectories.setdefault(t.synthetic_user_id, []).append(t)

        for u_id, t_steps in user_trajectories.items():
            t_steps_sorted = sorted(t_steps, key=lambda x: x.step_number)
            for i in range(1, len(t_steps_sorted)):
                if t_steps_sorted[i].action_target == t_steps_sorted[i - 1].action_target and t_steps_sorted[i - 1].action_result != "SUCCESS":
                    retries += 1
        retry_rate = round(retries / total_steps, 4) if total_steps > 0 else 0.0

        # Confusion rate: proportion of users experiencing loops, retries, or high frustration (>0.6)
        confused_users = sum(1 for u in users if (u.frustration_level or 0.0) >= 0.5 or (u.error_count or 0) >= 2)
        confusion_rate = round(confused_users / total_users, 4)

        # Dead-end rate: abandoned or timed out users with no progress
        dead_ends = sum(1 for u in users if u.status in ("ABANDONED", "TIMEOUT", "FAILED"))
        dead_end_rate = round(dead_ends / total_users, 4)

        # Time to first successful action
        first_success_latencies = []
        for u_id, t_steps in user_trajectories.items():
            success_steps = [s for s in t_steps if s.action_result == "SUCCESS"]
            if success_steps:
                first_success_latencies.append(success_steps[0].latency_ms / 1000.0)
        ttfa = round(float(np.mean(first_success_latencies)), 2) if first_success_latencies else 0.0

        # Segment breakdowns
        segment_metrics = cls._compute_segments(users)

        # Action distribution
        action_dist: Dict[str, int] = {}
        for t in trajectories:
            action_dist[t.action_type] = action_dist.get(t.action_type, 0) + 1

        return ExperimentMetrics(
            experiment_id=experiment_id,
            task_completion_rate=completion_rate,
            task_abandonment_rate=abandonment_rate,
            average_task_duration=avg_duration,
            median_task_duration=med_duration,
            p95_task_duration=p95_duration,
            average_actions=avg_actions,
            average_errors=avg_errors,
            retry_rate=retry_rate,
            back_navigation_rate=back_nav_rate,
            dead_end_rate=dead_end_rate,
            confusion_rate=confusion_rate,
            time_to_first_successful_action=ttfa,
            segment_metrics=segment_metrics,
            action_distribution=action_dist,
            funnel_steps=[],
            heatmap_data=[],
            total_llm_calls=total_steps,
            estimated_tokens_used=total_steps * 120
        )

    @classmethod
    def _compute_segments(cls, users: List[SyntheticUser]) -> Dict[str, Any]:
        segments: Dict[str, Dict[str, Any]] = {
            "technical_proficiency": {},
            "device": {},
            "network": {},
            "patience": {}
        }

        # Proficiency
        for prof in ["BEGINNER", "INTERMEDIATE", "EXPERT"]:
            sub = [u for u in users if u.technical_proficiency == prof]
            if sub:
                comp = sum(1 for u in sub if u.status == "COMPLETED")
                dur = [u.duration_seconds for u in sub]
                segments["technical_proficiency"][prof] = {
                    "total": len(sub),
                    "completed": comp,
                    "completion_rate": round(comp / len(sub), 4),
                    "avg_duration": round(float(np.mean(dur)), 2) if dur else 0.0,
                    "avg_frustration": round(float(np.mean([u.frustration_level for u in sub])), 2)
                }

        # Device
        for dev in ["DESKTOP", "LAPTOP", "TABLET"]:
            sub = [u for u in users if (u.device_profile or {}).get("device_type") == dev]
            if sub:
                comp = sum(1 for u in sub if u.status == "COMPLETED")
                segments["device"][dev] = {
                    "total": len(sub),
                    "completed": comp,
                    "completion_rate": round(comp / len(sub), 4)
                }

        # Network
        for net in ["FAST_BROADBAND", "REGULAR_4G", "SLOW_3G"]:
            sub = [u for u in users if (u.network_profile or {}).get("network_type") == net]
            if sub:
                comp = sum(1 for u in sub if u.status == "COMPLETED")
                segments["network"][net] = {
                    "total": len(sub),
                    "completed": comp,
                    "completion_rate": round(comp / len(sub), 4)
                }

        return segments
