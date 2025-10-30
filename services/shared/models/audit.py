"""Audit models for compliance and traceability tracking."""

from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime,
    ForeignKey, Index, Boolean
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, INET
from sqlalchemy.orm import relationship, validates

from database.base import BaseModel, TimestampMixin
from database.enums import AuditActionEnum


class AuditLog(BaseModel, TimestampMixin):
    """Comprehensive audit trail for FDA compliance and traceability."""
    
    __tablename__ = "audit_logs"
    
    # Core identification
    audit_id = Column(
        String(50),
        nullable=False,
        unique=True,
        comment="Unique audit log identifier"
    )
    correlation_id = Column(
        String(100),
        nullable=True,
        comment="Correlation ID for tracking related events"
    )
    trace_id = Column(
        String(100),
        nullable=True,
        comment="Distributed tracing ID"
    )
    
    # Action and operation details
    action = Column(
        AuditActionEnum,
        nullable=False,
        comment="Type of action performed"
    )
    resource_type = Column(
        String(50),
        nullable=False,
        comment="Type of resource affected (table, endpoint, etc.)"
    )
    resource_id = Column(
        String(100),
        nullable=True,
        comment="Identifier of the specific resource"
    )
    operation = Column(
        String(100),
        nullable=False,
        comment="Specific operation performed"
    )
    
    # User and session information
    user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who performed the action"
    )
    username = Column(
        String(100),
        nullable=True,
        comment="Username at the time of action"
    )
    user_role = Column(
        String(50),
        nullable=True,
        comment="User role at the time of action"
    )
    session_id = Column(
        String(100),
        nullable=True,
        comment="User session identifier"
    )
    
    # Request and context information
    request_id = Column(
        String(100),
        nullable=True,
        comment="HTTP request identifier"
    )
    endpoint = Column(
        String(200),
        nullable=True,
        comment="API endpoint that was called"
    )
    http_method = Column(
        String(10),
        nullable=True,
        comment="HTTP method (GET, POST, etc.)"
    )
    user_agent = Column(
        String(500),
        nullable=True,
        comment="User agent string from request"
    )
    
    # Network and security information
    ip_address = Column(
        INET,
        nullable=True,
        comment="IP address of the request"
    )
    client_ip = Column(
        INET,
        nullable=True,
        comment="Original client IP (if behind proxy)"
    )
    geo_location = Column(
        JSONB,
        nullable=True,
        comment="Geographic location data"
    )
    
    # Timing information
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When the action occurred"
    )
    duration_ms = Column(
        Integer,
        nullable=True,
        comment="Duration of the operation in milliseconds"
    )
    
    # Data changes (for data modification operations)
    before_data = Column(
        JSONB,
        nullable=True,
        comment="Data state before the change"
    )
    after_data = Column(
        JSONB,
        nullable=True,
        comment="Data state after the change"
    )
    changed_fields = Column(
        JSONB,
        nullable=True,
        comment="List of fields that were changed"
    )
    
    # Request and response data
    request_data = Column(
        JSONB,
        nullable=True,
        comment="Request payload (sanitized)"
    )
    response_data = Column(
        JSONB,
        nullable=True,
        comment="Response data (sanitized)"
    )
    response_status = Column(
        Integer,
        nullable=True,
        comment="HTTP response status code"
    )
    
    # Outcome and status
    success = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether the operation was successful"
    )
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if operation failed"
    )
    error_code = Column(
        String(50),
        nullable=True,
        comment="Error code for categorization"
    )
    
    # Business context
    business_context = Column(
        JSONB,
        nullable=True,
        comment="Business context and metadata"
    )
    compliance_context = Column(
        JSONB,
        nullable=True,
        comment="Compliance-specific context"
    )
    risk_level = Column(
        String(20),
        nullable=True,
        comment="Risk level of the operation (low, medium, high, critical)"
    )
    
    # Digital signature for tamper evidence
    signature = Column(
        String(1000),
        nullable=True,
        comment="Digital signature for tamper evidence"
    )
    signature_algorithm = Column(
        String(50),
        nullable=True,
        comment="Algorithm used for digital signature"
    )
    signature_key_id = Column(
        String(100),
        nullable=True,
        comment="Key identifier used for signing"
    )
    
    # Regulatory and compliance
    regulation_standard = Column(
        String(50),
        nullable=True,
        comment="Applicable regulation (21 CFR Part 11, etc.)"
    )
    compliance_level = Column(
        String(20),
        nullable=True,
        comment="Level of compliance validation"
    )
    retention_period_years = Column(
        Integer,
        nullable=True,
        comment="Required retention period in years"
    )
    
    # External system integration
    external_system = Column(
        String(50),
        nullable=True,
        comment="External system that initiated the action"
    )
    external_transaction_id = Column(
        String(100),
        nullable=True,
        comment="External system transaction ID"
    )
    external_reference = Column(
        String(200),
        nullable=True,
        comment="External system reference"
    )
    
    # Investigation and forensics
    investigation_notes = Column(
        Text,
        nullable=True,
        comment="Notes added during investigations"
    )
    flagged_for_review = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this log entry is flagged for review"
    )
    reviewed_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who reviewed this audit entry"
    )
    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this audit entry was reviewed"
    )
    
    # Archival and lifecycle
    archived = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this log entry is archived"
    )
    archived_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this log entry was archived"
    )
    purge_eligible_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this log entry becomes eligible for purging"
    )
    
    # Additional metadata
    additional_metadata = Column(
        JSONB,
        nullable=True,
        comment="Additional context and metadata"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_audit_logs_id", "audit_id"),
        Index("idx_audit_logs_timestamp", "timestamp"),
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_session", "session_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
        Index("idx_audit_logs_correlation", "correlation_id"),
        Index("idx_audit_logs_trace", "trace_id"),
        Index("idx_audit_logs_ip", "ip_address"),
        Index("idx_audit_logs_endpoint", "endpoint"),
        Index("idx_audit_logs_success", "success"),
        Index("idx_audit_logs_flagged", "flagged_for_review"),
        Index("idx_audit_logs_archived", "archived"),
        Index("idx_audit_logs_purge", "purge_eligible_at"),
        Index("idx_audit_logs_external", "external_system", "external_transaction_id"),
        Index("idx_audit_logs_business_context", "business_context", postgresql_using="gin"),
        Index("idx_audit_logs_compliance", "compliance_context", postgresql_using="gin"),
        # Composite indexes for common queries
        Index("idx_audit_logs_user_timestamp", "user_id", "timestamp"),
        Index("idx_audit_logs_resource_timestamp", "resource_type", "resource_id", "timestamp"),
        Index("idx_audit_logs_action_timestamp", "action", "timestamp"),
    )
    
    @validates('audit_id')
    def validate_audit_id(self, key, value):
        """Validate audit ID format."""
        if not value or len(value.strip()) < 5:
            raise ValueError("Audit ID must be at least 5 characters")
        return value.strip()
    
    @validates('resource_type')
    def validate_resource_type(self, key, value):
        """Validate resource type."""
        if not value or len(value.strip()) < 2:
            raise ValueError("Resource type must be at least 2 characters")
        return value.strip().lower()
    
    @validates('operation')
    def validate_operation(self, key, value):
        """Validate operation name."""
        if not value or len(value.strip()) < 2:
            raise ValueError("Operation must be at least 2 characters")
        return value.strip()
    
    @validates('http_method')
    def validate_http_method(self, key, value):
        """Validate HTTP method."""
        if value:
            valid_methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']
            value = value.upper()
            if value not in valid_methods:
                raise ValueError(f"Invalid HTTP method: {value}")
        return value
    
    @validates('response_status')
    def validate_response_status(self, key, value):
        """Validate HTTP response status code."""
        if value is not None and not (100 <= value <= 599):
            raise ValueError("Response status must be a valid HTTP status code")
        return value
    
    @validates('risk_level')
    def validate_risk_level(self, key, value):
        """Validate risk level."""
        if value:
            valid_levels = ['low', 'medium', 'high', 'critical']
            value = value.lower()
            if value not in valid_levels:
                raise ValueError(f"Invalid risk level: {value}")
        return value
    
    def __repr__(self):
        return f"<AuditLog(id='{self.audit_id}', action='{self.action}', resource='{self.resource_type}')>"
    
    @property
    def is_data_modification(self) -> bool:
        """Check if this audit log represents a data modification."""
        return self.action in [
            AuditActionEnum.CREATE,
            AuditActionEnum.UPDATE,
            AuditActionEnum.DELETE
        ]
    
    @property
    def is_security_event(self) -> bool:
        """Check if this is a security-related event."""
        security_actions = [AuditActionEnum.LOGIN, AuditActionEnum.LOGOUT]
        return (
            self.action in security_actions or
            self.risk_level in ['high', 'critical'] or
            not self.success
        )
    
    @property
    def is_high_risk(self) -> bool:
        """Check if this is a high-risk operation."""
        return self.risk_level in ['high', 'critical']
    
    @property
    def has_signature(self) -> bool:
        """Check if audit log has a digital signature."""
        return self.signature is not None and self.signature_algorithm is not None
    
    @property
    def is_flagged(self) -> bool:
        """Check if audit log is flagged for review."""
        return self.flagged_for_review
    
    @property
    def is_reviewed(self) -> bool:
        """Check if audit log has been reviewed."""
        return self.reviewed_by is not None and self.reviewed_at is not None
    
    @property
    def retention_expires_at(self) -> Optional[datetime]:
        """Calculate when retention period expires."""
        if self.retention_period_years and self.timestamp:
            from dateutil.relativedelta import relativedelta
            return self.timestamp + relativedelta(years=self.retention_period_years)
        return None
    
    def get_sanitized_data(self) -> Dict[str, Any]:
        """Get sanitized version of audit data for display."""
        sanitized = {
            "audit_id": self.audit_id,
            "timestamp": self.timestamp,
            "action": self.action.value if self.action else None,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "operation": self.operation,
            "username": self.username,
            "user_role": self.user_role,
            "endpoint": self.endpoint,
            "http_method": self.http_method,
            "response_status": self.response_status,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "ip_address": str(self.ip_address) if self.ip_address else None,
        }
        
        # Add error information if present
        if not self.success:
            sanitized.update({
                "error_message": self.error_message,
                "error_code": self.error_code,
            })
        
        # Add risk information if present
        if self.risk_level:
            sanitized["risk_level"] = self.risk_level
        
        return sanitized
    
    def flag_for_review(self, reason: str = None):
        """Flag this audit log for review."""
        self.flagged_for_review = True
        if reason and self.investigation_notes:
            self.investigation_notes += f"\n\nFlagged: {reason}"
        elif reason:
            self.investigation_notes = f"Flagged: {reason}"
    
    def mark_reviewed(self, reviewer_id: UUID, notes: str = None):
        """Mark this audit log as reviewed."""
        self.reviewed_by = reviewer_id
        self.reviewed_at = datetime.utcnow()
        self.flagged_for_review = False
        
        if notes:
            if self.investigation_notes:
                self.investigation_notes += f"\n\nReview: {notes}"
            else:
                self.investigation_notes = f"Review: {notes}"