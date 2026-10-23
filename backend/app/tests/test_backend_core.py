import pytest
from backend.app.config import settings
from backend.app.simulation.population import PopulationGenerator
from backend.app.simulation.evaluator import TaskEvaluator
from backend.app.analysis.reports import ExperimentComparator
from backend.app.analysis.metrics import MetricsCalculator
from backend.app.models.synthetic_user import SyntheticUser

def test_config_defaults():
    assert settings.PROJECT_NAME == "Synthetic Humans"
    assert settings.DEFAULT_LLM_PROVIDER in ("mock", "openai", "gemini")
    assert settings.HEADLESS_BROWSER is True

def test_population_generator_core():
    pop = PopulationGenerator.generate_population(
        experiment_id="core-test",
        population_size=5,
        random_seed=100
    )
    assert len(pop) == 5
    for u in pop:
        assert u.experiment_id == "core-test"
        assert u.technical_proficiency in ("BEGINNER", "INTERMEDIATE", "EXPERT")
        assert 0.0 <= u.patience <= 1.0

def test_evaluator_url_matches():
    task = {
        "goal": "Test goal",
        "success_conditions": [{"type": "url_contains", "value": "checkout"}],
        "failure_conditions": []
    }
    obs = {"url": "http://localhost:5050/checkout", "page_title": "Checkout", "visible_text_summary": ""}
    status = TaskEvaluator.evaluate_task_status(task, obs, 1, 10, 5.0, 60.0)
    assert status == "SUCCESS"
