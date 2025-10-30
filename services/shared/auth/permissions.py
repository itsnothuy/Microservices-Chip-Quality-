"""
Role-Based Access Control (RBAC) permission system.

Provides hierarchical role and permission management for manufacturing
quality control operations with FDA compliance requirements.
"""

from enum import Enum
from typing import Set, List, Dict, Optional
from dataclasses import dataclass


class Permission(str, Enum):
    """
    Granular permission definitions for the platform.
    
    Permission format: <resource>:<action>
    """
    
    # Inspection permissions
    INSPECTIONS_READ = "inspections:read"
    INSPECTIONS_WRITE = "inspections:write"
    INSPECTIONS_UPDATE = "inspections:update"
    INSPECTIONS_DELETE = "inspections:delete"
    INSPECTIONS_APPROVE = "inspections:approve"
    
    # Defect permissions
    DEFECTS_READ = "defects:read"
    DEFECTS_WRITE = "defects:write"
    DEFECTS_UPDATE = "defects:update"
    DEFECTS_APPROVE = "defects:approve"
    
    # Batch/Lot permissions
    BATCHES_READ = "batches:read"
    BATCHES_WRITE = "batches:write"
    BATCHES_UPDATE = "batches:update"
    BATCHES_RELEASE = "batches:release"
    
    # Artifact permissions
    ARTIFACTS_READ = "artifacts:read"
    ARTIFACTS_WRITE = "artifacts:write"
    ARTIFACTS_DELETE = "artifacts:delete"
    
    # Inference permissions
    INFERENCE_EXECUTE = "inference:execute"
    INFERENCE_READ = "inference:read"
    INFERENCE_CONFIGURE = "inference:configure"
    
    # Report permissions
    REPORTS_READ = "reports:read"
    REPORTS_WRITE = "reports:write"
    REPORTS_APPROVE = "reports:approve"
    REPORTS_EXPORT = "reports:export"
    
    # User management permissions
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"
    
    # System administration
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_CONFIGURE = "system:configure"
    SYSTEM_MONITOR = "system:monitor"
    
    # Compliance and audit
    COMPLIANCE_READ = "compliance:read"
    COMPLIANCE_WRITE = "compliance:write"
    COMPLIANCE_AUDIT = "compliance:audit"


@dataclass
class RoleDefinition:
    """
    Role definition with associated permissions and metadata.
    """
    
    name: str
    display_name: str
    description: str
    permissions: Set[Permission]
    requires_mfa: bool = False
    max_session_hours: int = 8
    can_impersonate: bool = False


