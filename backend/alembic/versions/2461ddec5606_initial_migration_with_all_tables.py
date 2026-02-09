"""Initial migration with all tables

Revision ID: 2461ddec5606
Revises:
Create Date: 2026-01-30 02:14:56.995562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2461ddec5606'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])

    # Create errors table
    op.create_table(
        'errors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('zeroeld_log_id', sa.String(255), nullable=True),
        sa.Column('zeroeld_event_id', sa.String(255), nullable=True),
        sa.Column('driver_id', sa.String(255), nullable=False),
        sa.Column('driver_name', sa.String(255), nullable=True),
        sa.Column('company_id', sa.String(255), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('error_key', sa.String(100), nullable=False),
        sa.Column('error_name', sa.String(255), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('error_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('discovered_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('fixed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_errors_zeroeld_log_id', 'errors', ['zeroeld_log_id'])
    op.create_index('ix_errors_zeroeld_event_id', 'errors', ['zeroeld_event_id'])
    op.create_index('ix_errors_driver_id', 'errors', ['driver_id'])
    op.create_index('ix_errors_company_id', 'errors', ['company_id'])
    op.create_index('ix_errors_error_key', 'errors', ['error_key'])
    op.create_index('ix_errors_status', 'errors', ['status'])
    op.create_index('ix_errors_discovered_at', 'errors', ['discovered_at'])

    # Create fixes table
    op.create_table(
        'fixes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('error_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('strategy_name', sa.String(100), nullable=False),
        sa.Column('fix_description', sa.Text(), nullable=True),
        sa.Column('api_calls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('result_message', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('screenshot_path', sa.String(500), nullable=True),
        sa.Column('retries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('approved_by', sa.String(255), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['error_id'], ['errors.id'], ondelete='CASCADE')
    )
    op.create_index('ix_fixes_error_id', 'fixes', ['error_id'])
    op.create_index('ix_fixes_status', 'fixes', ['status'])
    op.create_index('ix_fixes_created_at', 'fixes', ['created_at'])

    # Create agent_config table
    op.create_table(
        'agent_config',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('state', sa.String(20), nullable=False),
        sa.Column('polling_interval_seconds', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('max_concurrent_fixes', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('require_approval', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('dry_run_mode', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create fix_rules table
    op.create_table(
        'fix_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('error_key', sa.String(100), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('auto_fix', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('retry_delay_seconds', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('safety_checks', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('fix_strategy', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('error_key')
    )
    op.create_index('ix_fix_rules_error_key', 'fix_rules', ['error_key'])

    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', sa.String(255), nullable=True),
        sa.Column('user_id', sa.String(255), nullable=True),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_log_action_type', 'audit_log', ['action_type'])
    op.create_index('ix_audit_log_created_at', 'audit_log', ['created_at'])

    # Create active_connections table
    op.create_table(
        'active_connections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('connection_id', sa.String(255), nullable=False),
        sa.Column('client_type', sa.String(50), nullable=True),
        sa.Column('connected_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_ping', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('connection_id')
    )
    op.create_index('ix_active_connections_connection_id', 'active_connections', ['connection_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('active_connections')
    op.drop_table('audit_log')
    op.drop_table('fix_rules')
    op.drop_table('agent_config')
    op.drop_table('fixes')
    op.drop_table('errors')
    op.drop_table('users')
