import asyncio
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from playwright.async_api import BrowserContext, Page

from backend.app.models.synthetic_user import SyntheticUser
from backend.app.models.trajectory import TrajectoryStep
from backend.app.models.experiment import Experiment
from backend.app.simulation.state import PersistentUserState
from backend.app.simulation.persona import PersonaProfile
from backend.app.simulation.planner import HierarchicalTaskPlanner
from backend.app.simulation.evaluator import TaskEvaluator
from backend.app.simulation.decision import BaseLLMProvider, get_llm_provider
from backend.app.simulation.memory import UserCognitiveMemory
from backend.app.browser.actions import ActionExecutor
from backend.app.browser.observation import ObservationExtractor
from backend.app.browser.playwright_runner import browser_manager, SafetyBoundaryViolation
from backend.app.simulation.events import event_bus

logger = logging.getLogger(__name__)

# Dangerous keywords blocked by safety boundaries
RESTRICTED_KEYWORDS = [
    "credit_card", "cvv", "delete_account", "change_password", "passwd",
    "export_credentials", "terminal", "exec", "eval"
]

class SingleUserSimulationRunner:
    """
    Executes the persistent observation-decision-action-verification loop for an individual synthetic user.
    """

    def __init__(
        self,
        user: SyntheticUser,
        experiment: Experiment,
        llm_provider: BaseLLMProvider
    ):
        self.user = user
        self.experiment = experiment
        self.provider = llm_provider
        self.allowed_origins = experiment.allowed_origins or [browser_manager.get_origin(experiment.target_url)]

        # Initialize persona profile
        self.persona = PersonaProfile(
            technical_proficiency=user.technical_proficiency,
            patience=user.patience,
            risk_tolerance=user.risk_tolerance,
            goal_orientation=user.goal_orientation,
            reading_behavior=user.reading_behavior,
            error_tolerance=user.error_tolerance,
            familiarity_level=user.familiarity_level
        )

        # Initialize persistent cognitive state
        self.user_state = PersistentUserState(
            user_id=user.id,
            technical_proficiency=user.technical_proficiency,
            patience=user.patience,
            risk_tolerance=user.risk_tolerance,
            reading_behavior=user.reading_behavior,
            initial_goal=user.current_goal or experiment.task_definition.get("goal", ""),
            knowledge_state=dict(user.knowledge_state or {}),
            memory_state=dict(user.memory_state or {}),
            frustration_level=user.frustration_level,
            confidence_level=user.confidence_level
        )

        self.cognitive_memory = UserCognitiveMemory()

    def _validate_safety(self, action_type: str, target: str, params: Dict[str, Any]):
        """Blocks prohibited actions violating usability testing safety boundaries."""
        target_lower = target.lower()
        param_str = str(params).lower()

        for kw in RESTRICTED_KEYWORDS:
            if kw in target_lower or kw in param_str:
                raise SafetyBoundaryViolation(f"Blocked hazardous action containing restricted keyword: '{kw}'")

    async def run(self) -> List[TrajectoryStep]:
        trajectories: List[TrajectoryStep] = []
        context: Optional[BrowserContext] = None
        page: Optional[Page] = None
        start_time = time.perf_counter()

        max_steps = self.experiment.max_steps_per_user
        max_duration = self.experiment.max_duration_seconds

        try:
            # 1. Check target URL safety
            if not browser_manager.is_origin_allowed(self.experiment.target_url, self.allowed_origins):
                raise SafetyBoundaryViolation(f"Target URL '{self.experiment.target_url}' is not in allowed origins {self.allowed_origins}")

            # 2. Launch isolated user context
            context = await browser_manager.create_user_context(
                device_profile=self.user.device_profile,
                network_profile=self.user.network_profile,
                allowed_origins=self.allowed_origins
            )
            page = await context.new_page()

            # Set navigation timeout
            page.set_default_navigation_timeout(10000)
            page.set_default_timeout(5000)

            # 3. Initial navigation
            await page.goto(self.experiment.target_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(self.persona.scan_delay_ms)

            # Broadcast agent start
            await event_bus.publish(self.experiment.id, {
                "type": "agent_start",
                "user_id": self.user.id,
                "proficiency": self.user.technical_proficiency,
                "goal": self.user.current_goal or self.experiment.task_definition.get("goal", "")
            })

            step_number = 1
            terminal_status = None

            # 4. Simulation Loop
            while step_number <= max_steps:
                elapsed_seconds = time.perf_counter() - start_time
                if elapsed_seconds >= max_duration:
                    terminal_status = "TIMEOUT"
                    break

                # STAGE 1: OBSERVE
                obs_step_start = time.perf_counter()
                observation = await ObservationExtractor.capture_observation(
                    page=page,
                    user_id=self.user.id,
                    step_number=step_number,
                    take_screenshot=True
                )

                # Security check on current URL
                if not browser_manager.is_origin_allowed(page.url, self.allowed_origins):
                    raise SafetyBoundaryViolation(f"Page navigated outside allowed origins: {page.url}")

                # STAGE 2: UPDATE STATE
                self.user_state.record_page_visit(observation["url"], observation["page_title"])

                # Check task completion status before action
                eval_status = TaskEvaluator.evaluate_task_status(
                    task_definition=self.experiment.task_definition,
                    observation=observation,
                    steps_taken=step_number - 1,
                    max_steps=max_steps,
                    duration_seconds=elapsed_seconds,
                    max_duration_seconds=max_duration,
                    user_abandoned=False
                )
                if eval_status == "SUCCESS":
                    terminal_status = "COMPLETED"
                    break

                # STAGE 3: FORMULATE INTENT (Subgoal)
                self.user_state.current_subgoal = HierarchicalTaskPlanner.update_subgoal(
                    current_goal=self.user_state.current_goal,
                    url=observation["url"],
                    title=observation["page_title"],
                    observation=observation
                )

                # STAGE 4: SELECT ACTION
                decision = await self.provider.generate_decision(
                    observation=observation,
                    user_state=self.user_state,
                    persona=self.persona,
                    task_definition=self.experiment.task_definition
                )

                action_type = decision.get("action_type", "WAIT")
                target = decision.get("target", "")
                parameters = decision.get("parameters", {})
                reason = decision.get("reason", "")
                confidence = decision.get("confidence", 0.5)

                # Check for abandonment
                if action_type == "ABANDON":
                    terminal_status = "ABANDONED"
                    trajectory = TrajectoryStep(
                        synthetic_user_id=self.user.id,
                        experiment_id=self.experiment.id,
                        step_number=step_number,
                        url=observation["url"],
                        page_title=observation["page_title"],
                        visible_text_summary=observation["visible_text_summary"][:1000],
                        interactive_elements_count=observation["interactive_elements_count"],
                        screenshot_path=observation["screenshot_path"],
                        action_type="ABANDON",
                        action_target=target,
                        action_parameters=parameters,
                        action_reason=reason,
                        action_confidence=confidence,
                        action_result="SUCCESS",
                        resulting_url=page.url,
                        resulting_page_state={"status": "user_abandoned"},
                        frustration_after=round(self.user_state.frustration_level, 3),
                        confidence_after=round(self.user_state.confidence_level, 3),
                        latency_ms=10.0,
                        error_message=None
                    )
                    trajectories.append(trajectory)
                    await event_bus.publish(self.experiment.id, {
                        "type": "step",
                        "user_id": self.user.id,
                        "step_number": step_number,
                        "url": observation["url"],
                        "page_title": observation["page_title"],
                        "action_type": "ABANDON",
                        "action_target": target,
                        "action_reason": reason,
                        "action_confidence": confidence,
                        "action_result": "SUCCESS",
                        "frustration": round(self.user_state.frustration_level, 3),
                        "confidence": round(self.user_state.confidence_level, 3),
                        "subgoal": self.user_state.current_subgoal,
                        "latency_ms": 10.0,
                        "error_message": None,
                        "screenshot_path": observation.get("screenshot_path")
                    })
                    break

                # Safety boundary check
                self._validate_safety(action_type, target, parameters)

                # STAGE 5: EXECUTE ACTION
                action_result = await ActionExecutor.execute_action(
                    page=page,
                    action_type=action_type,
                    target=target,
                    parameters=parameters
                )

                # STAGE 6: VERIFY RESULT
                post_url = page.url
                res_status = action_result["result"]
                error_msg = action_result.get("error")

                # Detect application-level form error or validation rejection
                if res_status == "SUCCESS":
                    if "error=" in post_url.lower() or "validation_failed" in post_url.lower():
                        res_status = "FAILED"
                        error_msg = "Form submission rejected by application validation check"

                # STAGE 7: UPDATE MEMORY & STATE
                self.user_state.register_action_result(
                    action_type=action_type,
                    target=target,
                    result=res_status,
                    resulting_url=post_url,
                    error_message=error_msg
                )

                if res_status != "SUCCESS":
                    self.cognitive_memory.record_failure(target, error_msg or "Failed")
                else:
                    self.cognitive_memory.record_attempt(target, action_type)

                # Post-action observation for trajectory
                post_obs = await ObservationExtractor.capture_observation(
                    page=page,
                    user_id=self.user.id,
                    step_number=step_number,
                    take_screenshot=False
                )

                trajectory = TrajectoryStep(
                    synthetic_user_id=self.user.id,
                    experiment_id=self.experiment.id,
                    step_number=step_number,
                    url=observation["url"],
                    page_title=observation["page_title"],
                    visible_text_summary=observation["visible_text_summary"][:1000],
                    interactive_elements_count=observation["interactive_elements_count"],
                    screenshot_path=observation["screenshot_path"],
                    action_type=action_type,
                    action_target=target,
                    action_parameters=parameters,
                    action_reason=reason,
                    action_confidence=confidence,
                    action_result=res_status,
                    resulting_url=post_url,
                    resulting_page_state={"interactive_count": post_obs["interactive_elements_count"]},
                    frustration_after=round(self.user_state.frustration_level, 3),
                    confidence_after=round(self.user_state.confidence_level, 3),
                    latency_ms=action_result["latency_ms"],
                    error_message=error_msg
                )
                trajectories.append(trajectory)
                await event_bus.publish(self.experiment.id, {
                    "type": "step",
                    "user_id": self.user.id,
                    "step_number": step_number,
                    "url": observation["url"],
                    "page_title": observation["page_title"],
                    "action_type": action_type,
                    "action_target": target,
                    "action_reason": reason,
                    "action_confidence": confidence,
                    "action_result": res_status,
                    "frustration": round(self.user_state.frustration_level, 3),
                    "confidence": round(self.user_state.confidence_level, 3),
                    "subgoal": self.user_state.current_subgoal,
                    "latency_ms": action_result.get("latency_ms", 0.0),
                    "error_message": error_msg,
                    "screenshot_path": observation.get("screenshot_path")
                })

                # Check if user reached goal
                eval_post = TaskEvaluator.evaluate_task_status(
                    task_definition=self.experiment.task_definition,
                    observation=post_obs,
                    steps_taken=step_number,
                    max_steps=max_steps,
                    duration_seconds=time.perf_counter() - start_time,
                    max_duration_seconds=max_duration,
                    user_abandoned=False
                )
                if eval_post == "SUCCESS":
                    terminal_status = "COMPLETED"
                    break

                step_number += 1
                # Trait reading delay
                await page.wait_for_timeout(self.persona.scan_delay_ms)

            # Final status update
            total_duration = round(time.perf_counter() - start_time, 2)
            if not terminal_status:
                if step_number > max_steps:
                    terminal_status = "TIMEOUT"
                else:
                    terminal_status = "ABANDONED"
            self.user.status = terminal_status
            self.user.steps_taken = len(trajectories)
            self.user.duration_seconds = total_duration
            self.user.error_count = sum(1 for t in trajectories if t.action_result != "SUCCESS")
            self.user.frustration_level = round(self.user_state.frustration_level, 3)
            self.user.confidence_level = round(self.user_state.confidence_level, 3)
            self.user.completed_at = datetime.now(timezone.utc)
            self.user.knowledge_state = self.user_state.knowledge_state
            self.user.memory_state = self.user_state.memory_state

            await event_bus.publish(self.experiment.id, {
                "type": "agent_finish",
                "user_id": self.user.id,
                "status": self.user.status,
                "steps_taken": self.user.steps_taken,
                "duration_seconds": self.user.duration_seconds,
                "frustration": self.user.frustration_level,
                "error_count": self.user.error_count
            })

        except SafetyBoundaryViolation as sbv:
            logger.warning(f"User {self.user.id} violated safety boundary: {sbv}")
            self.user.status = "FAILED"
            self.user.duration_seconds = round(time.perf_counter() - start_time, 2)
            self.user.completed_at = datetime.now(timezone.utc)
            # Create safety violation step
            trajectories.append(TrajectoryStep(
                synthetic_user_id=self.user.id,
                experiment_id=self.experiment.id,
                step_number=len(trajectories) + 1,
                url=page.url if page else self.experiment.target_url,
                page_title="Safety Boundary Intervention",
                visible_text_summary="Action blocked by security policy",
                interactive_elements_count=0,
                screenshot_path=None,
                action_type="ABANDON",
                action_target="security_boundary",
                action_parameters={},
                action_reason=str(sbv),
                action_confidence=1.0,
                action_result="FAILED",
                resulting_url=page.url if page else self.experiment.target_url,
                resulting_page_state={"error": "safety_boundary_violation"},
                frustration_after=1.0,
                confidence_after=0.0,
                latency_ms=0.0,
                error_message=str(sbv)
            ))

        except Exception as e:
            logger.error(f"Error during simulation of user {self.user.id}: {str(e)}", exc_info=True)
            self.user.status = "FAILED"
            self.user.duration_seconds = round(time.perf_counter() - start_time, 2)
            self.user.completed_at = datetime.now(timezone.utc)

        finally:
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
            if context:
                try:
                    await context.close()
                except Exception:
                    pass

        return trajectories
