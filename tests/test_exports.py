import pytest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.database import async_session_maker, init_db
from backend.app.models.experiment import Experiment
from backend.app.models.synthetic_user import SyntheticUser
from backend.app.models.trajectory import TrajectoryStep
from backend.app.models.metrics import ExperimentMetrics
from backend.app.models.finding import FrictionFinding
import uuid

@pytest.mark.asyncio
async def test_exports_and_streaming_endpoints():
    await init_db()
    client = TestClient(app)

    exp_id = f"test-export-{uuid.uuid4().hex[:8]}"

    # Seed experiment with metrics, finding, and trajectory
    async with async_session_maker() as session:
        exp = Experiment(
            id=exp_id,
            name="Export Verification Experiment",
            target_url="http://localhost:5055/",
            population_size=1,
            task_definition={"goal": "Purchase item"},
            status="COMPLETED",
            is_authorized=True,
            allowed_origins=["http://localhost:5055"]
        )
        session.add(exp)

        user = SyntheticUser(
            id=f"{exp_id}-user-1",
            experiment_id=exp_id,
            demographic_attributes={"age": 28},
            technical_proficiency="EXPERT",
            patience=0.6,
            risk_tolerance=0.5,
            goal_orientation=0.8,
            reading_behavior="SCANNER",
            error_tolerance=0.4,
            familiarity_level="HIGH",
            device_profile={"device_type": "desktop"},
            network_profile={"network_type": "wifi"},
            personality_traits={},
            knowledge_state={},
            memory_state={},
            current_goal="Purchase item",
            current_subgoal="add_to_cart",
            frustration_level=0.15,
            confidence_level=0.85,
            status="COMPLETED",
            steps_taken=2,
            duration_seconds=12.5,
            error_count=0
        )
        session.add(user)

        step = TrajectoryStep(
            id=f"step-{uuid.uuid4().hex[:8]}",
            synthetic_user_id=user.id,
            experiment_id=exp_id,
            step_number=1,
            url="http://localhost:5055/",
            page_title="Store Home",
            visible_text_summary="Welcome",
            interactive_elements_count=5,
            action_type="CLICK",
            action_target="#buy-btn",
            action_parameters={},
            action_reason="Selected primary CTA",
            action_confidence=0.9,
            action_result="SUCCESS",
            resulting_url="http://localhost:5055/cart",
            resulting_page_state={},
            frustration_after=0.1,
            confidence_after=0.9,
            latency_ms=120.0
        )
        session.add(step)

        metrics = ExperimentMetrics(
            id=f"m-{exp_id}",
            experiment_id=exp_id,
            task_completion_rate=1.0,
            task_abandonment_rate=0.0,
            average_task_duration=12.5,
            median_task_duration=12.5,
            p95_task_duration=12.5,
            average_actions=2.0,
            average_errors=0.0,
            retry_rate=0.0,
            back_navigation_rate=0.0,
            dead_end_rate=0.0,
            confusion_rate=0.0,
            time_to_first_successful_action=1.2,
            segment_metrics={"technical_proficiency": {"EXPERT": {"total": 1, "completed": 1, "completion_rate": 1.0, "avg_duration": 12.5, "avg_frustration": 0.15}}},
            funnel_steps=[{"stage": "home", "users_reached": 1, "conversion_rate": 1.0, "drop_off_rate": 0.0}],
            heatmap_data=[{"url": "http://localhost:5055/", "selector": "#buy-btn", "total_interactions": 1, "errors": 0, "abandonments": 0, "friction_score": 0.0}],
            action_distribution={"CLICK": 1},
            total_llm_calls=2,
            estimated_tokens_used=150
        )
        session.add(metrics)

        finding = FrictionFinding(
            id=f"f-{exp_id}",
            experiment_id=exp_id,
            severity="MEDIUM",
            category="CTA_VISIBILITY",
            title="Non-standard button label",
            description="Button labeled unusually",
            evidence={"selector": "#buy-btn"},
            recommendation="Rename to standard label"
        )
        session.add(finding)
        await session.commit()

    # 1. Test JSON Export
    json_resp = client.get(f"/api/experiments/{exp_id}/export/json")
    assert json_resp.status_code == 200
    assert "attachment" in json_resp.headers.get("content-disposition", "")
    data = json_resp.json()
    assert data["experiment"]["id"] == exp_id
    assert data["metrics"]["task_completion_rate"] == 1.0
    assert len(data["findings"]) == 1
    assert len(data["synthetic_users"]) == 1
    assert len(data["synthetic_users"][0]["trajectories"]) == 1

    # 2. Test CSV Export
    csv_resp = client.get(f"/api/experiments/{exp_id}/export/csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers.get("content-type", "")
    csv_text = csv_resp.text
    assert "experiment_id,user_id,technical_proficiency" in csv_text
    assert exp_id in csv_text
    assert "#buy-btn" in csv_text

    # 3. Test Markdown Audit Report Export
    report_resp = client.get(f"/api/experiments/{exp_id}/export/report")
    assert report_resp.status_code == 200
    assert "text/markdown" in report_resp.headers.get("content-type", "")
    report_text = report_resp.text
    assert "Synthetic Humans - Usability & Behavioral Audit Report" in report_text
    assert exp_id in report_text
    assert "Non-standard button label" in report_text
    assert "Executive Summary" in report_text