# Manufacturing-specific role definitions
MANUFACTURING_ROLES: Dict[str, RoleDefinition] = {
    "admin": RoleDefinition(
        name="admin",
        display_name="System Administrator",
        description="Full system access and user management",
        permissions={
            Permission.INSPECTIONS_READ,
            Permission.INSPECTIONS_WRITE,
            Permission.INSPECTIONS_UPDATE,
            Permission.INSPECTIONS_DELETE,
            Permission.INSPECTIONS_APPROVE,
            Permission.DEFECTS_READ,
            Permission.DEFECTS_WRITE,
            Permission.DEFECTS_UPDATE,
            Permission.DEFECTS_APPROVE,
            Permission.BATCHES_READ,
            Permission.BATCHES_WRITE,
            Permission.BATCHES_UPDATE,
            Permission.BATCHES_RELEASE,
            Permission.ARTIFACTS_READ,
            Permission.ARTIFACTS_WRITE,
            Permission.ARTIFACTS_DELETE,
            Permission.INFERENCE_EXECUTE,
            Permission.INFERENCE_READ,
            Permission.INFERENCE_CONFIGURE,
            Permission.REPORTS_READ,
            Permission.REPORTS_WRITE,
            Permission.REPORTS_APPROVE,
            Permission.REPORTS_EXPORT,
            Permission.USERS_READ,
            Permission.USERS_WRITE,
            Permission.USERS_UPDATE,
            Permission.USERS_DELETE,
            Permission.SYSTEM_ADMIN,
            Permission.SYSTEM_CONFIGURE,
            Permission.SYSTEM_MONITOR,
            Permission.COMPLIANCE_READ,
            Permission.COMPLIANCE_WRITE,
            Permission.COMPLIANCE_AUDIT,
        },
        requires_mfa=True,
        max_session_hours=4,
        can_impersonate=True
    ),
    
    "quality_manager": RoleDefinition(
        name="quality_manager",
        display_name="Quality Manager",
        description="Quality oversight and approval authority",
        permissions={
            Permission.INSPECTIONS_READ,
            Permission.INSPECTIONS_WRITE,
            Permission.INSPECTIONS_UPDATE,
            Permission.INSPECTIONS_APPROVE,
            Permission.DEFECTS_READ,
            Permission.DEFECTS_WRITE,
            Permission.DEFECTS_UPDATE,
            Permission.DEFECTS_APPROVE,
            Permission.BATCHES_READ,
            Permission.BATCHES_WRITE,
            Permission.BATCHES_UPDATE,
            Permission.BATCHES_RELEASE,
            Permission.ARTIFACTS_READ,
            Permission.ARTIFACTS_WRITE,
            Permission.INFERENCE_READ,
            Permission.INFERENCE_CONFIGURE,
            Permission.REPORTS_READ,
            Permission.REPORTS_WRITE,
            Permission.REPORTS_APPROVE,
            Permission.REPORTS_EXPORT,
            Permission.USERS_READ,
            Permission.SYSTEM_MONITOR,
            Permission.COMPLIANCE_READ,
            Permission.COMPLIANCE_WRITE,
        },
        requires_mfa=True,
        max_session_hours=8
    ),
    
    "operator": RoleDefinition(
        name="operator",
        display_name="Production Operator",
        description="Production line operation and basic inspection",
        permissions={
            Permission.INSPECTIONS_READ,
            Permission.INSPECTIONS_WRITE,
            Permission.DEFECTS_READ,
            Permission.DEFECTS_WRITE,
            Permission.ARTIFACTS_READ,
            Permission.ARTIFACTS_WRITE,
            Permission.INFERENCE_EXECUTE,
            Permission.REPORTS_READ,
        },
        requires_mfa=False,
        max_session_hours=8
    ),
    
    "inspector": RoleDefinition(
        name="inspector",
        display_name="Quality Inspector",
        description="Detailed inspection and defect classification",
        permissions={
            Permission.INSPECTIONS_READ,
            Permission.INSPECTIONS_WRITE,
            Permission.INSPECTIONS_UPDATE,
            Permission.DEFECTS_READ,
            Permission.DEFECTS_WRITE,
            Permission.DEFECTS_UPDATE,
            Permission.BATCHES_READ,
            Permission.ARTIFACTS_READ,
            Permission.ARTIFACTS_WRITE,
            Permission.INFERENCE_EXECUTE,
            Permission.INFERENCE_READ,
            Permission.REPORTS_READ,
            Permission.REPORTS_WRITE,
        },
        requires_mfa=False,
        max_session_hours=8
    ),
    
    "engineer": RoleDefinition(
        name="engineer",
        display_name="Quality Engineer",
        description="Technical analysis and process optimization",
        permissions={
            Permission.INSPECTIONS_READ,
            Permission.INSPECTIONS_WRITE,
            Permission.INSPECTIONS_UPDATE,
            Permission.DEFECTS_READ,
            Permission.DEFECTS_WRITE,
            Permission.DEFECTS_UPDATE,
            Permission.BATCHES_READ,
            Permission.BATCHES_WRITE,
            Permission.BATCHES_UPDATE,
            Permission.ARTIFACTS_READ,
            Permission.ARTIFACTS_WRITE,
            Permission.INFERENCE_EXECUTE,
            Permission.INFERENCE_READ,
            Permission.INFERENCE_CONFIGURE,
            Permission.REPORTS_READ,
            Permission.REPORTS_WRITE,
            Permission.REPORTS_EXPORT,
            Permission.COMPLIANCE_READ,
        },
        requires_mfa=False,
        max_session_hours=8
    ),
    
    "auditor": RoleDefinition(
        name="auditor",
        display_name="Compliance Auditor",
        description="Read-only access for compliance review",
        permissions={
            Permission.INSPECTIONS_READ,
            Permission.DEFECTS_READ,
            Permission.BATCHES_READ,
            Permission.ARTIFACTS_READ,
            Permission.REPORTS_READ,
            Permission.REPORTS_EXPORT,
            Permission.USERS_READ,
            Permission.COMPLIANCE_READ,
            Permission.COMPLIANCE_AUDIT,
        },
        requires_mfa=True,
        max_session_hours=8
    ),
    
    "supervisor": RoleDefinition(
        name="supervisor",
        display_name="Production Supervisor",
        description="Team management and operational oversight",
        permissions={
            Permission.INSPECTIONS_READ,
            Permission.INSPECTIONS_WRITE,
            Permission.INSPECTIONS_UPDATE,
            Permission.DEFECTS_READ,
            Permission.DEFECTS_WRITE,
            Permission.DEFECTS_UPDATE,
            Permission.BATCHES_READ,
            Permission.BATCHES_WRITE,
            Permission.ARTIFACTS_READ,
            Permission.ARTIFACTS_WRITE,
            Permission.INFERENCE_EXECUTE,
            Permission.INFERENCE_READ,
            Permission.REPORTS_READ,
            Permission.REPORTS_WRITE,
            Permission.SYSTEM_MONITOR,
        },
        requires_mfa=False,
        max_session_hours=8
    ),
}


