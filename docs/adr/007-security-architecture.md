# ADR-007: Security Architecture and Implementation

## Status
Accepted

## Context
The chip quality inspection platform handles sensitive manufacturing data and requires enterprise-grade security to protect:
- **Intellectual Property**: Proprietary chip designs and manufacturing processes
- **Quality Data**: Inspection results and defect patterns
- **System Access**: API endpoints and internal services
- **Compliance Requirements**: Manufacturing audit trails and data retention
- **Multi-tenant Access**: Different access levels for operators, engineers, and management

## Decision
We will implement a comprehensive security architecture based on industry standards with defense-in-depth principles:

### Core Security Components
- **OAuth2 + JWT**: Token-based authentication with fine-grained scopes
- **Role-Based Access Control (RBAC)**: Hierarchical permissions system
- **API Gateway Security**: Rate limiting, request validation, and threat protection
- **Network Security**: Zero-trust networking with service mesh
- **Data Protection**: Encryption at rest and in transit
- **Audit Logging**: Comprehensive security event tracking

## Authentication & Authorization Architecture

### OAuth2 + JWT Implementation

#### Token Structure
```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT",
    "kid": "key-2025-01"
  },
  "payload": {
    "iss": "https://auth.chip-quality.com",
    "sub": "user_12345",
    "aud": ["chip-quality-api"],
    "exp": 1737372000,
    "iat": 1737368400,
    "jti": "token_abc123",
    "scope": "inspections:read inspections:write defects:read reports:write",
    "user_id": "user_12345",
    "tenant_id": "acme_manufacturing",
    "role": "quality_engineer",
    "permissions": [
      "view_inspections",
      "create_inspections", 
      "view_defects",
      "generate_reports"
    ]
  }
}
```

#### Security Middleware Implementation
```python
from jose import JWTError, jwt
from cryptography.hazmat.primitives import serialization
import httpx
from functools import wraps

class SecurityConfig:
    JWT_ALGORITHM = "RS256"
    JWT_ISSUER = "https://auth.chip-quality.com"
    JWT_AUDIENCE = ["chip-quality-api"]
    JWKS_URL = "https://auth.chip-quality.com/.well-known/jwks.json"
    JWKS_CACHE_TTL = 3600  # 1 hour
    TOKEN_LEEWAY = 30  # 30 seconds clock skew tolerance

class JWTSecurityMiddleware:
    def __init__(self):
        self.public_keys = {}
        self.keys_last_updated = 0
    
    async def get_public_key(self, kid: str) -> str:
        """Fetch and cache public keys from JWKS endpoint"""
        current_time = time.time()
        
        if current_time - self.keys_last_updated > SecurityConfig.JWKS_CACHE_TTL:
            async with httpx.AsyncClient() as client:
                response = await client.get(SecurityConfig.JWKS_URL)
                jwks = response.json()
                
                for key in jwks["keys"]:
                    key_id = key["kid"]
                    # Convert JWK to PEM format
                    self.public_keys[key_id] = jwk_to_pem(key)
                
                self.keys_last_updated = current_time
        
        return self.public_keys.get(kid)
    
    async def verify_token(self, token: str) -> dict:
        """Verify JWT token and extract claims"""
        try:
            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                raise SecurityError("Missing key ID in token header")
            
            # Get public key
            public_key = await self.get_public_key(kid)
            if not public_key:
                raise SecurityError(f"Unknown key ID: {kid}")
            
            # Verify token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[SecurityConfig.JWT_ALGORITHM],
                issuer=SecurityConfig.JWT_ISSUER,
                audience=SecurityConfig.JWT_AUDIENCE,
                leeway=SecurityConfig.TOKEN_LEEWAY
            )
            
            return payload
            
        except JWTError as e:
            raise SecurityError(f"Invalid token: {str(e)}")
    
    async def __call__(self, request: Request, call_next):
        # Skip authentication for public endpoints
        if request.url.path in ["/health", "/metrics", "/docs"]:
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid authorization header"
            )
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            # Verify token and extract claims
            claims = await self.verify_token(token)
            
            # Add claims to request state
            request.state.user_id = claims["user_id"]
            request.state.tenant_id = claims["tenant_id"]
            request.state.role = claims["role"]
            request.state.permissions = claims["permissions"]
            request.state.scopes = claims["scope"].split()
            
            return await call_next(request)
            
        except SecurityError as e:
            raise HTTPException(status_code=401, detail=str(e))

# Apply middleware to FastAPI app
app.add_middleware(JWTSecurityMiddleware)
```

### Role-Based Access Control (RBAC)

