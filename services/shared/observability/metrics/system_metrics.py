"""
System Performance Metrics

Tracks system-level performance metrics:
- API response times and throughput
- Database query performance
- Cache hit rates
- Queue depths and processing rates
- Infrastructure resource usage
"""

from prometheus_client import Counter, Histogram, Gauge, Summary
import structlog

logger = structlog.get_logger()


class SystemMetrics:
    """System performance and infrastructure metrics."""
    
    def __init__(self) -> None:
        # HTTP/API metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
        )
        
        self.http_request_size = Summary(
            'http_request_size_bytes',
            'HTTP request size',
            ['method', 'endpoint']
        )
        
        self.http_response_size = Summary(
            'http_response_size_bytes',
            'HTTP response size',
            ['method', 'endpoint']
        )
        
        # Database metrics
        self.db_queries_total = Counter(
            'db_queries_total',
            'Total database queries',
            ['operation', 'table', 'status']
        )
        
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration',
            ['operation', 'table'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
        )
        
        self.db_connections_active = Gauge(
            'db_connections_active',
            'Number of active database connections',
            ['pool']
        )
        
        self.db_connection_pool_size = Gauge(
            'db_connection_pool_size',
            'Database connection pool size',
            ['pool', 'state']
        )
        
        # Cache metrics
        self.cache_operations = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'cache_name', 'result']
        )
        
        self.cache_hit_rate = Gauge(
            'cache_hit_rate',
            'Cache hit rate percentage',
            ['cache_name']
        )
        
        self.cache_latency = Histogram(
            'cache_latency_seconds',
            'Cache operation latency',
            ['operation', 'cache_name'],
            buckets=[0.0001, 0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1]
        )
        
        # Message queue metrics
        self.queue_size = Gauge(
            'queue_size',
            'Number of messages in queue',
            ['queue_name', 'status']
        )
        
        self.queue_messages_processed = Counter(
            'queue_messages_processed_total',
            'Total messages processed from queue',
            ['queue_name', 'status']
        )
        
        self.queue_processing_duration = Histogram(
            'queue_processing_duration_seconds',
            'Message processing duration',
            ['queue_name'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
        )
        
        # External service calls
        self.external_requests = Counter(
            'external_requests_total',
            'External service requests',
            ['service', 'endpoint', 'status']
        )
        
        self.external_request_duration = Histogram(
            'external_request_duration_seconds',
            'External service request duration',
            ['service', 'endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        # Error tracking
        self.errors_total = Counter(
            'errors_total',
            'Total errors',
            ['error_type', 'severity', 'component']
        )
        
        self.exceptions_unhandled = Counter(
            'exceptions_unhandled_total',
            'Unhandled exceptions',
            ['exception_type', 'component']
        )
        
        # Resource utilization
        self.cpu_usage = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage',
            ['core']
        )
        
        self.memory_usage = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes',
            ['type']
        )
        
        self.disk_usage = Gauge(
            'disk_usage_bytes',
            'Disk usage in bytes',
            ['mount_point', 'type']
        )
        
        logger.info("System metrics initialized")


class APIMetrics:
    """Detailed API-specific metrics."""
    
    def __init__(self) -> None:
        # Request rate limiting
        self.rate_limit_hits = Counter(
            'rate_limit_hits_total',
            'Rate limit hits',
            ['endpoint', 'client_id']
        )
        
        # Authentication
        self.auth_attempts = Counter(
            'auth_attempts_total',
            'Authentication attempts',
            ['method', 'result']
        )
        
        self.auth_token_validations = Counter(
            'auth_token_validations_total',
            'Token validation attempts',
            ['result']
        )
        
        # API versioning
        self.api_version_usage = Counter(
            'api_version_usage_total',
            'API version usage',
            ['version', 'endpoint']
        )
        
        # Concurrent requests
        self.active_requests = Gauge(
            'active_requests',
            'Number of active requests',
            ['endpoint']
        )
        
        logger.info("API metrics initialized")


# Singleton instances
system_metrics = SystemMetrics()
api_metrics = APIMetrics()
