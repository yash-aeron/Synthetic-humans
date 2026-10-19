from typing import List, Dict, Any
from backend.app.models.synthetic_user import SyntheticUser
from backend.app.models.trajectory import TrajectoryStep

class FunnelAndHeatmapAggregator:
    """Computes workflow funnel drops and UI element interaction heatmaps."""

    @classmethod
    def compute_funnel(cls, users: List[SyntheticUser], trajectories: List[TrajectoryStep]) -> List[Dict[str, Any]]:
        total_users = len(users)
        if total_users == 0:
            return []

        user_visited: Dict[str, set] = {u.id: set() for u in users}
        for t in trajectories:
            url_l = t.url.lower()
            if "/" in url_l:
                user_visited[t.synthetic_user_id].add("landing")
            if any(k in url_l for k in ["products", "catalog", "search"]):
                user_visited[t.synthetic_user_id].add("catalog")
            if any(k in url_l for k in ["product", "details", "item"]):
                user_visited[t.synthetic_user_id].add("details")
            if any(k in url_l for k in ["checkout", "cart"]):
                user_visited[t.synthetic_user_id].add("checkout")

        step_counts = {
            "Landing Page": sum(1 for u in users if "landing" in user_visited.get(u.id, set())),
            "Product Catalog / Search": sum(1 for u in users if "catalog" in user_visited.get(u.id, set())),
            "Product Details": sum(1 for u in users if "details" in user_visited.get(u.id, set())),
            "Checkout Flow": sum(1 for u in users if "checkout" in user_visited.get(u.id, set())),
            "Task Completed": sum(1 for u in users if u.status == "COMPLETED")
        }

        funnel = []
        prev_count = total_users
        for stage_name, count in step_counts.items():
            conversion_rate = round(count / total_users, 4) if total_users > 0 else 0.0
            drop_off = round((prev_count - count) / prev_count, 4) if prev_count > 0 else 0.0
            funnel.append({
                "stage": stage_name,
                "users_reached": count,
                "conversion_rate": conversion_rate,
                "drop_off_rate": max(0.0, drop_off)
            })
            prev_count = count

        return funnel

    @classmethod
    def compute_heatmap(cls, trajectories: List[TrajectoryStep]) -> List[Dict[str, Any]]:
        element_stats: Dict[str, Dict[str, Any]] = {}

        for t in trajectories:
            target = t.action_target
            if not target or target in ("window", "body", "security_boundary"):
                continue

            key = f"{t.url}::{target}"
            if key not in element_stats:
                element_stats[key] = {
                    "url": t.url,
                    "selector": target,
                    "action_type": t.action_type,
                    "total_interactions": 0,
                    "errors": 0,
                    "abandonments": 0
                }

            element_stats[key]["total_interactions"] += 1
            if t.action_result != "SUCCESS":
                element_stats[key]["errors"] += 1
            if t.action_type == "ABANDON":
                element_stats[key]["abandonments"] += 1

        heatmap = []
        for key, data in element_stats.items():
            friction_score = round(
                (data["errors"] * 2.0 + data["abandonments"] * 3.0) / max(1, data["total_interactions"]),
                2
            )
            heatmap.append({
                **data,
                "friction_score": friction_score
            })

        # Sort by total interactions and friction
        heatmap.sort(key=lambda x: (x["friction_score"], x["total_interactions"]), reverse=True)
        return heatmap[:50]
