import pytest
from datetime import datetime, timezone
from backend.app.models.synthetic_user import SyntheticUser
from backend.app.models.trajectory import TrajectoryStep
from backend.app.analysis.metrics import MetricsCalculator
from backend.app.analysis.aggregation import FunnelAndHeatmapAggregator
from backend.app.analysis.anomaly import ConfusionAndFrictionDetector
from backend.app.analysis.reports import ExperimentComparator

def test_metrics_calculation_and_segments():
    exp_id = "test-exp"
    users = [
        SyntheticUser(
            id=f"u-{i}",
            experiment_id=exp_id,
            technical_proficiency="EXPERT" if i < 3 else "BEGINNER",
            patience=0.8 if i < 3 else 0.3,
            status="COMPLETED" if i < 4 else "ABANDONED",
            duration_seconds=30.0 + i * 5,
            steps_taken=5 + i,
            error_count=0 if i < 3 else 2,
            frustration_level=0.1 if i < 3 else 0.7,
            device_profile={"device_type": "DESKTOP"},
            network_profile={"network_type": "FAST_BROADBAND"}
        )
        for i in range(10)
    ]

    trajectories = []
    for u in users:
        for s in range(u.steps_taken):
            trajectories.append(TrajectoryStep(
                id=f"t-{u.id}-{s}",
                synthetic_user_id=u.id,
                experiment_id=exp_id,
                step_number=s + 1,
                url="http://localhost:5050/",
                page_title="Home",
                action_type="GO_BACK" if s == 2 and u.technical_proficiency == "BEGINNER" else "CLICK",
                action_target="#checkout-btn",
                action_result="SUCCESS" if u.status == "COMPLETED" or s < 3 else "FAILED",
                frustration_after=u.frustration_level,
                confidence_after=0.8,
                latency_ms=100.0
            ))

    metrics = MetricsCalculator.compute_metrics(exp_id, users, trajectories)

    assert metrics.task_completion_rate == 0.40 # 4 completed out of 10
    assert metrics.task_abandonment_rate == 0.60
    assert metrics.average_task_duration > 0.0
    assert "technical_proficiency" in metrics.segment_metrics
    assert "EXPERT" in metrics.segment_metrics["technical_proficiency"]
    assert "BEGINNER" in metrics.segment_metrics["technical_proficiency"]

    # Expert completion should be higher than beginner
    expert_stat = metrics.segment_metrics["technical_proficiency"]["EXPERT"]
    beginner_stat = metrics.segment_metrics["technical_proficiency"]["BEGINNER"]
    assert expert_stat["completion_rate"] == 1.0 # 3 of 3
    assert beginner_stat["completion_rate"] < 0.5

def test_funnel_and_heatmap_aggregation():
    users = [
        SyntheticUser(id="u1", experiment_id="exp", status="COMPLETED", steps_taken=4, duration_seconds=20.0),
        SyntheticUser(id="u2", experiment_id="exp", status="ABANDONED", steps_taken=2, duration_seconds=15.0)
    ]
    trajectories = [
        TrajectoryStep(synthetic_user_id="u1", experiment_id="exp", step_number=1, url="http://localhost:5050/", action_type="CLICK", action_target="#catalog", action_result="SUCCESS"),
        TrajectoryStep(synthetic_user_id="u1", experiment_id="exp", step_number=2, url="http://localhost:5050/products", action_type="CLICK", action_target="#item-1", action_result="SUCCESS"),
        TrajectoryStep(synthetic_user_id="u1", experiment_id="exp", step_number=3, url="http://localhost:5050/product/item-1", action_type="CLICK", action_target="#checkout", action_result="SUCCESS"),
        TrajectoryStep(synthetic_user_id="u1", experiment_id="exp", step_number=4, url="http://localhost:5050/checkout", action_type="CLICK", action_target="#confirm", action_result="SUCCESS"),
        TrajectoryStep(synthetic_user_id="u2", experiment_id="exp", step_number=1, url="http://localhost:5050/", action_type="CLICK", action_target="#catalog", action_result="SUCCESS"),
        TrajectoryStep(synthetic_user_id="u2", experiment_id="exp", step_number=2, url="http://localhost:5050/", action_type="ABANDON", action_target="#missing", action_result="FAILED")
    ]

    funnel = FunnelAndHeatmapAggregator.compute_funnel(users, trajectories)
    assert len(funnel) == 5
    assert funnel[0]["stage"] == "Landing Page"

    heatmap = FunnelAndHeatmapAggregator.compute_heatmap(trajectories)
    assert len(heatmap) > 0
    assert any(h["selector"] == "#catalog" for h in heatmap)

def test_friction_and_anomaly_detection():
    users = [
        SyntheticUser(id=f"u-{i}", experiment_id="exp", technical_proficiency="BEGINNER", status="ABANDONED", steps_taken=3, duration_seconds=20.0)
        for i in range(10)
    ]
    trajectories = []
    for u in users:
        # Simulate postal routing code failure on checkout form
        trajectories.append(TrajectoryStep(
            synthetic_user_id=u.id, experiment_id="exp", step_number=1,
            url="http://localhost:5050/checkout", action_type="TYPE", action_target="#zip_code",
            action_result="FAILED", error_message="Validation error"
        ))
        trajectories.append(TrajectoryStep(
            synthetic_user_id=u.id, experiment_id="exp", step_number=2,
            url="http://localhost:5050/checkout", action_type="ABANDON", action_target="body",
            action_result="SUCCESS"
        ))

    findings = ConfusionAndFrictionDetector.analyze_findings("exp", users, trajectories)
    assert len(findings) >= 1
    # Check that evidence-based finding was registered
    categories = [f.category for f in findings]
    assert "CONFUSING_FORM" in categories or "UNNOTICED_ACTION" in categories

def test_experiment_comparator():
    users_base = [SyntheticUser(id="u1", experiment_id="b", status="ABANDONED", steps_taken=4, duration_seconds=50.0, error_count=2)]
    users_var = [SyntheticUser(id="u2", experiment_id="v", status="COMPLETED", steps_taken=2, duration_seconds=25.0, error_count=0)]

    base_metrics = MetricsCalculator.compute_metrics("b", users_base, [])
    var_metrics = MetricsCalculator.compute_metrics("v", users_var, [])

    comparison = ExperimentComparator.compare("b", "v", base_metrics, var_metrics)
    assert comparison.completion_rate_delta > 0.0
    assert comparison.duration_delta < 0.0
    assert "Simulation results indicate" in comparison.summary