class PermissionChecker:
    """
    Permission validation and authorization checking.
    """
    
    def __init__(self):
        self.roles = MANUFACTURING_ROLES
    
    def get_role_permissions(self, role_name: str) -> Set[Permission]:
        """
        Get all permissions for a role.
        
        Args:
            role_name: Name of the role
            
        Returns:
            Set of permissions for the role
            
        Raises:
            ValueError: If role doesn't exist
        """
        if role_name not in self.roles:
            raise ValueError(f"Unknown role: {role_name}")
        
        return self.roles[role_name].permissions
    
    def has_permission(
        self,
        user_role: str,
        required_permission: Permission
    ) -> bool:
        """
        Check if user role has specific permission.
        
        Args:
            user_role: User's role name
            required_permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        if user_role not in self.roles:
            return False
        
        role_permissions = self.roles[user_role].permissions
        return required_permission in role_permissions
    
    def has_any_permission(
        self,
        user_role: str,
        required_permissions: List[Permission]
    ) -> bool:
        """
        Check if user has any of the required permissions.
        
        Args:
            user_role: User's role name
            required_permissions: List of permissions to check
            
        Returns:
            True if user has at least one permission, False otherwise
        """
        if user_role not in self.roles:
            return False
        
        role_permissions = self.roles[user_role].permissions
        return any(perm in role_permissions for perm in required_permissions)
    
    def has_all_permissions(
        self,
        user_role: str,
        required_permissions: List[Permission]
    ) -> bool:
        """
        Check if user has all required permissions.
        
        Args:
            user_role: User's role name
            required_permissions: List of permissions to check
            
        Returns:
            True if user has all permissions, False otherwise
        """
        if user_role not in self.roles:
            return False
        
        role_permissions = self.roles[user_role].permissions
        return all(perm in role_permissions for perm in required_permissions)
    
    def get_user_scopes(self, role_name: str) -> List[str]:
        """
        Get list of permission scope strings for a role.
        
        Args:
            role_name: Name of the role
            
        Returns:
            List of permission scope strings
        """
        if role_name not in self.roles:
            return []
        
        permissions = self.roles[role_name].permissions
        return [perm.value for perm in permissions]
    
    def validate_scopes(
        self,
        user_scopes: List[str],
        required_scopes: List[str]
    ) -> bool:
        """
        Validate user has all required scopes.
        
        Args:
            user_scopes: User's permission scopes
            required_scopes: Required permission scopes
            
        Returns:
            True if user has all required scopes, False otherwise
        """
        user_scope_set = set(user_scopes)
        required_scope_set = set(required_scopes)
        
        return required_scope_set.issubset(user_scope_set)
    
    def requires_mfa(self, role_name: str) -> bool:
        """
        Check if role requires MFA.
        
        Args:
            role_name: Name of the role
            
        Returns:
            True if MFA is required, False otherwise
        """
        if role_name not in self.roles:
            return False
        
        return self.roles[role_name].requires_mfa


# Global permission checker instance
permission_checker = PermissionChecker()


def check_permission(user_role: str, required_permission: Permission) -> bool:
    """
    Convenience function to check single permission.
    
    Args:
        user_role: User's role name
        required_permission: Permission to check
        
    Returns:
        True if user has permission, False otherwise
    """
    return permission_checker.has_permission(user_role, required_permission)


def get_role_scopes(role_name: str) -> List[str]:
    """
    Convenience function to get role scopes.
    
    Args:
        role_name: Name of the role
        
    Returns:
        List of permission scope strings
    """
    return permission_checker.get_user_scopes(role_name)
