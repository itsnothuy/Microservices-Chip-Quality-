"""
User and authentication database models.

Implements comprehensive user management with security features,
role assignments, and FDA 21 CFR Part 11 compliance.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, ForeignKey,
    Text, JSON, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, INET
from sqlalchemy.orm import relationship

from services.shared.database.base import BaseModel, TimestampMixin


class User(BaseModel, TimestampMixin):
    """
    User model with comprehensive security and compliance features.
    
    Supports:
    - Password-based authentication with bcrypt hashing
    - Email verification workflow
    - Account status management (active, locked, disabled)
    - MFA secret storage
    - Last login tracking
    - Failed login attempt tracking
    - Password history for compliance
    """
    
    __tablename__ = "users"
    
    # Authentication credentials
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique username for login"
    )
    
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address"
    )
    
    password_hash = Column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password"
    )
    
    # User profile
    full_name = Column(
        String(200),
        nullable=True,
        comment="User's full name"
    )
    
    department = Column(
        String(100),
        nullable=True,
        index=True,
        comment="User's department"
    )
    
    employee_id = Column(
        String(50),
        nullable=True,
        index=True,
        comment="Employee/operator ID"
    )
    
    # Account status
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether user account is active"
    )
    
    is_verified = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether email is verified"
    )
    
    is_locked = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether account is locked"
    )
    
    locked_until = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Account lockout expiration time"
    )
    
    # Security tracking
    failed_login_attempts = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of consecutive failed login attempts"
    )
    
    last_failed_login = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last failed login"
    )
    
    last_login = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Timestamp of last successful login"
    )
    
    last_password_change = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last password change"
    )
    
    # MFA settings
    mfa_enabled = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether MFA is enabled"
    )
    
    mfa_secret = Column(
        String(100),
        nullable=True,
        comment="TOTP secret for MFA (encrypted)"
    )
    
    mfa_backup_codes = Column(
        JSON,
        nullable=True,
        comment="Encrypted backup codes for MFA recovery"
    )
    
    # Verification tokens
    email_verification_token = Column(
        String(100),
        nullable=True,
        comment="Token for email verification"
    )
    
    email_verification_expires = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Email verification token expiration"
    )
    
    password_reset_token = Column(
        String(100),
        nullable=True,
        comment="Token for password reset"
    )
    
    password_reset_expires = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Password reset token expiration"
    )
    
    # Metadata
    metadata_json = Column(
        JSON,
        nullable=True,
        default={},
        comment="Additional user metadata"
    )
    
    # Relationships
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    password_history = relationship("PasswordHistory", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_users_username_lower", "username"),
        Index("idx_users_email_lower", "email"),
        Index("idx_users_active_status", "is_active", "is_locked"),
    )


class Role(BaseModel, TimestampMixin):
    """
    Role definition for RBAC system.
    
    Defines hierarchical roles with associated permissions for
    manufacturing quality control operations.
    """
    
    __tablename__ = "roles"
    
    name = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique role identifier"
    )
    
    display_name = Column(
        String(100),
        nullable=False,
        comment="Human-readable role name"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Role description"
    )
    
    permissions = Column(
        JSON,
        nullable=False,
        default=[],
        comment="List of permission scope strings"
    )
    
    requires_mfa = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether role requires MFA"
    )
    
    max_session_hours = Column(
        Integer,
        nullable=False,
        default=8,
        comment="Maximum session duration in hours"
    )
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="role")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("max_session_hours > 0", name="check_positive_session_hours"),
    )


class UserRole(BaseModel, TimestampMixin):
    """
    Many-to-many relationship between users and roles.
    
    Tracks role assignments with audit information.
    """
    
    __tablename__ = "user_roles"
    
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID"
    )
    
    role_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Role ID"
    )
    
    assigned_by = Column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="User ID who assigned this role"
    )
    
    assigned_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When role was assigned"
    )
    
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Optional role assignment expiration"
    )
    
    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="user_roles")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
        Index("idx_user_roles_user_id", "user_id"),
        Index("idx_user_roles_role_id", "role_id"),
    )


class UserSession(BaseModel, TimestampMixin):
    """
    Active user session tracking.
    
    Maintains session state for security monitoring and concurrent
    session limits. Supports FDA audit trail requirements.
    """
    
    __tablename__ = "user_sessions"
    
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID"
    )
    
    session_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique session identifier"
    )
    
    jti = Column(
        String(100),
        nullable=False,
        index=True,
        comment="JWT ID for token tracking"
    )
    
    client_ip = Column(
        INET,
        nullable=False,
        comment="Client IP address"
    )
    
    user_agent = Column(
        Text,
        nullable=True,
        comment="Client user agent string"
    )
    
    device_fingerprint = Column(
        String(100),
        nullable=True,
        comment="Device fingerprint for additional security"
    )
    
    last_activity = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="Last activity timestamp"
    )
    
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Session expiration time"
    )
    
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether session is active"
    )
    
    revoked_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When session was revoked"
    )
    
    revoked_reason = Column(
        String(200),
        nullable=True,
        comment="Reason for session revocation"
    )
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index("idx_sessions_user_active", "user_id", "is_active"),
        Index("idx_sessions_expires", "expires_at"),
        Index("idx_sessions_jti", "jti"),
    )


class AuthEvent(BaseModel, TimestampMixin):
    """
    Authentication and authorization event log.
    
    Comprehensive audit trail for FDA 21 CFR Part 11 compliance.
    Records all authentication attempts, authorization decisions,
    and security events.
    """
    
    __tablename__ = "auth_events"
    
    event_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Event type (login, logout, permission_check, etc.)"
    )
    
    user_id = Column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="User ID (null for failed login attempts)"
    )
    
    username = Column(
        String(50),
        nullable=True,
        index=True,
        comment="Username used in attempt"
    )
    
    session_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Session identifier"
    )
    
    client_ip = Column(
        INET,
        nullable=False,
        index=True,
        comment="Client IP address"
    )
    
    user_agent = Column(
        Text,
        nullable=True,
        comment="Client user agent"
    )
    
    success = Column(
        Boolean,
        nullable=False,
        index=True,
        comment="Whether event was successful"
    )
    
    failure_reason = Column(
        String(200),
        nullable=True,
        comment="Reason for failure"
    )
    
    resource = Column(
        String(100),
        nullable=True,
        comment="Resource being accessed"
    )
    
    action = Column(
        String(50),
        nullable=True,
        comment="Action being performed"
    )
    
    metadata_json = Column(
        JSON,
        nullable=True,
        default={},
        comment="Additional event metadata"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_auth_events_type_time", "event_type", "created_at"),
        Index("idx_auth_events_user_time", "user_id", "created_at"),
        Index("idx_auth_events_ip_time", "client_ip", "created_at"),
        Index("idx_auth_events_success", "success", "created_at"),
    )


class PasswordHistory(BaseModel, TimestampMixin):
    """
    Password history for compliance.
    
    Stores hashed passwords to prevent reuse of recent passwords,
    meeting FDA and other compliance requirements.
    """
    
    __tablename__ = "password_history"
    
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User ID"
    )
    
    password_hash = Column(
        String(255),
        nullable=False,
        comment="Historical password hash"
    )
    
    changed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="When password was changed"
    )
    
    changed_by = Column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="User ID who changed password (for admin resets)"
    )
    
    # Relationships
    user = relationship("User", back_populates="password_history")
    
    # Indexes
    __table_args__ = (
        Index("idx_password_history_user_time", "user_id", "changed_at"),
    )


class ElectronicSignature(BaseModel, TimestampMixin):
    """
    Electronic signature records for FDA 21 CFR Part 11 compliance.
    
    Captures digital signatures for critical quality operations
    with complete audit trail and non-repudiation.
    """
    
    __tablename__ = "electronic_signatures"
    
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="User who signed"
    )
    
    resource_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of resource signed (inspection, report, etc.)"
    )
    
    resource_id = Column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="ID of signed resource"
    )
    
    action = Column(
        String(50),
        nullable=False,
        comment="Action being signed (approve, reject, override)"
    )
    
    signature_meaning = Column(
        Text,
        nullable=False,
        comment="Meaning of the signature"
    )
    
    reason = Column(
        Text,
        nullable=True,
        comment="Reason for signing"
    )
    
    signed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="Timestamp of signature"
    )
    
    signature_hash = Column(
        String(100),
        nullable=False,
        comment="Cryptographic hash of signature data"
    )
    
    client_ip = Column(
        INET,
        nullable=False,
        comment="IP address where signature was created"
    )
    
    metadata_json = Column(
        JSON,
        nullable=True,
        default={},
        comment="Additional signature metadata"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_esig_resource", "resource_type", "resource_id"),
        Index("idx_esig_user_time", "user_id", "signed_at"),
    )
