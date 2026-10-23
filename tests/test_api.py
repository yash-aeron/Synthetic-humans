import pytest
import asyncio
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db

@pytest.fixture(autouse=True, scope="module")
def setup_test_db():
    asyncio.run(init_db())

client = TestClient(app)

def test_health_check_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "Synthetic Humans" in data["service"]

def test_experiment_creation_and_retrieval():
    payload = {
        "name": "E2E Laptop Checkout Usability Test",
        "target_url": "http://localhost:5050/",
        "description": "Evaluate user checkout flow",
        "population_size": 10,
        "task_definition": {
            "goal": "Purchase a laptop",
            "success_conditions": [
                {"type": "url_contains", "value": "order-placed"}
            ],
            "optional_conditions": [],
            "failure_conditions": []
        },
        "max_steps_per_user": 20,
        "max_duration_seconds": 60,
        "concurrency": 2,
        "random_seed": 42,
        "is_authorized": True
    }

    res = client.post("/api/experiments", json=payload)
    assert res.status_code == 201
    data = res.json()
    exp_id = data["id"]
    assert exp_id is not None
    assert data["population_size"] == 10
    assert data["status"] == "CREATED"

    # List experiments
    list_res = client.get("/api/experiments")
    assert list_res.status_code == 200
    experiments = list_res.json()
    assert any(e["id"] == exp_id for e in experiments)

    # Get single experiment
    get_res = client.get(f"/api/experiments/{exp_id}")
    assert get_res.status_code == 200
    exp_detail = get_res.json()
    assert exp_detail["experiment"]["id"] == exp_id

    # List users generated for experiment
    users_res = client.get(f"/api/experiments/{exp_id}/users")
    assert users_res.status_code == 200
    users = users_res.json()
    assert len(users) == 10
    assert users[0]["technical_proficiency"] in ("BEGINNER", "INTERMEDIATE", "EXPERT")

def test_unauthorized_experiment_rejected():
    payload = {
        "name": "Unauthorized Test",
        "target_url": "http://example.com",
        "population_size": 5,
        "task_definition": {"goal": "test", "success_conditions": []},
        "is_authorized": False
    }
    res = client.post("/api/experiments", json=payload)
    assert res.status_code == 400
    assert "authorization confirmation is required" in res.json()["detail"]
