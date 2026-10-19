from typing import List, Dict, Any
from backend.app.models.synthetic_user import SyntheticUser
from backend.app.models.trajectory import TrajectoryStep
from backend.app.models.finding import FrictionFinding

class ConfusionAndFrictionDetector:
    """Detects behavioral usability anomalies and synthesizes evidence-based UX findings."""

    @classmethod
    def analyze_findings(
        cls,
        experiment_id: str,
        users: List[SyntheticUser],
        trajectories: List[TrajectoryStep]
    ) -> List[FrictionFinding]:
        findings: List[FrictionFinding] = []
        total_users = len(users)
        if total_users == 0:
            return findings

        # Group trajectories by user
        user_trajectories: Dict[str, List[TrajectoryStep]] = {}
        for t in trajectories:
            user_trajectories.setdefault(t.synthetic_user_id, []).append(t)

        user_map = {u.id: u for u in users}

        # 1. Check for Confusing Form Validation Hurdles
        form_error_steps = [
            t for t in trajectories
            if t.action_result != "SUCCESS"
            and any(k in t.action_target.lower() for k in ("zip", "postal", "input", "submit", "checkout"))
        ]
        affected_users = {t.synthetic_user_id for t in form_error_steps}
        if affected_users and (len(affected_users) / total_users) >= 0.15:
            pct = round((len(affected_users) / total_users) * 100, 1)
            findings.append(FrictionFinding(
                experiment_id=experiment_id,
                severity="HIGH",
                category="CONFUSING_FORM",
                title="Strict or Uncommunicated Form Validation Failure",
                description=f"Simulation indicates a potential usability issue: {pct}% of simulated users encountered repeated validation errors during form completion.",
                evidence={
                    "affected_users_count": len(affected_users),
                    "affected_percentage": pct,
                    "target_elements": list({t.action_target for t in form_error_steps})[:5],
                    "sample_error": form_error_steps[0].error_message if form_error_steps else None
                },
                recommendation="Provide inline helper hints, permissive formatting masks, and distinct visual feedback for required fields before form submission."
            ))

        # 2. Check for Hidden or Unclear CTA (e.g., checkout/buy button below fold or counter-intuitive label)
        abandoned_on_checkout = []
        for u_id, t_steps in user_trajectories.items():
            if t_steps and t_steps[-1].action_type == "ABANDON":
                last_url = t_steps[-1].url.lower()
                if "cart" in last_url or "product" in last_url or "checkout" in last_url:
                    abandoned_on_checkout.append(u_id)

        if abandoned_on_checkout and (len(abandoned_on_checkout) / total_users) >= 0.15:
            pct = round((len(abandoned_on_checkout) / total_users) * 100, 1)
            # Segment breakdown of this friction
            beginner_abandon = sum(1 for uid in abandoned_on_checkout if user_map.get(uid) and user_map[uid].technical_proficiency == "BEGINNER")
            beginner_total = sum(1 for u in users if u.technical_proficiency == "BEGINNER")
            beginner_pct = round((beginner_abandon / max(1, beginner_total)) * 100, 1)

            findings.append(FrictionFinding(
                experiment_id=experiment_id,
                severity="HIGH",
                category="UNNOTICED_ACTION",
                title="Primary Action Discovery Failure in Purchase Workflow",
                description=f"Simulation indicates a potential usability issue: {pct}% of users abandoned on product or review pages without completing the conversion action. Among beginner users, {beginner_pct}% failed to locate or trigger the confirmation button.",
                evidence={
                    "total_abandoned_here": len(abandoned_on_checkout),
                    "abandonment_percentage": pct,
                    "beginner_abandonment_percentage": beginner_pct,
                    "last_screen_urls": list({t_steps[-1].url for uid, t_steps in user_trajectories.items() if uid in abandoned_on_checkout})[:3]
                },
                recommendation="Ensure the primary call-to-action button is visible above the viewport fold, uses industry-standard copy (e.g. 'Checkout' / 'Place Order'), and maintains strong visual prominence."
            ))

        # 3. Check for Navigation Loops & Back-and-Forth Pacing
        looping_users = []
        for u_id, t_steps in user_trajectories.items():
            urls = [t.url for t in t_steps]
            if len(urls) >= 4:
                # Check A -> B -> A pattern
                for i in range(len(urls) - 2):
                    if urls[i] == urls[i + 2] and urls[i] != urls[i + 1]:
                        looping_users.append(u_id)
                        break

        if looping_users and (len(looping_users) / total_users) >= 0.10:
            pct = round((len(looping_users) / total_users) * 100, 1)
            findings.append(FrictionFinding(
                experiment_id=experiment_id,
                severity="MEDIUM",
                category="NAVIGATION_LOOP",
                title="Repetitive Back-Navigation and Workflow Indecision",
                description=f"Simulation indicates a potential usability issue: {pct}% of users cycled between category listings and previous pages repeatedly before making forward progress.",
                evidence={
                    "looping_users_count": len(looping_users),
                    "looping_percentage": pct
                },
                recommendation="Improve category hierarchy and breadcrumb navigation to prevent disoriented users from reverting to previous screens."
            ))

        # 4. Check for Misclicks / Unresponsive Click Affordances
        target_counts: Dict[str, Dict[str, int]] = {}
        for t in trajectories:
            if t.action_type == "CLICK":
                entry = target_counts.setdefault(t.action_target, {"total": 0, "failed": 0})
                entry["total"] += 1
                if t.action_result != "SUCCESS":
                    entry["failed"] += 1

        high_fail_targets = [tgt for tgt, cnt in target_counts.items() if cnt["total"] >= 3 and (cnt["failed"] / cnt["total"]) >= 0.5]
        if high_fail_targets:
            findings.append(FrictionFinding(
                experiment_id=experiment_id,
                severity="MEDIUM",
                category="MISCLICK",
                title="Unresponsive or Confusing Interactive Target",
                description="Simulation indicates a potential usability issue: Simulated users repeatedly clicked targets that failed to produce an active state transition or response.",
                evidence={
                    "problematic_selectors": high_fail_targets[:5]
                },
                recommendation="Inspect target elements for pointer-event blocking, ambiguous styling resembling buttons, or slow asynchronous event listeners."
            ))

        return findings
