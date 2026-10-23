import pytest
from backend.app.simulation.decision import RealLLMProvider, get_llm_provider
from backend.app.simulation.state import PersistentUserState
from backend.app.simulation.persona import PersonaProfile

@pytest.mark.asyncio
async def test_real_llm_provider_prompt_construction():
    provider = RealLLMProvider(provider_name="openai", api_key="sk-test-key", model="gpt-4o-mini")

    state = PersistentUserState(
        user_id="user-prompt-test",
        technical_proficiency="BEGINNER",
        patience=0.4,
        frustration_level=0.35,
        confidence_level=0.65,
        initial_goal="Purchase a monitor"
    )
    state.current_subgoal = "find_monitor_category"

    persona = PersonaProfile(
        technical_proficiency="BEGINNER",
        patience=0.4,
        risk_tolerance=0.3,
        goal_orientation=0.7,
        reading_behavior="THOROUGH",
        error_tolerance=0.5,
        familiarity_level="LOW"
    )

    observation = {
        "url": "http://example.com/shop",
        "page_title": "Electronics Catalog",
        "visible_text_summary": "Top Monitors and Laptops",
        "interactive_elements": [
            {"tag": "button", "selector": "#view-monitors", "text": "View Monitors", "name": "monitors"}
        ]
    }

    task_definition = {"goal": "Purchase a monitor"}

    sys_prompt, user_prompt = provider._build_prompts(observation, state, persona, task_definition)

    assert "BEGINNER" in sys_prompt
    assert "0.35" in sys_prompt  # frustration level
    assert "find_monitor_category" in sys_prompt
    assert "Purchase a monitor" in sys_prompt
    assert "http://example.com/shop" in user_prompt
    assert "#view-monitors" in user_prompt

@pytest.mark.asyncio
async def test_real_llm_provider_fallback_when_no_api_key():
    provider = RealLLMProvider(provider_name="gemini", api_key=None)

    state = PersistentUserState(user_id="user-fallback", patience=0.5)
    persona = PersonaProfile(technical_proficiency="INTERMEDIATE", patience=0.5, risk_tolerance=0.5, goal_orientation=0.5, reading_behavior="SCANNER", error_tolerance=0.5, familiarity_level="MEDIUM")
    obs = {
        "url": "http://example.com",
        "page_title": "Home",
        "visible_text_summary": "Welcome",
        "interactive_elements": [
            {"tag": "a", "selector": "#shop-link", "text": "Shop Products", "is_enabled": True}
        ]
    }
    task = {"goal": "Shop"}

    decision = await provider.generate_decision(obs, state, persona, task)
    assert decision["action_type"] in ("CLICK", "WAIT", "SCROLL")
    assert decision["confidence"] > 0.0

def test_get_llm_provider_factory():
    p_mock = get_llm_provider({"provider": "mock"})
    assert p_mock.__class__.__name__ == "MockLLMProvider"

    p_openai = get_llm_provider({"provider": "openai", "api_key": "test"})
    assert isinstance(p_openai, RealLLMProvider)
    assert p_openai.provider_name == "openai"

    p_gemini = get_llm_provider({"provider": "gemini", "api_key": "test"})
    assert isinstance(p_gemini, RealLLMProvider)
    assert p_gemini.provider_name == "gemini"
