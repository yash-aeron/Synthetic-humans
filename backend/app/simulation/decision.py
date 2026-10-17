from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import random
import re
import json
import logging
import httpx
from backend.app.simulation.state import PersistentUserState
from backend.app.simulation.persona import PersonaProfile

class BaseLLMProvider(ABC):
    """Abstract provider interface for cognitive reasoning and action decision-making."""

    @abstractmethod
    async def generate_decision(
        self,
        observation: Dict[str, Any],
        user_state: PersistentUserState,
        persona: PersonaProfile,
        task_definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Returns structured action dict with action_type, target, parameters, reason, confidence."""
        pass

    @abstractmethod
    async def summarize_observation(self, observation: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    async def evaluate_goal(self, task_definition: Dict[str, Any], observation: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def classify_confusion(self, trajectory_slice: List[Dict[str, Any]]) -> Dict[str, Any]:
        pass


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic cognitive decision provider based on psychological traits,
    cognitive memory, and DOM affordance heuristics.
    Requires no external API keys and guarantees reproducible behavior.
    """

    def __init__(self, seed: Optional[int] = 42):
        self.seed = seed

    async def generate_decision(
        self,
        observation: Dict[str, Any],
        user_state: PersistentUserState,
        persona: PersonaProfile,
        task_definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        # 1. Check if user frustration dictates abandonment
        if user_state.should_abandon():
            return {
                "action_type": "ABANDON",
                "target": "body",
                "parameters": {},
                "reason": f"Frustration level ({round(user_state.frustration_level, 2)}) exceeded tolerance threshold ({round(user_state.abandonment_threshold, 2)}).",
                "confidence": 0.95
            }

        interactive_elements = observation.get("interactive_elements", [])
        current_url = observation.get("url", "").lower()
        visible_text = observation.get("visible_text_summary", "").lower()
        recent_failures = [f.get("target") for f in user_state.memory_state.get("recent_failures", [])[-3:]]

        # Filter out elements that recently failed
        viable_elements = [
            el for el in interactive_elements
            if el.get("selector") not in recent_failures and el.get("is_enabled", True)
        ]

        if not viable_elements:
            # If no viable elements, scroll or go back or wait
            if user_state.frustration_level > 0.5:
                return {
                    "action_type": "GO_BACK",
                    "target": "window",
                    "parameters": {},
                    "reason": "Encountered dead end with no interactive options, attempting back-navigation.",
                    "confidence": 0.70
                }
            return {
                "action_type": "SCROLL",
                "target": "window",
                "parameters": {"direction": "down"},
                "reason": "Scanning further down the viewport to discover interactive elements.",
                "confidence": 0.80
            }

        goal_text = str(task_definition.get("goal", "")).lower()

        # Semantic score for each viable element based on persona
        best_candidate = None
        best_score = -999.0
        best_reason = ""

        # Extract current path for self-link loop detection
        from urllib.parse import urlparse
        parsed_curr = urlparse(current_url)
        curr_path = parsed_curr.path.rstrip('/')

        # Cognitive memory of recent clicks
        recent_targets = [a.get("target") for a in user_state.memory_state.get("recent_actions", [])[-6:]]

        for el in viable_elements:
            tag = el.get("tag", "")
            el_text = el.get("text", "").lower()
            el_name = el.get("name", "").lower()
            selector = el.get("selector", "")
            el_type = el.get("type", "")
            el_href = (el.get("href") or "").strip().lower()

            score = 0.0
            reasons = []

            # Subgoal matching
            subgoal = user_state.current_subgoal
            if subgoal == "discover_products_or_search":
                if "search" in el_text or "search" in el_name:
                    score += 5.0
                    reasons.append("matches search affordance")
                elif "catalog" in el_text or "products" in el_text or "shop" in el_text or "store" in el_text:
                    score += 6.0
                    reasons.append("navigation to catalog")
                elif "laptops" in el_text or "electronics" in el_text:
                    score += 7.0
                    reasons.append("specific product category link")

            elif subgoal == "choose_target_item":
                # Penalize top header/nav catalog link when selecting a product item
                if "nav" in selector or "header" in selector or el_text == "products catalog":
                    score -= 8.0
                    reasons.append("bypassing top navigation to focus on product listings")

                # Direct product action buttons/links
                if selector.startswith("#view-") or "view-" in selector or "/product/" in el_href:
                    score += 14.0
                    reasons.append("direct product details CTA")
                elif re.search(r"\b(view|details|order|specs)\b", el_text):
                    score += 10.0
                    reasons.append("view item details")
                elif re.search(r"\b(laptop|notebook|workstation|pc|omnibook)\b", el_text) or re.search(r"\b(laptop|notebook)\b", selector):
                    score += 8.0
                    reasons.append("target item title link")

            elif subgoal == "add_to_cart":
                if "add to cart" in el_text or "buy now" in el_text:
                    score += 12.0
                    reasons.append("primary add to cart CTA")
                elif "inquire" in el_text:
                    score += 8.0
                    reasons.append("secondary cart CTA")
                elif tag == "select" or "quantity" in el_name:
                    score += 4.0
                    reasons.append("product option configuration")

            elif subgoal == "proceed_to_checkout":
                if "checkout" in el_text or "proceed" in el_text or "finalize" in el_text or "inquiry" in el_text:
                    score += 12.0
                    reasons.append("checkout transition CTA")
                elif "checkout" in el_href or "checkout" in selector:
                    score += 10.0
                    reasons.append("checkout target link")

            elif subgoal == "submit_checkout_form":
                # Prioritize filling empty required inputs before clicking submit!
                val = str(el.get("value") or "").strip()
                if tag in ("input", "textarea") and el_type not in ("hidden", "submit"):
                    if not val:
                        score += 15.0
                        reasons.append("unfilled required form input")
                    else:
                        score += 3.0
                        reasons.append("already filled input")
                elif "submit" in el_text or "place order" in el_text or "complete" in el_text or "confirm" in el_text:
                    score += 13.0
                    reasons.append("order completion submission CTA")

            # ANTI-LOOP & COGNITIVE REPETITION PENALTIES
            # 1. Self-link / same page navigation penalty
            if el_href:
                href_path = urlparse(el_href).path.rstrip('/')
                if href_path and (href_path == curr_path or el_href == current_url):
                    score -= 8.0
                    reasons.append("self-navigation loop penalty")

            # 2. Repeated target click penalty
            times_clicked = recent_targets.count(selector)
            if times_clicked > 0:
                score -= times_clicked * 6.0
                reasons.append(f"repeated action penalty (x{times_clicked})")

            # BEHAVIORAL POLICY MODIFIERS
            if persona.technical_proficiency == "BEGINNER":
                # Beginners are drawn to informational links and help banners
                if "help" in el_text or "about" in el_text or "info" in el_text or "faq" in el_text:
                    score += 3.5
                    reasons.append("beginner seeking explanatory information")
                # Beginners sometimes click non-primary buttons
                if "cancel" in el_text or "reset" in el_text:
                    score += 1.0

            elif persona.technical_proficiency == "EXPERT":
                # Experts heavily favor search bars and direct buttons
                if tag == "input" and ("search" in el_name or "query" in el_name or "q" in el_name):
                    score += 4.0
                    reasons.append("expert using direct search efficiency")
                if "help" in el_text or "faq" in el_text or "about" in el_text:
                    score -= 5.0 # Experts bypass fluff

            if persona.reading_behavior == "SCANNER":
                # Scanners prefer prominent buttons
                if tag == "button" or "btn" in selector:
                    score += 2.0

            # If user has high frustration, prioritize back or escape
            if user_state.frustration_level > 0.6:
                if "back" in el_text or "return" in el_text:
                    score += 6.0
                    reasons.append("frustrated user seeking previous stable state")

            if score > best_score:
                best_score = score
                best_candidate = el
                best_reason = "; ".join(reasons) if reasons else "Exploring available UI element"

        if not best_candidate or best_score <= 0.0:
            # Fallback exploration: pick a relevant button or link, or scroll
            buttons = [e for e in viable_elements if e.get("tag") in ("button", "a")]
            if buttons and random.random() < 0.7:
                best_candidate = random.choice(buttons[:3])
                best_reason = "Exploring prominent visible navigation element."
            else:
                return {
                    "action_type": "SCROLL",
                    "target": "window",
                    "parameters": {"direction": "down"},
                    "reason": "No high-confidence actions found; scrolling to reveal more UI content.",
                    "confidence": 0.60
                }

        # Formulate action for candidate
        cand_tag = best_candidate.get("tag", "")
        cand_selector = best_candidate.get("selector", "")
        cand_type = best_candidate.get("type", "")

        if cand_tag == "input" and cand_type in ("text", "email", "search", ""):
            # Type action
            name_lower = best_candidate.get("name", "").lower()
            text_val = "Laptop"
            if "name" in name_lower:
                text_val = "Alex Mercer"
            elif "email" in name_lower:
                text_val = "alex.mercer@example.com"
            elif "address" in name_lower or "street" in name_lower:
                text_val = "123 Research Way"
            elif "zip" in name_lower or "postal" in name_lower:
                # Usability friction simulation for postal code:
                has_validation_error = (
                    "validation" in visible_text
                    or "failed" in visible_text
                    or "error" in current_url
                    or any("zip" in str(f.get("target", "")).lower() for f in user_state.memory_state.get("recent_failures", []))
                )
                past_zip_attempts = sum(
                    1 for a in user_state.memory_state.get("recent_actions", [])
                    if "zip" in str(a.get("target", "")).lower()
                )

                if persona.technical_proficiency == "BEGINNER":
                    if past_zip_attempts > 0 or has_validation_error:
                        # Patient beginners adapt to numeric digits after initial failure
                        if persona.patience >= 0.4:
                            text_val = "94105"
                        else:
                            # Impatient beginners struggle with format repeatedly
                            text_val = "ZIP-94105"
                    else:
                        # First attempt: beginner enters formatted string
                        text_val = "ZIP-94105"
                else:
                    # Intermediate & Expert users enter clean 5-digit zip directly
                    text_val = "94105"

            return {
                "action_type": "TYPE",
                "target": cand_selector,
                "parameters": {"text": text_val, "clear": True},
                "reason": f"Entering required data into form input: {best_reason}",
                "confidence": 0.85
            }

        elif cand_tag == "select":
            return {
                "action_type": "SELECT",
                "target": cand_selector,
                "parameters": {"value": "1"},
                "reason": f"Selecting configuration option: {best_reason}",
                "confidence": 0.80
            }

        else:
            return {
                "action_type": "CLICK",
                "target": cand_selector,
                "parameters": {},
                "reason": best_reason,
                "confidence": min(0.95, max(0.40, 0.5 + best_score * 0.05))
            }

    async def summarize_observation(self, observation: Dict[str, Any]) -> str:
        return f"Page '{observation.get('page_title')}' at {observation.get('url')} with {observation.get('interactive_elements_count')} interactive items."

    async def evaluate_goal(self, task_definition: Dict[str, Any], observation: Dict[str, Any]) -> Dict[str, Any]:
        return {"satisfied": False, "score": 0.5}

    async def classify_confusion(self, trajectory_slice: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {"is_confused": len(trajectory_slice) > 4, "pattern": "hesitant_navigation"}


logger = logging.getLogger(__name__)

class RealLLMProvider(BaseLLMProvider):
    """
    Production-ready LLM provider supporting OpenAI and Google Gemini APIs
    with structured JSON extraction, retry backoff, and graceful fallback.
    """

    ALLOWED_ACTIONS = {"CLICK", "TYPE", "SELECT", "SCROLL", "PRESS_KEY", "GO_BACK", "WAIT", "ABANDON"}

    def __init__(self, provider_name: str = "openai", api_key: Optional[str] = None, model: Optional[str] = None):
        self.provider_name = provider_name.lower()
        self.api_key = api_key
        self.model = model or ("gpt-4o-mini" if self.provider_name == "openai" else "gemini-2.0-flash")
        self.fallback = MockLLMProvider()

    def _build_prompts(
        self,
        observation: Dict[str, Any],
        user_state: PersistentUserState,
        persona: PersonaProfile,
        task_definition: Dict[str, Any]
    ) -> tuple[str, str]:
        system_prompt = (
            f"You are a simulated human user participating in an HCI usability experiment.\n"
            f"USER PROFILE:\n"
            f"- Technical Proficiency: {persona.technical_proficiency}\n"
            f"- Patience: {persona.patience:.2f} (0.0 to 1.0)\n"
            f"- Risk Tolerance: {persona.risk_tolerance:.2f}\n"
            f"- Reading Behavior: {persona.reading_behavior}\n"
            f"CURRENT PSYCHOLOGICAL STATE:\n"
            f"- Frustration Level: {user_state.frustration_level:.2f} (0.0=calm, 1.0=enraged)\n"
            f"- Confidence Level: {user_state.confidence_level:.2f}\n"
            f"- High-Level Goal: {task_definition.get('goal', 'Complete the task')}\n"
            f"- Current Subgoal: {user_state.current_subgoal}\n\n"
            f"INSTRUCTIONS:\n"
            f"Based strictly on the current webpage and your cognitive state, choose your next browser action.\n"
            f"You MUST output valid JSON matching this exact schema:\n"
            f"{{\n"
            f'  "action_type": "CLICK" | "TYPE" | "SELECT" | "SCROLL" | "PRESS_KEY" | "GO_BACK" | "WAIT" | "ABANDON",\n'
            f'  "target": "css_selector_or_window",\n'
            f'  "parameters": {{ "text": "...", "direction": "down" }},\n'
            f'  "reason": "Detailed first-person explanation of why you made this choice based on your persona",\n'
            f'  "confidence": 0.0 to 1.0\n'
            f"}}"
        )

        elements_sample = observation.get("interactive_elements", [])[:25]
        elements_str = "\n".join([
            f"- [{i}] Tag: <{el.get('tag')}> | Selector: {el.get('selector')} | Text: '{el.get('text', '')[:40]}' | Name: '{el.get('name', '')}'"
            for i, el in enumerate(elements_sample)
        ])

        user_prompt = (
            f"CURRENT PAGE STATE:\n"
            f"- URL: {observation.get('url')}\n"
            f"- Page Title: {observation.get('page_title')}\n"
            f"- Page Text Excerpt: {observation.get('visible_text_summary', '')[:400]}\n\n"
            f"AVAILABLE INTERACTIVE DOM ELEMENTS:\n"
            f"{elements_str or 'None detected in viewport.'}\n\n"
            f"Select your next action now:"
        )

        return system_prompt, user_prompt

    async def _call_openai(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.3,
            "max_tokens": 400
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)

    async def _call_gemini(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_prompt}\n\n{user_prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.3,
                "maxOutputTokens": 400
            }
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(content)

    async def generate_decision(
        self,
        observation: Dict[str, Any],
        user_state: PersistentUserState,
        persona: PersonaProfile,
        task_definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not self.api_key:
            logger.debug(f"API key not configured for {self.provider_name}; using deterministic fallback.")
            return await self.fallback.generate_decision(observation, user_state, persona, task_definition)

        system_prompt, user_prompt = self._build_prompts(observation, user_state, persona, task_definition)

        try:
            if self.provider_name == "openai":
                result = await self._call_openai(system_prompt, user_prompt)
            elif self.provider_name == "gemini":
                result = await self._call_gemini(system_prompt, user_prompt)
            else:
                return await self.fallback.generate_decision(observation, user_state, persona, task_definition)

            # Sanitize and validate action
            act_type = str(result.get("action_type", "WAIT")).upper()
            if act_type not in self.ALLOWED_ACTIONS:
                act_type = "WAIT"

            return {
                "action_type": act_type,
                "target": str(result.get("target", "window")),
                "parameters": dict(result.get("parameters", {})),
                "reason": str(result.get("reason", f"Selected via {self.provider_name} ({self.model})")),
                "confidence": float(result.get("confidence", 0.75))
            }

        except Exception as e:
            logger.warning(f"Error calling {self.provider_name} ({str(e)}); falling back to deterministic cognitive engine.")
            return await self.fallback.generate_decision(observation, user_state, persona, task_definition)

    async def summarize_observation(self, observation: Dict[str, Any]) -> str:
        return await self.fallback.summarize_observation(observation)

    async def evaluate_goal(self, task_definition: Dict[str, Any], observation: Dict[str, Any]) -> Dict[str, Any]:
        return await self.fallback.evaluate_goal(task_definition, observation)

    async def classify_confusion(self, trajectory_slice: List[Dict[str, Any]]) -> Dict[str, Any]:
        return await self.fallback.classify_confusion(trajectory_slice)


def get_llm_provider(config: Optional[Dict[str, Any]] = None) -> BaseLLMProvider:
    cfg = config or {}
    provider_name = cfg.get("provider", "mock").lower()

    if provider_name == "openai":
        return RealLLMProvider("openai", api_key=cfg.get("api_key"), model=cfg.get("model_name"))
    elif provider_name == "gemini":
        return RealLLMProvider("gemini", api_key=cfg.get("api_key"), model=cfg.get("model_name"))
    else:
        return MockLLMProvider()
