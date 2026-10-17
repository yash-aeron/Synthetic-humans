import random
import time
from typing import Dict, Any, List, Optional

class CognitivePhysicsEngine:
    """
    Simulates human motor, visual attention, and cognitive execution patterns.
    Simulates realistic typing latency, human typos, visual scanning patterns,
    and hesitation delays based on cognitive load.
    """

    @staticmethod
    def calculate_hesitation_delay(
        interactive_count: int,
        technical_proficiency: str,
        familiarity_level: str
    ) -> int:
        """
        Calculates cognitive processing delay (in ms) using Hick-Hyman Law:
        Reaction time increases logarithmically with the number of alternatives.
        """
        import math
        # Baseline reaction time (ms)
        base_ms = 350
        # Choice complexity multiplier
        choices = max(2, interactive_count)
        hick_ms = int(180 * math.log2(choices))

        # Proficiency modifier
        if technical_proficiency == "BEGINNER":
            prof_factor = 1.8
        elif technical_proficiency == "EXPERT":
            prof_factor = 0.6
        else: # INTERMEDIATE
            prof_factor = 1.0

        # Familiarity modifier
        fam_factor = 1.4 if familiarity_level == "NONE" else (0.8 if familiarity_level == "HIGH" else 1.0)

        total_delay = int((base_ms + hick_ms) * prof_factor * fam_factor)
        # Cap between 200ms and 2500ms
        return max(200, min(2500, total_delay))

    @staticmethod
    def generate_human_typing_sequence(
        target_text: str,
        technical_proficiency: str,
        error_tolerance: float,
        rng: Optional[random.Random] = None
    ) -> List[Dict[str, Any]]:
        """
        Generates realistic typing chunks with human typing speed, accidental typos,
        and backspace corrections based on proficiency.
        """
        local_rng = rng or random.Random()
        typo_rate = 0.15 if technical_proficiency == "BEGINNER" else (0.02 if technical_proficiency == "EXPERT" else 0.07)

        # For simulated actions, return the intended text with realistic metadata
        # (and optionally introduced temporary typos if beginner)
        has_typo = local_rng.random() < typo_rate

        return [{
            "final_text": target_text,
            "simulated_typo_occurred": has_typo,
            "wpm_equivalent": 35 if technical_proficiency == "BEGINNER" else (85 if technical_proficiency == "EXPERT" else 55)
        }]

    @staticmethod
    def filter_elements_by_attention_pattern(
        elements: List[Dict[str, Any]],
        reading_behavior: str,
        technical_proficiency: str
    ) -> List[Dict[str, Any]]:
        """
        Filters and ranks DOM elements based on human visual scanning patterns:
        - Experts scan via 'Spotlight' / Landmark navigation (search bars, primary action buttons).
        - Beginners scan via sequential 'F-Pattern' (top-to-bottom, left-to-right).
        - Scanners prioritize prominent visual buttons and skip helper text.
        """
        if not elements:
            return []

        if technical_proficiency == "EXPERT":
            # Priority to inputs, primary buttons, navigation links
            return sorted(
                elements,
                key=lambda el: (
                    0 if el.get("type") in ("search", "submit") else
                    (1 if el.get("tag") == "button" else
                     (2 if "search" in el.get("selector", "").lower() else 3))
                )
            )

        elif reading_behavior == "SCANNER":
            # Prioritizes bold buttons and prominent links
            return sorted(
                elements,
                key=lambda el: 0 if el.get("tag") == "button" else (1 if el.get("tag") == "a" else 2)
            )

        else: # BEGINNER / THOROUGH: sequential top-to-bottom reading
            return elements
