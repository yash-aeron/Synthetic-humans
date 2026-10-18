import random
import uuid
from typing import Dict, Any, List, Optional
from backend.app.models.synthetic_user import SyntheticUser

DEFAULT_DISTRIBUTIONS = {
    "technical_proficiency": {
        "BEGINNER": 0.40,
        "INTERMEDIATE": 0.45,
        "EXPERT": 0.15
    },
    "age_group": {
        "18-25": 0.25,
        "26-45": 0.50,
        "46-65": 0.20,
        "65+": 0.05
    },
    "device_type": {
        "DESKTOP": 0.60,
        "LAPTOP": 0.30,
        "TABLET": 0.10
    },
    "network_quality": {
        "FAST_BROADBAND": 0.70,
        "REGULAR_4G": 0.25,
        "SLOW_3G": 0.05
    },
    "patience": {
        "LOW": 0.25,
        "MEDIUM": 0.50,
        "HIGH": 0.25
    },
    "reading_behavior": {
        "SCANNER": 0.50,
        "SELECTIVE": 0.35,
        "THOROUGH": 0.15
    },
    "prior_familiarity": {
        "NONE": 0.50,
        "LOW": 0.30,
        "MEDIUM": 0.15,
        "HIGH": 0.05
    },
    "accessibility_needs": {
        "NONE": 0.85,
        "LOW_VISION": 0.08,
        "MOTOR_IMPAIRMENT": 0.07
    }
}

DEVICE_CONFIGS = {
    "DESKTOP": {
        "device_type": "DESKTOP",
        "viewport_width": 1920,
        "viewport_height": 1080,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    },
    "LAPTOP": {
        "device_type": "LAPTOP",
        "viewport_width": 1366,
        "viewport_height": 768,
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    },
    "TABLET": {
        "device_type": "TABLET",
        "viewport_width": 768,
        "viewport_height": 1024,
        "user_agent": "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
    }
}

NETWORK_CONFIGS = {
    "FAST_BROADBAND": {
        "network_type": "FAST_BROADBAND",
        "download_kbps": 50000,
        "latency_ms": 20
    },
    "REGULAR_4G": {
        "network_type": "REGULAR_4G",
        "download_kbps": 12000,
        "latency_ms": 80
    },
    "SLOW_3G": {
        "network_type": "SLOW_3G",
        "download_kbps": 750,
        "latency_ms": 300
    }
}

def sample_discrete(dist: Dict[str, float], rng: random.Random) -> str:
    """Deterministically samples a key from a discrete probability distribution."""
    keys = list(dist.keys())
    weights = [dist[k] for k in keys]
    total = sum(weights)
    if total <= 0:
        return keys[0]
    normalized_weights = [w / total for w in weights]
    return rng.choices(keys, weights=normalized_weights, k=1)[0]

class PopulationGenerator:
    """Generates deterministic, statistically representative populations of synthetic users."""

    @classmethod
    def generate_population(
        cls,
        experiment_id: str,
        population_size: int,
        custom_distributions: Optional[Dict[str, Dict[str, float]]] = None,
        random_seed: int = 42,
        initial_goal: str = "Explore application and achieve task"
    ) -> List[SyntheticUser]:
        rng = random.Random(random_seed)

        # Merge distributions
        dists = {}
        for k, default_v in DEFAULT_DISTRIBUTIONS.items():
            if custom_distributions and k in custom_distributions and custom_distributions[k]:
                dists[k] = custom_distributions[k]
            else:
                dists[k] = default_v

        users: List[SyntheticUser] = []

        for i in range(population_size):
            tech_prof = sample_discrete(dists["technical_proficiency"], rng)
            age = sample_discrete(dists["age_group"], rng)
            dev_type = sample_discrete(dists["device_type"], rng)
            net_type = sample_discrete(dists["network_quality"], rng)
            patience_cat = sample_discrete(dists["patience"], rng)
            reading_cat = sample_discrete(dists["reading_behavior"], rng)
            familiarity = sample_discrete(dists["prior_familiarity"], rng)
            access_need = sample_discrete(dists["accessibility_needs"], rng)

            # Map category to continuous numeric patience value
            if patience_cat == "LOW":
                patience_val = rng.uniform(0.1, 0.35)
            elif patience_cat == "MEDIUM":
                patience_val = rng.uniform(0.4, 0.65)
            else:
                patience_val = rng.uniform(0.7, 0.95)

            # Risk tolerance correlated with proficiency and age
            if tech_prof == "EXPERT":
                risk_tolerance = rng.uniform(0.6, 0.9)
                goal_orientation = rng.uniform(0.75, 0.98)
                error_tolerance = rng.uniform(0.3, 0.6)
            elif tech_prof == "BEGINNER":
                risk_tolerance = rng.uniform(0.15, 0.45)
                goal_orientation = rng.uniform(0.5, 0.8)
                error_tolerance = rng.uniform(0.5, 0.85)
            else: # INTERMEDIATE
                risk_tolerance = rng.uniform(0.4, 0.7)
                goal_orientation = rng.uniform(0.65, 0.85)
                error_tolerance = rng.uniform(0.4, 0.7)

            # Personality traits (Big 5 approximations)
            personality = {
                "conscientiousness": round(rng.uniform(0.2, 0.9), 2),
                "neuroticism": round(rng.uniform(0.1, 0.8), 2),
                "openness": round(rng.uniform(0.3, 0.9), 2),
                "persistence": round(patience_val, 2)
            }

            demographics = {
                "age_group": age,
                "education": rng.choice(["High School", "Bachelors", "Masters", "Doctorate"]),
                "native_language": "English",
                "accessibility_needs": access_need
            }

            device = DEVICE_CONFIGS.get(dev_type, DEVICE_CONFIGS["DESKTOP"]).copy()
            network = NETWORK_CONFIGS.get(net_type, NETWORK_CONFIGS["FAST_BROADBAND"]).copy()

            user = SyntheticUser(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{experiment_id}-s{random_seed}-user-{i+1}")),
                experiment_id=experiment_id,
                demographic_attributes=demographics,
                technical_proficiency=tech_prof,
                patience=round(patience_val, 3),
                risk_tolerance=round(risk_tolerance, 3),
                goal_orientation=round(goal_orientation, 3),
                reading_behavior=reading_cat,
                error_tolerance=round(error_tolerance, 3),
                familiarity_level=familiarity,
                device_profile=device,
                network_profile=network,
                personality_traits=personality,
                knowledge_state={
                    "visited_urls": [],
                    "discovered_elements": [],
                    "observed_concepts": []
                },
                memory_state={
                    "recent_actions": [],
                    "recent_failures": [],
                    "consecutive_failures": 0,
                    "url_visit_counts": {}
                },
                current_goal=initial_goal,
                current_subgoal="initial_page_scan",
                frustration_level=0.0,
                confidence_level=1.0,
                action_history=[],
                status="PENDING",
                steps_taken=0,
                duration_seconds=0.0,
                error_count=0
            )
            users.append(user)

        return users
