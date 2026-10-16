"""Initial schema for synthetic humans

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-08 22:30:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'experiments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_url', sa.String(length=1024), nullable=False),
        sa.Column('population_size', sa.Integer(), nullable=False),
        sa.Column('task_definition', sa.JSON(), nullable=False),
        sa.Column('population_distributions', sa.JSON(), nullable=True),
        sa.Column('max_steps_per_user', sa.Integer(), nullable=False),
        sa.Column('max_duration_seconds', sa.Integer(), nullable=False),
        sa.Column('concurrency', sa.Integer(), nullable=False),
        sa.Column('random_seed', sa.Integer(), nullable=False),
        sa.Column('model_configuration', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('is_authorized', sa.Boolean(), nullable=False),
        sa.Column('allowed_origins', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'synthetic_users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('experiment_id', sa.String(length=36), nullable=False),
        sa.Column('demographic_attributes', sa.JSON(), nullable=False),
        sa.Column('technical_proficiency', sa.String(length=32), nullable=False),
        sa.Column('patience', sa.Float(), nullable=False),
        sa.Column('risk_tolerance', sa.Float(), nullable=False),
        sa.Column('goal_orientation', sa.Float(), nullable=False),
        sa.Column('reading_behavior', sa.String(length=32), nullable=False),
        sa.Column('error_tolerance', sa.Float(), nullable=False),
        sa.Column('familiarity_level', sa.String(length=32), nullable=False),
        sa.Column('device_profile', sa.JSON(), nullable=False),
        sa.Column('network_profile', sa.JSON(), nullable=False),
        sa.Column('personality_traits', sa.JSON(), nullable=False),
        sa.Column('knowledge_state', sa.JSON(), nullable=False),
        sa.Column('memory_state', sa.JSON(), nullable=False),
        sa.Column('current_goal', sa.Text(), nullable=False),
        sa.Column('current_subgoal', sa.Text(), nullable=False),
        sa.Column('frustration_level', sa.Float(), nullable=False),
        sa.Column('confidence_level', sa.Float(), nullable=False),
        sa.Column('action_history', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('steps_taken', sa.Integer(), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=False),
        sa.Column('error_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'trajectories',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('synthetic_user_id', sa.String(length=36), nullable=False),
        sa.Column('experiment_id', sa.String(length=36), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('url', sa.String(length=1024), nullable=False),
        sa.Column('page_title', sa.String(length=512), nullable=False),
        sa.Column('visible_text_summary', sa.Text(), nullable=False),
        sa.Column('interactive_elements_count', sa.Integer(), nullable=False),
        sa.Column('screenshot_path', sa.String(length=1024), nullable=True),
        sa.Column('action_type', sa.String(length=32), nullable=False),
        sa.Column('action_target', sa.String(length=512), nullable=False),
        sa.Column('action_parameters', sa.JSON(), nullable=False),
        sa.Column('action_reason', sa.Text(), nullable=False),
        sa.Column('action_confidence', sa.Float(), nullable=False),
        sa.Column('action_result', sa.String(length=32), nullable=False),
        sa.Column('resulting_url', sa.String(length=1024), nullable=False),
        sa.Column('resulting_page_state', sa.JSON(), nullable=False),
        sa.Column('frustration_after', sa.Float(), nullable=False),
        sa.Column('confidence_after', sa.Float(), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['synthetic_user_id'], ['synthetic_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'experiment_metrics',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('experiment_id', sa.String(length=36), nullable=False),
        sa.Column('task_completion_rate', sa.Float(), nullable=False),
        sa.Column('task_abandonment_rate', sa.Float(), nullable=False),
        sa.Column('average_task_duration', sa.Float(), nullable=False),
        sa.Column('median_task_duration', sa.Float(), nullable=False),
        sa.Column('p95_task_duration', sa.Float(), nullable=False),
        sa.Column('average_actions', sa.Float(), nullable=False),
        sa.Column('average_errors', sa.Float(), nullable=False),
        sa.Column('retry_rate', sa.Float(), nullable=False),
        sa.Column('back_navigation_rate', sa.Float(), nullable=False),
        sa.Column('dead_end_rate', sa.Float(), nullable=False),
        sa.Column('confusion_rate', sa.Float(), nullable=False),
        sa.Column('time_to_first_successful_action', sa.Float(), nullable=False),
        sa.Column('segment_metrics', sa.JSON(), nullable=False),
        sa.Column('funnel_steps', sa.JSON(), nullable=False),
        sa.Column('heatmap_data', sa.JSON(), nullable=False),
        sa.Column('action_distribution', sa.JSON(), nullable=False),
        sa.Column('total_llm_calls', sa.Integer(), nullable=False),
        sa.Column('estimated_tokens_used', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('experiment_id')
    )

    op.create_table(
        'friction_findings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('experiment_id', sa.String(length=36), nullable=False),
        sa.Column('severity', sa.String(length=16), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence', sa.JSON(), nullable=False),
        sa.Column('recommendation', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'experiment_comparisons',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('baseline_experiment_id', sa.String(length=36), nullable=False),
        sa.Column('variant_experiment_id', sa.String(length=36), nullable=False),
        sa.Column('completion_rate_delta', sa.Float(), nullable=False),
        sa.Column('duration_delta', sa.Float(), nullable=False),
        sa.Column('error_delta', sa.Float(), nullable=False),
        sa.Column('abandonment_delta', sa.Float(), nullable=False),
        sa.Column('segment_deltas', sa.JSON(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['baseline_experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('experiment_comparisons')
    op.drop_table('friction_findings')
    op.drop_table('experiment_metrics')
    op.drop_table('trajectories')
    op.drop_table('synthetic_users')
    op.drop_table('experiments')
