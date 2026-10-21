export interface TaskDefinition {
  goal: string;
  success_conditions: Array<{ type: string; value: string; description?: string }>;
  optional_conditions?: any[];
  failure_conditions?: any[];
}

export interface Experiment {
  id: string;
  name: string;
  description?: string | null;
  target_url: string;
  population_size: number;
  task_definition: TaskDefinition;
  population_distributions?: Record<string, Record<string, number>> | null;
  max_steps_per_user: number;
  max_duration_seconds: number;
  concurrency: number;
  random_seed: number;
  model_configuration: Record<string, any>;
  status: 'CREATED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  is_authorized: boolean;
  allowed_origins: string[];
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  completed_users_count?: number;
  abandoned_users_count?: number;
  failed_users_count?: number;
}

export interface SyntheticUser {
  id: string;
  experiment_id: string;
  demographic_attributes: Record<string, any>;
  technical_proficiency: 'BEGINNER' | 'INTERMEDIATE' | 'EXPERT';
  patience: number;
  risk_tolerance: number;
  goal_orientation: number;
  reading_behavior: string;
  error_tolerance: number;
  familiarity_level: string;
  device_profile: Record<string, any>;
  network_profile: Record<string, any>;
  personality_traits: Record<string, any>;
  knowledge_state: Record<string, any>;
  memory_state: Record<string, any>;
  current_goal: string;
  current_subgoal: string;
  frustration_level: number;
  confidence_level: number;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'ABANDONED' | 'FAILED' | 'TIMEOUT';
  steps_taken: number;
  duration_seconds: number;
  error_count: number;
  created_at: string;
  completed_at?: string | null;
  trajectories?: TrajectoryStep[];
}

export interface TrajectoryStep {
  id: string;
  synthetic_user_id: string;
  experiment_id: string;
  step_number: number;
  timestamp: string;
  url: string;
  page_title: string;
  visible_text_summary: string;
  interactive_elements_count: number;
  screenshot_path?: string | null;
  action_type: string;
  action_target: string;
  action_parameters: Record<string, any>;
  action_reason: string;
  action_confidence: number;
  action_result: string;
  resulting_url: string;
  resulting_page_state: Record<string, any>;
  frustration_after: number;
  confidence_after: number;
  latency_ms: number;
  error_message?: string | null;
}

export interface FunnelStep {
  stage: string;
  users_reached: number;
  conversion_rate: number;
  drop_off_rate: number;
}

export interface HeatmapItem {
  url: string;
  selector: string;
  total_interactions: number;
  errors: number;
  abandonments: number;
  friction_score: number;
}

export interface ExperimentMetrics {
  id: string;
  experiment_id: string;
  task_completion_rate: number;
  task_abandonment_rate: number;
  average_task_duration: number;
  median_task_duration: number;
  p95_task_duration: number;
  average_actions: number;
  average_errors: number;
  retry_rate: number;
  back_navigation_rate: number;
  dead_end_rate: number;
  confusion_rate: number;
  time_to_first_successful_action: number;
  segment_metrics: Record<string, any>;
  funnel_steps: FunnelStep[];
  heatmap_data: HeatmapItem[];
  action_distribution: Record<string, number>;
  total_llm_calls: number;
  estimated_tokens_used: number;
}

export interface FrictionFinding {
  id: string;
  experiment_id: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  category: string;
  title: string;
  description: string;
  evidence: Record<string, any>;
  recommendation: string;
  created_at: string;
}

export interface ExperimentComparison {
  id: string;
  baseline_experiment_id: string;
  variant_experiment_id: string;
  completion_rate_delta: number;
  duration_delta: number;
  error_delta: number;
  abandonment_delta: number;
  segment_deltas: Record<string, any>;
  summary: string;
  created_at: string;
}

export interface ExperimentDetailResponse {
  experiment: Experiment;
  metrics?: ExperimentMetrics | null;
  findings: FrictionFinding[];
}