#### Permission System Design
```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Set

class Resource(Enum):
    INSPECTIONS = "inspections"
    DEFECTS = "defects"
    REPORTS = "reports"
    ARTIFACTS = "artifacts"
    USERS = "users"
    SYSTEM = "system"

class Action(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"

@dataclass
class Permission:
    resource: Resource
    action: Action
    conditions: List[str] = None  # For conditional permissions
    
    def __str__(self):
        return f"{self.resource.value}:{self.action.value}"

class Role:
    def __init__(self, name: str, permissions: List[Permission]):
        self.name = name
        self.permissions = permissions
    
    def has_permission(self, resource: Resource, action: Action) -> bool:
        return any(
            p.resource == resource and p.action == action 
            for p in self.permissions
        )

# Predefined roles
ROLES = {
    "operator": Role("operator", [
        Permission(Resource.INSPECTIONS, Action.READ),
        Permission(Resource.INSPECTIONS, Action.CREATE),
        Permission(Resource.DEFECTS, Action.READ),
        Permission(Resource.ARTIFACTS, Action.READ),
    ]),
    
    "quality_engineer": Role("quality_engineer", [
        Permission(Resource.INSPECTIONS, Action.READ),
        Permission(Resource.INSPECTIONS, Action.CREATE),
        Permission(Resource.INSPECTIONS, Action.UPDATE),
        Permission(Resource.DEFECTS, Action.READ),
        Permission(Resource.DEFECTS, Action.UPDATE),
        Permission(Resource.REPORTS, Action.READ),
        Permission(Resource.REPORTS, Action.CREATE),
        Permission(Resource.ARTIFACTS, Action.READ),
    ]),
    
    "manager": Role("manager", [
        Permission(Resource.INSPECTIONS, Action.READ),
        Permission(Resource.DEFECTS, Action.READ),
        Permission(Resource.REPORTS, Action.READ),
        Permission(Resource.REPORTS, Action.CREATE),
        Permission(Resource.USERS, Action.READ),
        Permission(Resource.ARTIFACTS, Action.READ),
    ]),
    
    "admin": Role("admin", [
        Permission(resource, action) 
        for resource in Resource 
        for action in Action
    ])
}

# Authorization decorator
def require_permission(resource: Resource, action: Action):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs (FastAPI dependency injection)
            request = kwargs.get('request') or args[0]
            
            user_role = getattr(request.state, 'role', None)
            if not user_role:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            role = ROLES.get(user_role)
            if not role or not role.has_permission(resource, action):
                raise HTTPException(
                    status_code=403, 
                    detail=f"Insufficient permissions: {resource.value}:{action.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage in API endpoints
@app.post("/v1/inspections")
@require_permission(Resource.INSPECTIONS, Action.CREATE)
async def create_inspection(
    request: Request,
    inspection_data: InspectionCreate
):
    # Implementation here
    pass
```

### API Gateway Security

#### Rate Limiting Implementation
```python
import redis.asyncio as redis
from typing import Optional
import time
import hashlib

class TokenBucketRateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int,
        cost: int = 1
    ) -> tuple[bool, dict]:
        """
        Token bucket rate limiting
        
        Args:
            key: Unique identifier (user_id, IP, etc.)
            limit: Number of tokens per window
            window: Time window in seconds
            cost: Number of tokens to consume
            
        Returns:
            (allowed, info) where info contains rate limit details
        """
        current_time = time.time()
        bucket_key = f"rate_limit:{key}"
        
        # Use Lua script for atomic operations
        lua_script = """
        local bucket_key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local cost = tonumber(ARGV[3])
        local current_time = tonumber(ARGV[4])
        
        local bucket = redis.call('HMGET', bucket_key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or limit
        local last_refill = tonumber(bucket[2]) or current_time
        
        -- Calculate tokens to add based on time elapsed
        local time_elapsed = current_time - last_refill
        local tokens_to_add = math.floor(time_elapsed * limit / window)
        tokens = math.min(tokens + tokens_to_add, limit)
        
        local allowed = tokens >= cost
        local remaining = tokens
        
        if allowed then
            remaining = tokens - cost
        end
        
        -- Update bucket
        redis.call('HMSET', bucket_key, 
                  'tokens', remaining, 
                  'last_refill', current_time)
        redis.call('EXPIRE', bucket_key, window * 2)
        
        return {allowed and 1 or 0, remaining, limit}
        """
        
        result = await self.redis.eval(
            lua_script, 1, bucket_key, limit, window, cost, current_time
        )
        
        allowed, remaining, total = result
        
        return bool(allowed), {
            'remaining': remaining,
            'limit': total,
            'reset_time': current_time + window
        }

# Rate limiting middleware
class RateLimitMiddleware:
    def __init__(self, redis_client: redis.Redis):
        self.limiter = TokenBucketRateLimiter(redis_client)
        
        # Different limits for different endpoints
        self.limits = {
            "default": (100, 60),  # 100 requests per minute
            "auth": (10, 60),      # 10 auth requests per minute
            "upload": (20, 300),   # 20 uploads per 5 minutes
            "inference": (50, 60), # 50 inference requests per minute
        }
    
    def get_rate_limit_key(self, request: Request) -> str:
        """Generate rate limit key based on user or IP"""
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Fallback to IP address
        client_ip = request.client.host
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()
        
        return f"ip:{client_ip}"
    
    def get_endpoint_category(self, request: Request) -> str:
        """Categorize endpoint for rate limiting"""
        path = request.url.path
        
        if "/auth/" in path:
            return "auth"
        elif "/artifacts/" in path and request.method == "POST":
            return "upload"
        elif "/infer" in path:
            return "inference"
        else:
            return "default"
    
    async def __call__(self, request: Request, call_next):
        # Get rate limit parameters
        key = self.get_rate_limit_key(request)
        category = self.get_endpoint_category(request)
        limit, window = self.limits[category]
        
        # Check rate limit
        allowed, info = await self.limiter.is_allowed(key, limit, window)
        
        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )
        else:
            response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(info['limit'])
        response.headers["X-RateLimit-Remaining"] = str(info['remaining'])
        response.headers["X-RateLimit-Reset"] = str(int(info['reset_time']))
        
        return response

app.add_middleware(RateLimitMiddleware, redis_client=redis_client)
```

