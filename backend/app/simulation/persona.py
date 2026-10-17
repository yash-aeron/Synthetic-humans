from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class PersonaProfile:
    technical_proficiency: str # BEGINNER, INTERMEDIATE, EXPERT
    patience: float # 0.0 (impatient) - 1.0 (very patient)
    risk_tolerance: float # 0.0 (risk averse) - 1.0 (exploratory)
    goal_orientation: float # 0.0 (easily distracted) - 1.0 (strictly focused)
    reading_behavior: str # SCANNER, THOROUGH, SELECTIVE
    error_tolerance: float # 0.0 - 1.0
    familiarity_level: str # NONE, LOW, MEDIUM, HIGH

    # Behavioral policy weights
    abandonment_threshold: float = 0.8
    exploration_probability: float = 0.2
    scan_delay_ms: int = 500

    def __post_init__(self):
        # Calculate dynamic behavioral parameters from core traits
        if self.technical_proficiency == "BEGINNER":
            self.exploration_probability = 0.35 * (1.0 - self.risk_tolerance)
            self.abandonment_threshold = 0.5 + 0.3 * self.patience
            self.scan_delay_ms = 1200
        elif self.technical_proficiency == "EXPERT":
            self.exploration_probability = 0.1
            self.abandonment_threshold = 0.6 + 0.2 * self.patience
            self.scan_delay_ms = 300
        else: # INTERMEDIATE
            self.exploration_probability = 0.2
            self.abandonment_threshold = 0.55 + 0.25 * self.patience
            self.scan_delay_ms = 700

    def should_read_explanatory_text(self) -> bool:
        """Determines if the persona spends cognitive budget reading helper text."""
        if self.reading_behavior == "THOROUGH":
            return True
        if self.reading_behavior == "SCANNER":
            return False
        return self.technical_proficiency == "BEGINNER"

    def should_verify_before_click(self) -> bool:
        """Risk-averse users verify inputs and destructive buttons twice."""
        return self.risk_tolerance < 0.4
