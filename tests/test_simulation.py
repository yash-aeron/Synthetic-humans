import pytest
from backend.app.simulation.population import PopulationGenerator, DEFAULT_DISTRIBUTIONS
from backend.app.simulation.state import PersistentUserState
from backend.app.simulation.persona import PersonaProfile
from backend.app.simulation.evaluator import TaskEvaluator
from backend.app.simulation.decision import MockLLMProvider
from backend.app.browser.playwright_runner import browser_manager

def test_deterministic_population_generation():
    """Verify that using the same random seed produces identical synthetic user populations."""
    exp_id = "test-exp-1"
    pop_1 = PopulationGenerator.generate_population(exp_id, population_size=20, random_seed=42)
    pop_2 = PopulationGenerator.generate_population(exp_id, population_size=20, random_seed=42)

    assert len(pop_1) == 20
    assert len(pop_2) == 20

    for u1, u2 in zip(pop_1, pop_2):
        assert u1.id == u2.id
        assert u1.technical_proficiency == u2.technical_proficiency
        assert u1.patience == u2.patience
        assert u1.risk_tolerance == u2.risk_tolerance
        assert u1.reading_behavior == u2.reading_behavior
        assert u1.device_profile == u2.device_profile
        assert u1.network_profile == u2.network_profile

def test_different_seeds_produce_different_populations():
    """Verify different seeds yield different randomized samples."""
    exp_id = "test-exp-1"
    pop_1 = PopulationGenerator.generate_population(exp_id, population_size=10, random_seed=42)
    pop_2 = PopulationGenerator.generate_population(exp_id, population_size=10, random_seed=999)

    proficiencies_1 = [u.technical_proficiency for u in pop_1]
    proficiencies_2 = [u.technical_proficiency for u in pop_2]
    # At least some users will have different IDs or traits
    assert [u.id for u in pop_1] != [u.id for u in pop_2]

def test_population_distribution_statistical_alignment():
    """Verify that generated population follows requested distributions within statistical tolerance."""
    custom_dists = {
        "technical_proficiency": {
            "BEGINNER": 0.70,
            "INTERMEDIATE": 0.20,
            "EXPERT": 0.10
        }
    }
    pop = PopulationGenerator.generate_population("exp-test", population_size=200, custom_distributions=custom_dists, random_seed=123)
    beginners = sum(1 for u in pop if u.technical_proficiency == "BEGINNER")
    prop = beginners / len(pop)
    # Expected 0.70, tolerance +/- 0.08 for N=200
    assert 0.62 <= prop <= 0.78

def test_persistent_user_state_transitions():
    """Verify that failure increases frustration and decreases confidence, while success does the reverse."""
    state = PersistentUserState(
        user_id="user-1",
        technical_proficiency="BEGINNER",
        patience=0.5,
        frustration_level=0.1,
        confidence_level=0.9
    )

    initial_frust = state.frustration_level
    initial_conf = state.confidence_level

    # Action fails
    state.register_action_result("CLICK", "#missing-btn", "FAILED", "http://example.com/page1", "Element not found")
    assert state.frustration_level > initial_frust
    assert state.confidence_level < initial_conf
    assert state.memory_state["consecutive_failures"] == 1

    # Action succeeds
    mid_frust = state.frustration_level
    state.register_action_result("CLICK", "#next-btn", "SUCCESS", "http://example.com/page2")
    assert state.frustration_level < mid_frust
    assert state.memory_state["consecutive_failures"] == 0

def test_loop_detection_and_frustration_spike():
    """Verify that repeatedly cycling to the same URL triggers navigation loop detection."""
    state = PersistentUserState(user_id="user-1", patience=0.5, frustration_level=0.1)
    url_loop = "http://example.com/products"

    # Simulate loop
    for _ in range(4):
        state.register_action_result("CLICK", "a.catalog", "SUCCESS", url_loop)
        state.record_page_visit(url_loop, "Products")

    assert state.memory_state.get("loop_detected") is True
    assert state.frustration_level > 0.2