### Network Security

#### Service Mesh Security with Istio
```yaml
# Istio security policies
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: chip-quality
spec:
  mtls:
    mode: STRICT  # Enforce mTLS for all service communication
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: api-gateway-policy
  namespace: chip-quality
spec:
  selector:
    matchLabels:
      app: api-gateway
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/istio-system/sa/istio-ingressgateway-service-account"]
    to:
    - operation:
        methods: ["GET", "POST", "PUT", "DELETE"]
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: inference-service-policy
  namespace: chip-quality
spec:
  selector:
    matchLabels:
      app: inference-service
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/chip-quality/sa/api-gateway"]
    to:
    - operation:
        methods: ["POST"]
        paths: ["/inference/*"]
---
# Network policies for additional security
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: chip-quality-network-policy
  namespace: chip-quality
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: chip-quality
    - namespaceSelector:
        matchLabels:
          name: istio-system
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: chip-quality
  - to:
    - namespaceSelector:
        matchLabels:
          name: istio-system
  - to: []  # Allow external traffic
    ports:
    - protocol: TCP
      port: 443  # HTTPS only
    - protocol: TCP
      port: 53   # DNS
    - protocol: UDP
      port: 53   # DNS
```

### Data Protection

#### Encryption at Rest
```yaml
# StorageClass with encryption
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: encrypted-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
---
# PostgreSQL with encryption
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-cluster
spec:
  instances: 3
  
  postgresql:
    parameters:
      ssl: "on"
      ssl_cert_file: "/opt/certs/server.crt"
      ssl_key_file: "/opt/certs/server.key"
      ssl_ca_file: "/opt/certs/ca.crt"
      ssl_ciphers: "ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256"
  
  certificates:
    serverTLSSecret: postgres-server-certs
    serverCASecret: postgres-ca-certs
    clientCASecret: postgres-client-ca-certs
  
  storage:
    size: 100Gi
    storageClass: encrypted-ssd
```

