"""
Database enumeration types

All enum types used in the database schema, matching docs/database/schema.md
"""

import enum


class PartTypeEnum(str, enum.Enum):
    """Part type classification"""
    PCB = "pcb"
    SEMICONDUCTOR = "semiconductor"
    COMPONENT = "component"
    ASSEMBLY = "assembly"
    WAFER = "wafer"


class LotStatusEnum(str, enum.Enum):
    """Manufacturing lot status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    QUARANTINED = "quarantined"
    RELEASED = "released"
    REJECTED = "rejected"


class InspectionTypeEnum(str, enum.Enum):
    """Type of quality inspection"""
    VISUAL = "visual"
    ELECTRICAL = "electrical"
    THERMAL = "thermal"
    DIMENSIONAL = "dimensional"
    FUNCTIONAL = "functional"
    OPTICAL = "optical"


class InspectionStatusEnum(str, enum.Enum):
    """Inspection processing status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DefectTypeEnum(str, enum.Enum):
    """Types of manufacturing defects"""
    SCRATCH = "scratch"
    VOID = "void"
    CONTAMINATION = "contamination"
    MISALIGNMENT = "misalignment"
    SHORT = "short"
    OPEN = "open"
    CRACK = "crack"
    BURN = "burn"
    FOREIGN_OBJECT = "foreign_object"
    DELAMINATION = "delamination"
    CORROSION = "corrosion"


class DefectSeverityEnum(str, enum.Enum):
    """Defect severity classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DetectionMethodEnum(str, enum.Enum):
    """Method used to detect defect"""
    ML_AUTOMATED = "ml_automated"
    MANUAL_REVIEW = "manual_review"
    HYBRID = "hybrid"
    RULE_BASED = "rule_based"


class ReviewStatusEnum(str, enum.Enum):
    """Defect review status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    FALSE_POSITIVE = "false_positive"


class InferenceStatusEnum(str, enum.Enum):
    """ML inference job status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ArtifactTypeEnum(str, enum.Enum):
    """Type of artifact/file"""
    IMAGE = "image"
    VIDEO = "video"
    MEASUREMENT = "measurement"
    DOCUMENT = "document"
    LOG = "log"
    MODEL_OUTPUT = "model_output"


class StorageLocationEnum(str, enum.Enum):
    """Storage tier for artifacts"""
    PRIMARY = "primary"
    ARCHIVE = "archive"
    COLD_STORAGE = "cold_storage"
    TEMPORARY = "temporary"


class ReportTypeEnum(str, enum.Enum):
    """Type of generated report"""
    INSPECTION_SUMMARY = "inspection_summary"
    DEFECT_ANALYSIS = "defect_analysis"
    QUALITY_METRICS = "quality_metrics"
    PRODUCTION_OVERVIEW = "production_overview"
    COMPLIANCE_REPORT = "compliance_report"
    PERFORMANCE_ANALYSIS = "performance_analysis"


class ReportStatusEnum(str, enum.Enum):
    """Report generation status"""
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReportFormatEnum(str, enum.Enum):
    """Report output format"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"


class AuditActionEnum(str, enum.Enum):
    """Type of audited action"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    DOWNLOAD = "download"
    EXPORT = "export"


class EventLevelEnum(str, enum.Enum):
    """Event/log severity level"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
