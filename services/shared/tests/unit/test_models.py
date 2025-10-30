"""Unit tests for database models"""

import pytest
from datetime import date, datetime
from decimal import Decimal
import uuid

from ...models.manufacturing import Part, Lot
from ...models.inspection import Inspection, Defect
from ...models.inference import InferenceJob
from ...models.artifacts import Artifact
from ...models.reporting import Report
from ...models.audit import AuditLog
from ...database.enums import (
    PartTypeEnum,
    LotStatusEnum,
    InspectionTypeEnum,
    InspectionStatusEnum,
    DefectTypeEnum,
    DefectSeverityEnum,
    DetectionMethodEnum,
    ReviewStatusEnum,
    InferenceStatusEnum,
    ArtifactTypeEnum,
    StorageLocationEnum,
    ReportTypeEnum,
    ReportStatusEnum,
    ReportFormatEnum,
    AuditActionEnum,
)


class TestPartModel:
    """Tests for Part model"""
    
    def test_part_creation(self):
        """Test creating a Part instance"""
        part = Part(
            part_number="TEST-001",
            part_name="Test Part",
            part_type=PartTypeEnum.PCB,
            specifications={"layers": 4},
            tolerance_requirements={"dimensional": "±0.1mm"},
        )
        
        assert part.part_number == "TEST-001"
        assert part.part_name == "Test Part"
        assert part.part_type == PartTypeEnum.PCB
        assert part.specifications == {"layers": 4}
        assert part.version == 1
    
    def test_part_repr(self):
        """Test Part string representation"""
        part = Part(
            id=uuid.uuid4(),
            part_number="TEST-001",
            part_name="Test Part",
            part_type=PartTypeEnum.PCB,
        )
        
        repr_str = repr(part)
        assert "Part" in repr_str
        assert "TEST-001" in repr_str


class TestLotModel:
    """Tests for Lot model"""
    
    def test_lot_creation(self):
        """Test creating a Lot instance"""
        part_id = uuid.uuid4()
        lot = Lot(
            lot_number="LOT-001",
            part_id=part_id,
            production_date=date(2025, 10, 29),
            batch_size=1000,
            production_line="LINE-A",
            status=LotStatusEnum.ACTIVE,
        )
        
        assert lot.lot_number == "LOT-001"
        assert lot.part_id == part_id
        assert lot.batch_size == 1000
        assert lot.status == LotStatusEnum.ACTIVE
    
    def test_lot_default_status(self):
        """Test Lot default status is active"""
        lot = Lot(
            lot_number="LOT-002",
            part_id=uuid.uuid4(),
            production_date=date(2025, 10, 29),
            batch_size=500,
            production_line="LINE-B",
        )
        
        assert lot.status == LotStatusEnum.ACTIVE


class TestInspectionModel:
    """Tests for Inspection model"""
    
    def test_inspection_creation(self):
        """Test creating an Inspection instance"""
        lot_id = uuid.uuid4()
        inspection = Inspection(
            lot_id=lot_id,
            chip_id="CHIP-001",
            inspection_type=InspectionTypeEnum.VISUAL,
            status=InspectionStatusEnum.PENDING,
            priority=5,
            station_id="STATION-A",
        )
        
        assert inspection.lot_id == lot_id
        assert inspection.chip_id == "CHIP-001"
        assert inspection.inspection_type == InspectionTypeEnum.VISUAL
        assert inspection.status == InspectionStatusEnum.PENDING
        assert inspection.priority == 5
    
    def test_inspection_default_priority(self):
        """Test Inspection default priority is 5"""
        inspection = Inspection(
            lot_id=uuid.uuid4(),
            chip_id="CHIP-002",
            inspection_type=InspectionTypeEnum.ELECTRICAL,
            station_id="STATION-B",
        )
        
        assert inspection.priority == 5


class TestDefectModel:
    """Tests for Defect model"""
    
    def test_defect_creation(self):
        """Test creating a Defect instance"""
        inspection_id = uuid.uuid4()
        defect = Defect(
            inspection_id=inspection_id,
            defect_type=DefectTypeEnum.SCRATCH,
            severity=DefectSeverityEnum.MEDIUM,
            confidence=Decimal("0.95"),
            location={"x": 100, "y": 200, "width": 50, "height": 30},
            detection_method=DetectionMethodEnum.ML_AUTOMATED,
        )
        
        assert defect.inspection_id == inspection_id
        assert defect.defect_type == DefectTypeEnum.SCRATCH
        assert defect.severity == DefectSeverityEnum.MEDIUM
        assert defect.confidence == Decimal("0.95")
        assert defect.detection_method == DetectionMethodEnum.ML_AUTOMATED
    
    def test_defect_default_review_status(self):
        """Test Defect default review status"""
        defect = Defect(
            inspection_id=uuid.uuid4(),
            defect_type=DefectTypeEnum.VOID,
            severity=DefectSeverityEnum.LOW,
            confidence=Decimal("0.85"),
            location={},
            detection_method=DetectionMethodEnum.MANUAL_REVIEW,
        )
        
        assert defect.review_status == ReviewStatusEnum.PENDING


