"""SQLAlchemy ORM models for database tables."""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.session import Base


class User(Base):
    """User accounts for API authentication."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_superuser = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.username} ({self.email})>"


class Error(Base):
    """Error records discovered by the agent."""

    __tablename__ = "errors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zeroeld_log_id = Column(String(255), nullable=True, index=True)
    zeroeld_event_id = Column(String(255), nullable=True, index=True)
    driver_id = Column(String(255), nullable=False, index=True)
    driver_name = Column(String(255), nullable=True)
    company_id = Column(String(255), nullable=False, index=True)
    company_name = Column(String(255), nullable=True)
    error_key = Column(String(100), nullable=False, index=True)
    error_name = Column(String(255), nullable=False)
    error_message = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False, default="medium")
    category = Column(String(50), nullable=True)  # Error category (data_integrity, location_movement, etc.)
    status = Column(String(20), nullable=False, default="pending", index=True)
    error_metadata = Column(JSON, nullable=True)
    discovered_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    fixed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    fixes = relationship("Fix", back_populates="error", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Error {self.id} - {self.error_key}: {self.status}>"


class Fix(Base):
    """Fix attempts and results for errors."""

    __tablename__ = "fixes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    error_id = Column(UUID(as_uuid=True), ForeignKey("errors.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy_name = Column(String(100), nullable=False)
    fix_description = Column(Text, nullable=True)
    api_calls = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, index=True)
    result_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    screenshot_path = Column(String(500), nullable=True)  # Path to screenshot if fix fails
    retries = Column(Integer, nullable=False, default=0)
    requires_approval = Column(Boolean, nullable=False, default=True)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    error = relationship("Error", back_populates="fixes")

    def __repr__(self):
        return f"<Fix {self.id} - {self.strategy_name}: {self.status}>"


class AgentConfig(Base):
    """Agent configuration and state."""

    __tablename__ = "agent_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(String(20), nullable=False)  # stopped, starting, running, paused, stopping
    polling_interval_seconds = Column(Integer, nullable=False, default=300)
    max_concurrent_fixes = Column(Integer, nullable=False, default=1)
    require_approval = Column(Boolean, nullable=False, default=True)
    dry_run_mode = Column(Boolean, nullable=False, default=True)
    last_run_at = Column(DateTime, nullable=True)  # Timestamp of last agent run
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AgentConfig id={self.id} state={self.state}>"


class FixRule(Base):
    """Fix rules and configuration for error types."""

    __tablename__ = "fix_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    error_key = Column(String(100), nullable=False, unique=True, index=True)
    enabled = Column(Boolean, nullable=False, default=True)
    auto_fix = Column(Boolean, nullable=False, default=False)
    priority = Column(Integer, nullable=False, default=50)  # 0-100, higher = more urgent
    max_retries = Column(Integer, nullable=False, default=3)
    retry_delay_seconds = Column(Integer, nullable=False, default=300)
    safety_checks = Column(JSON, nullable=True)
    fix_strategy = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<FixRule {self.error_key} enabled={self.enabled} auto_fix={self.auto_fix}>"


class AuditLog(Base):
    """Audit log for all agent actions."""

    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_type = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(255), nullable=True)
    user_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<AuditLog {self.id} - {self.action_type}>"


class ActiveConnection(Base):
    """Track active WebSocket connections."""

    __tablename__ = "active_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(String(255), unique=True, nullable=False, index=True)
    client_type = Column(String(50), nullable=True)
    connected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_ping = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<ActiveConnection {self.connection_id} - {self.client_type}>"