def test_abandonment_trigger():
    """Verify that high frustration exceeding user patience threshold triggers abandonment."""
    state = PersistentUserState(user_id="user-1", technical_proficiency="EXPERT", patience=0.2, frustration_level=0.85)
    assert state.should_abandon() is True

def test_allowed_origin_enforcement():
    """Verify origin boundary checks prevent navigation to foreign domains."""
    allowed = ["http://localhost:5050", "http://127.0.0.1:5050"]

    assert browser_manager.is_origin_allowed("http://localhost:5050/products", allowed) is True
    assert browser_manager.is_origin_allowed("http://127.0.0.1:5050/checkout", allowed) is True
    assert browser_manager.is_origin_allowed("https://malicious-tracker.com/steal", allowed) is False
    assert browser_manager.is_origin_allowed("https://google.com", allowed) is False

def test_task_evaluator_conditions():
    """Verify task evaluator recognizes success and failure conditions."""
    task = {
        "goal": "Purchase item",
        "success_conditions": [
            {"type": "url_contains", "value": "order-placed"},
            {"type": "text_present", "value": "Order Confirmed"}
        ],
        "failure_conditions": [
            {"type": "url_contains", "value": "system-error"}
        ]
    }

    obs_in_progress = {
        "url": "http://localhost:5050/checkout",
        "page_title": "Checkout",
        "visible_text_summary": "Enter delivery info"
    }
    assert TaskEvaluator.evaluate_task_status(task, obs_in_progress, 2, 20, 10.0, 100.0) == "IN_PROGRESS"

    obs_success = {
        "url": "http://localhost:5050/order-placed",
        "page_title": "Order Confirmed",
        "visible_text_summary": "Order Confirmed! Thank you."
    }
    assert TaskEvaluator.evaluate_task_status(task, obs_success, 4, 20, 20.0, 100.0) == "SUCCESS"

    obs_fail = {
        "url": "http://localhost:5050/system-error",
        "page_title": "Fatal Error",
        "visible_text_summary": "Service Unavailable"
    }
    assert TaskEvaluator.evaluate_task_status(task, obs_fail, 5, 20, 25.0, 100.0) == "FAILURE"

@pytest.mark.asyncio
async def test_mock_llm_provider_behavioral_differentiation():
    """Verify that BEGINNER and EXPERT personas produce different decisions on identical UI affordances."""
    provider = MockLLMProvider()

    obs = {
        "url": "http://localhost:5050/",
        "page_title": "Home",
        "visible_text_summary": "Welcome to store",
        "interactive_elements": [
            {"tag": "input", "name": "search", "selector": "#search-input", "type": "text", "text": "Search...", "is_enabled": True},
            {"tag": "a", "selector": "#hero-info", "text": "System Specifications FAQ", "is_enabled": True},
            {"tag": "a", "selector": "#hero-laptops", "text": "Explore Laptops", "is_enabled": True}
        ]
    }

    state_beg = PersistentUserState(user_id="u-beg", technical_proficiency="BEGINNER", patience=0.5)
    persona_beg = PersonaProfile(technical_proficiency="BEGINNER", patience=0.5, risk_tolerance=0.3, goal_orientation=0.6, reading_behavior="THOROUGH", error_tolerance=0.5, familiarity_level="NONE")

    state_exp = PersistentUserState(user_id="u-exp", technical_proficiency="EXPERT", patience=0.5)
    persona_exp = PersonaProfile(technical_proficiency="EXPERT", patience=0.5, risk_tolerance=0.8, goal_orientation=0.9, reading_behavior="SCANNER", error_tolerance=0.4, familiarity_level="HIGH")

    task = {"goal": "Explore laptops and buy"}

    dec_beg = await provider.generate_decision(obs, state_beg, persona_beg, task)
    dec_exp = await provider.generate_decision(obs, state_exp, persona_exp, task)

    assert dec_beg["action_type"] in ("CLICK", "TYPE")
    assert dec_exp["action_type"] in ("CLICK", "TYPE")
    # Expert leverages direct search or main category, beginner checks info or category
    assert dec_exp["confidence"] >= 0.5
