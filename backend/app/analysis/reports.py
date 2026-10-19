from typing import Dict, Any, Optional
from backend.app.models.metrics import ExperimentMetrics
from backend.app.models.finding import ExperimentComparison

class ExperimentComparator:
    """Generates comparative differential analysis between two simulated experiments."""

    @classmethod
    def compare(
        cls,
        baseline_id: str,
        variant_id: str,
        baseline_metrics: ExperimentMetrics,
        variant_metrics: ExperimentMetrics
    ) -> ExperimentComparison:
        v_comp = variant_metrics.task_completion_rate if variant_metrics.task_completion_rate is not None else 0.0
        b_comp = baseline_metrics.task_completion_rate if baseline_metrics.task_completion_rate is not None else 0.0
        completion_delta = round(v_comp - b_comp, 4)

        v_dur = variant_metrics.average_task_duration if variant_metrics.average_task_duration is not None else 0.0
        b_dur = baseline_metrics.average_task_duration if baseline_metrics.average_task_duration is not None else 0.0
        duration_delta = round(v_dur - b_dur, 2)

        v_err = variant_metrics.average_errors if variant_metrics.average_errors is not None else 0.0
        b_err = baseline_metrics.average_errors if baseline_metrics.average_errors is not None else 0.0
        error_delta = round(v_err - b_err, 2)

        v_ab = variant_metrics.task_abandonment_rate if variant_metrics.task_abandonment_rate is not None else 0.0
        b_ab = baseline_metrics.task_abandonment_rate if baseline_metrics.task_abandonment_rate is not None else 0.0
        abandonment_delta = round(v_ab - b_ab, 4)

        # Segment-level deltas
        base_segs = baseline_metrics.segment_metrics or {}
        var_segs = variant_metrics.segment_metrics or {}

        segment_deltas: Dict[str, Any] = {}
        for seg_category in ["technical_proficiency", "device"]:
            category_delta = {}
            base_cat = base_segs.get(seg_category, {})
            var_cat = var_segs.get(seg_category, {})
            for key in base_cat.keys():
                if key in var_cat:
                    b_c = base_cat[key].get("completion_rate", 0.0) or 0.0
                    v_c = var_cat[key].get("completion_rate", 0.0) or 0.0
                    category_delta[key] = {
                        "baseline_completion": b_c,
                        "variant_completion": v_c,
                        "delta": round(v_c - b_c, 4)
                    }
            segment_deltas[seg_category] = category_delta

        # Construct scientific, evidence-based summary
        sign = "+" if completion_delta >= 0 else ""
        comp_pct = round(completion_delta * 100, 1)
        b_pct = round(b_comp * 100, 1)
        v_pct = round(v_comp * 100, 1)

        summary = (
            f"Simulation results indicate the variant application version altered task completion "
            f"from {b_pct}% to {v_pct}% ({sign}{comp_pct}% delta). "
            f"Average task completion duration shifted by {duration_delta}s, with an error delta of {error_delta}. "
            f"[Note: These findings reflect simulated synthetic agent behavior under modeled heuristics, not human-validated usability studies.]"
        )

        return ExperimentComparison(
            baseline_experiment_id=baseline_id,
            variant_experiment_id=variant_id,
            completion_rate_delta=completion_delta,
            duration_delta=duration_delta,
            error_delta=error_delta,
            abandonment_delta=abandonment_delta,
            segment_deltas=segment_deltas,
            summary=summary
        )
