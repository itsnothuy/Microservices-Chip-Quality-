"""
SQLAlchemy database models for the semiconductor manufacturing platform.

This module contains all database models organized by domain:
- manufacturing: Parts, Lots, and related manufacturing entities
- inspection: Inspections, Defects, and quality control data
- inference: ML inference jobs and results
- artifacts: File storage and metadata
- reporting: Reports and analytics
- audit: Audit logs for compliance and traceability
- users: User management and authentication
"""

from .manufacturing import Part, Lot
from .inspection import Inspection, Defect
from .inference import InferenceJob
from .artifacts import Artifact
from .reporting import Report
from .audit import AuditLog
from .users import (
    User,
    Role,
    UserRole,
    UserSession,
    AuthEvent,
    PasswordHistory,
    ElectronicSignature,
)

__all__ = [
    # Manufacturing models
    "Part",
    "Lot",
    # Inspection models
    "Inspection",
    "Defect",
    # ML inference models
    "InferenceJob",
    # Artifact models
    "Artifact",
    # Reporting models
    "Report",
    # Audit models
    "AuditLog",
    # User and auth models
    "User",
    "Role",
    "UserRole",
    "UserSession",
    "AuthEvent",
    "PasswordHistory",
    "ElectronicSignature",
]