class TestInferenceJobModel:
    """Tests for InferenceJob model"""
    
    def test_inference_job_creation(self):
        """Test creating an InferenceJob instance"""
        inspection_id = uuid.uuid4()
        job = InferenceJob(
            inspection_id=inspection_id,
            model_name="defect_detector",
            model_version="v2.0",
            status=InferenceStatusEnum.QUEUED,
            priority=7,
        )
        
        assert job.inspection_id == inspection_id
        assert job.model_name == "defect_detector"
        assert job.model_version == "v2.0"
        assert job.status == InferenceStatusEnum.QUEUED
        assert job.priority == 7
        assert job.batch_size == 1
    
    def test_inference_job_defaults(self):
        """Test InferenceJob default values"""
        job = InferenceJob(
            inspection_id=uuid.uuid4(),
            model_name="test_model",
            model_version="v1.0",
        )
        
        assert job.status == InferenceStatusEnum.QUEUED
        assert job.priority == 5
        assert job.batch_size == 1
        assert job.confidence_threshold == Decimal("0.7")


class TestArtifactModel:
    """Tests for Artifact model"""
    
    def test_artifact_creation(self):
        """Test creating an Artifact instance"""
        inspection_id = uuid.uuid4()
        artifact = Artifact(
            inspection_id=inspection_id,
            artifact_type=ArtifactTypeEnum.IMAGE,
            file_name="test_image.jpg",
            file_path="/artifacts/2025/10/test_image.jpg",
            content_type="image/jpeg",
            file_size_bytes=1024000,
            checksum_sha256="a" * 64,
            storage_location=StorageLocationEnum.PRIMARY,
        )
        
        assert artifact.inspection_id == inspection_id
        assert artifact.artifact_type == ArtifactTypeEnum.IMAGE
        assert artifact.file_name == "test_image.jpg"
        assert artifact.file_size_bytes == 1024000
        assert len(artifact.checksum_sha256) == 64


class TestReportModel:
    """Tests for Report model"""
    
    def test_report_creation(self):
        """Test creating a Report instance"""
        user_id = uuid.uuid4()
        report = Report(
            report_type=ReportTypeEnum.INSPECTION_SUMMARY,
            title="Daily Inspection Report",
            data_range={"start_date": "2025-10-01", "end_date": "2025-10-29"},
            status=ReportStatusEnum.GENERATING,
            format=ReportFormatEnum.PDF,
            generated_by=user_id,
        )
        
        assert report.report_type == ReportTypeEnum.INSPECTION_SUMMARY
        assert report.title == "Daily Inspection Report"
        assert report.status == ReportStatusEnum.GENERATING
        assert report.format == ReportFormatEnum.PDF
        assert report.generated_by == user_id


class TestAuditLogModel:
    """Tests for AuditLog model"""
    
    def test_audit_log_creation(self):
        """Test creating an AuditLog instance"""
        entity_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        audit = AuditLog(
            entity_type="inspections",
            entity_id=entity_id,
            action=AuditActionEnum.CREATE,
            user_id=user_id,
            session_id="session-123",
            changes={"status": {"from": None, "to": "pending"}},
        )
        
        assert audit.entity_type == "inspections"
        assert audit.entity_id == entity_id
        assert audit.action == AuditActionEnum.CREATE
        assert audit.user_id == user_id
        assert "status" in audit.changes


class TestEnums:
    """Tests for enum types"""
    
    def test_part_type_enum(self):
        """Test PartTypeEnum values"""
        assert PartTypeEnum.PCB.value == "pcb"
        assert PartTypeEnum.SEMICONDUCTOR.value == "semiconductor"
    
    def test_inspection_type_enum(self):
        """Test InspectionTypeEnum values"""
        assert InspectionTypeEnum.VISUAL.value == "visual"
        assert InspectionTypeEnum.ELECTRICAL.value == "electrical"
    
    def test_defect_severity_enum(self):
        """Test DefectSeverityEnum values"""
        assert DefectSeverityEnum.LOW.value == "low"
        assert DefectSeverityEnum.CRITICAL.value == "critical"