#### Application-Level Encryption
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class DataEncryption:
    def __init__(self, encryption_key: str):
        # Derive encryption key from password
        password = encryption_key.encode()
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self.cipher_suite = Fernet(key)
        self.salt = salt
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data like defect descriptions"""
        if not data:
            return data
        
        encrypted = self.cipher_suite.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return encrypted_data
        
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = self.cipher_suite.decrypt(encrypted_bytes)
        return decrypted.decode()

# Usage in data models
class DefectModel(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    inspection_id: UUID = Field(foreign_key="inspections.id")
    defect_type: str
    severity: str
    description_encrypted: Optional[str] = Field(default=None)
    
    @property
    def description(self) -> str:
        if self.description_encrypted:
            return encryption_service.decrypt_sensitive_data(self.description_encrypted)
        return ""
    
    @description.setter
    def description(self, value: str):
        if value:
            self.description_encrypted = encryption_service.encrypt_sensitive_data(value)
```

### Audit Logging

#### Comprehensive Security Audit Trail
```python
from datetime import datetime
from typing import Optional, Dict, Any
import json

class SecurityAuditLogger:
    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger
    
    def log_authentication_event(
        self,
        user_id: str,
        event_type: str,  # login, logout, token_refresh, failed_login
        ip_address: str,
        user_agent: str,
        success: bool,
        failure_reason: Optional[str] = None
    ):
        self.logger.info(
            "Authentication event",
            event_type="authentication",
            event_subtype=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_authorization_event(
        self,
        user_id: str,
        resource: str,
        action: str,
        result: str,  # allowed, denied
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.logger.info(
            "Authorization event",
            event_type="authorization",
            user_id=user_id,
            resource=resource,
            action=action,
            result=result,
            resource_id=resource_id,
            context=context,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_data_access_event(
        self,
        user_id: str,
        operation: str,  # create, read, update, delete
        table_name: str,
        record_id: str,
        sensitive_data_accessed: bool = False,
        data_classification: str = "internal"
    ):
        self.logger.info(
            "Data access event",
            event_type="data_access",
            user_id=user_id,
            operation=operation,
            table_name=table_name,
            record_id=record_id,
            sensitive_data_accessed=sensitive_data_accessed,
            data_classification=data_classification,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def log_security_incident(
        self,
        incident_type: str,
        severity: str,
        description: str,
        affected_user: Optional[str] = None,
        ip_address: Optional[str] = None,
        indicators: Optional[Dict[str, Any]] = None
    ):
        self.logger.error(
            "Security incident",
            event_type="security_incident",
            incident_type=incident_type,
            severity=severity,
            description=description,
            affected_user=affected_user,
            ip_address=ip_address,
            indicators=indicators,
            timestamp=datetime.utcnow().isoformat()
        )

# Integration with API endpoints
audit_logger = SecurityAuditLogger(logger)

@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    start_time = time.time()
    user_id = getattr(request.state, 'user_id', 'anonymous')
    
    try:
        response = await call_next(request)
        
        # Log successful operations
        if request.method in ['POST', 'PUT', 'DELETE']:
            audit_logger.log_data_access_event(
                user_id=user_id,
                operation=request.method.lower(),
                table_name=extract_table_from_path(request.url.path),
                record_id=extract_record_id_from_response(response),
                sensitive_data_accessed=is_sensitive_endpoint(request.url.path)
            )
        
        return response
        
    except HTTPException as e:
        if e.status_code == 403:
            audit_logger.log_authorization_event(
                user_id=user_id,
                resource=request.url.path,
                action=request.method,
                result="denied"
            )
        
        raise
```

## Security Monitoring and Incident Response

### Security Metrics and Alerting
```yaml
# Prometheus alerting rules for security events
groups:
- name: security.rules
  rules:
  - alert: HighFailedLoginRate
    expr: |
      (
        rate(authentication_events_total{event_subtype="failed_login"}[5m]) 
        / rate(authentication_events_total{event_subtype=~"login|failed_login"}[5m])
      ) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High failed login rate detected"
      description: "Failed login rate is {{ $value | humanizePercentage }}"

  - alert: UnauthorizedAccessAttempt
    expr: increase(authorization_events_total{result="denied"}[5m]) > 10
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Multiple unauthorized access attempts"
      description: "{{ $value }} unauthorized access attempts in 5 minutes"

  - alert: SuspiciousDataAccess
    expr: increase(data_access_events_total{sensitive_data_accessed="true"}[1h]) > 100
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High volume of sensitive data access"
      description: "{{ $value }} sensitive data access events in 1 hour"
```

## Consequences

### Positive
- **Strong Authentication**: JWT with public key cryptography prevents token forgery
- **Fine-grained Authorization**: RBAC system supports complex permission requirements
- **Defense in Depth**: Multiple security layers provide comprehensive protection
- **Audit Compliance**: Complete audit trail for regulatory requirements
- **Zero Trust Network**: Service mesh enforces encrypted communication
- **Data Protection**: Encryption at rest and in transit protects sensitive information

### Negative
- **Implementation Complexity**: Multiple security components require careful integration
- **Performance Impact**: Authentication, encryption, and logging add latency
- **Operational Overhead**: Security monitoring and incident response procedures
- **Key Management**: Secure handling of encryption keys and certificates

### Mitigations
- **Automation**: Automated security scanning and vulnerability assessment
- **Documentation**: Comprehensive security procedures and incident response playbooks
- **Training**: Regular security training for development and operations teams
- **Testing**: Penetration testing and security audits

## Implementation Timeline

### Phase 1: Authentication & Authorization (Week 1-2)
- Implement JWT authentication middleware
- Set up RBAC system with basic roles
- Deploy OAuth2 authorization server

### Phase 2: Network Security (Week 3-4)
- Configure Istio service mesh with mTLS
- Implement network policies
- Set up API gateway security

### Phase 3: Data Protection (Week 5-6)
- Enable encryption at rest for databases
- Implement application-level encryption for sensitive data
- Configure secure communication channels

### Phase 4: Monitoring & Compliance (Week 7-8)
- Deploy security monitoring and alerting
- Implement comprehensive audit logging
- Conduct security testing and validation

## References
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Istio Security Documentation](https://istio.io/latest/docs/concepts/security/)
- [JWT Security Best Practices](https://tools.ietf.org/html/rfc8725)