# ================================================================================================
# 🏭 TEST FIXTURES - MANUFACTURING DATA FACTORIES
# ================================================================================================
# Production-grade test data factories for semiconductor manufacturing platform
# Coverage: Realistic manufacturing data, compliance scenarios, edge cases
# Features: Factory Boy integration, realistic data patterns, configurable scenarios
# ================================================================================================

import factory
import factory.fuzzy
from factory.alchemy import SQLAlchemyModelFactory
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
import random
import json

from faker import Faker
from PIL import Image
import numpy as np

fake = Faker()

# ================================================================================================
# 🏭 MANUFACTURING DATA FACTORIES
# ================================================================================================

class BatchFactory(factory.Factory):
    """Factory for creating realistic batch data."""
    
    class Meta:
        model = dict
    
    batch_id = factory.Sequence(lambda n: f"BATCH_{datetime.now().year}_{n:06d}")
    product_line = factory.fuzzy.FuzzyChoice([
        "ADVANCED_PROCESSOR",
        "MEMORY_CONTROLLER", 
        "GRAPHICS_ACCELERATOR",
        "NETWORK_PROCESSOR",
        "EMBEDDED_CONTROLLER"
    ])
    wafer_lot = factory.Sequence(lambda n: f"WAFER_LOT_{chr(65 + (n % 26))}{n:03d}")
    production_date = factory.LazyFunction(lambda: datetime.utcnow().date().isoformat())
    target_quantity = factory.fuzzy.FuzzyInteger(500, 2000)
    current_quantity = factory.LazyAttribute(lambda obj: random.randint(0, obj.target_quantity))
    quality_target = factory.fuzzy.FuzzyFloat(0.95, 0.99)
    current_yield = factory.LazyAttribute(
        lambda obj: min(obj.quality_target + random.uniform(-0.05, 0.02), 1.0)
    )
    status = factory.fuzzy.FuzzyChoice([
        "CREATED", "IN_PROGRESS", "COMPLETED", "ON_HOLD", "CANCELLED"
    ])
    priority = factory.fuzzy.FuzzyChoice(["LOW", "NORMAL", "HIGH", "CRITICAL"])
    
    @factory.lazy_attribute
    def specification(self):
        """Generate realistic chip specifications."""
        base_sizes = {
            "ADVANCED_PROCESSOR": {"width": 12.5, "height": 10.2, "thickness": 0.8},
            "MEMORY_CONTROLLER": {"width": 8.0, "height": 6.5, "thickness": 0.5},
            "GRAPHICS_ACCELERATOR": {"width": 15.0, "height": 12.0, "thickness": 1.0},
            "NETWORK_PROCESSOR": {"width": 10.0, "height": 8.0, "thickness": 0.6},
            "EMBEDDED_CONTROLLER": {"width": 6.0, "height": 4.5, "thickness": 0.4}
        }
        
        base_size = base_sizes[self.product_line]
        return {
            "chip_size": {
                "width": base_size["width"] + random.uniform(-0.1, 0.1),
                "height": base_size["height"] + random.uniform(-0.1, 0.1),
                "thickness": base_size["thickness"] + random.uniform(-0.05, 0.05)
            },
            "tolerance": {
                "dimensional": random.uniform(0.005, 0.02),
                "electrical": random.uniform(0.02, 0.08)
            },
            "quality_thresholds": {
                "defect_rate_max": random.uniform(0.01, 0.05),
                "surface_quality_min": random.uniform(0.90, 0.98),
                "yield_target": self.quality_target
            },
            "electrical_specs": {
                "voltage_min": random.uniform(1.0, 1.8),
                "voltage_max": random.uniform(3.0, 5.5),
                "current_max": random.uniform(0.5, 3.0),
                "frequency_max": random.uniform(1000, 5000)  # MHz
            }
        }
    
    @factory.lazy_attribute
    def metadata(self):
        """Generate batch metadata."""
        return {
            "customer_code": fake.company()[:3].upper() + str(random.randint(100, 999)),
            "order_number": f"ORD_{random.randint(100000, 999999)}",
            "shift": random.choice(["DAY", "NIGHT", "WEEKEND"]),
            "line_operator": f"OP_{random.randint(100, 999):03d}",
            "created_by": f"PLANNER_{random.randint(10, 99):02d}",
            "estimated_completion": (
                datetime.utcnow() + timedelta(
                    hours=random.randint(4, 48)
                )
            ).isoformat(),
            "special_instructions": fake.sentence() if random.random() < 0.3 else None
        }


class ChipFactory(factory.Factory):
    """Factory for creating realistic chip data."""
    
    class Meta:
        model = dict
    
    chip_id = factory.Sequence(lambda n: f"CHIP_{n:08d}")
    batch_id = factory.SubFactory(BatchFactory, batch_id=True)
    wafer_position = factory.LazyAttribute(lambda obj: {
        "wafer_id": f"WAFER_{random.randint(1000, 9999)}",
        "die_x": random.randint(0, 20),
        "die_y": random.randint(0, 15),
        "sector": random.choice(["A", "B", "C", "D"])
    })
    manufacturing_data = factory.LazyAttribute(lambda obj: {
        "fabrication_date": fake.date_between(start_date="-30d", end_date="today").isoformat(),
        "fab_line": f"FAB_LINE_{random.randint(1, 8)}",
        "process_node": random.choice(["7nm", "10nm", "14nm", "28nm"]),
        "mask_revision": f"REV_{random.randint(10, 99)}",
        "thermal_budget": random.uniform(800, 1200),  # °C·min
        "deposition_layers": random.randint(15, 45)
    })
    
    @factory.lazy_attribute 
    def quality_metrics(self):
        """Generate realistic quality metrics."""
        # Base quality with some variation
        base_quality = random.uniform(0.85, 0.98)
        return {
            "electrical_test": {
                "voltage_dropout": random.uniform(0.1, 0.5),
                "current_leakage": random.uniform(0.01, 0.1),  # µA
                "frequency_response": base_quality + random.uniform(-0.05, 0.02),
                "noise_level": random.uniform(0.1, 2.0)  # dB
            },
            "physical_inspection": {
                "surface_roughness": random.uniform(0.1, 0.8),  # nm
                "dimensional_accuracy": base_quality + random.uniform(-0.02, 0.01),
                "color_uniformity": random.uniform(0.90, 0.99),
                "scratch_count": random.randint(0, 5)
            },
            "optical_test": {
                "light_transmission": random.uniform(0.85, 0.95),
                "refractive_index": random.uniform(1.4, 1.6),
                "optical_clarity": base_quality + random.uniform(-0.03, 0.02)
            }
        }


class InspectionFactory(factory.Factory):
    """Factory for creating realistic inspection data."""
    
    class Meta:
        model = dict
    
    inspection_id = factory.Sequence(lambda n: f"INSP_{n:08d}")
    batch_id = factory.LazyFunction(lambda: BatchFactory().batch_id)
    chip_id = factory.LazyFunction(lambda: ChipFactory().chip_id)
    inspection_type = factory.fuzzy.FuzzyChoice([
        "visual_defect_detection",
        "dimensional_measurement", 
        "electrical_test",
        "thermal_analysis",
        "surface_quality_check",
        "packaging_integrity"
    ])
    timestamp = factory.LazyFunction(lambda: datetime.utcnow().isoformat())
    operator_id = factory.Sequence(lambda n: f"OP_{n % 50 + 1:03d}")
    station_id = factory.fuzzy.FuzzyChoice([
        "STATION_A01", "STATION_A02", "STATION_B01", "STATION_B02",
        "STATION_C01", "STATION_QC01", "STATION_QC02"
    ])
    
    @factory.lazy_attribute
    def quality_metrics(self):
        """Generate inspection quality metrics."""
        # Simulate realistic quality distribution
        is_defective = random.random() < 0.05  # 5% defect rate
        
        if is_defective:
            return {
                "defect_probability": random.uniform(0.70, 0.95),
                "surface_roughness": random.uniform(0.30, 0.80),
                "dimensional_accuracy": random.uniform(0.75, 0.90),
                "color_consistency": random.uniform(0.60, 0.85),
                "overall_quality_score": random.uniform(0.20, 0.60)
            }
        else:
            return {
                "defect_probability": random.uniform(0.01, 0.15),
                "surface_roughness": random.uniform(0.05, 0.25),
                "dimensional_accuracy": random.uniform(0.95, 0.99),
                "color_consistency": random.uniform(0.90, 0.99),
                "overall_quality_score": random.uniform(0.85, 0.98)
            }
    
    @factory.lazy_attribute
    def defects_detected(self):
        """Generate realistic defect data."""
        if self.quality_metrics["defect_probability"] > 0.5:
            num_defects = random.randint(1, 4)
            defects = []
            
            for _ in range(num_defects):
                defect_types = ["scratch", "crack", "contamination", "discoloration", "deformation"]
                severities = ["minor", "moderate", "major", "critical"]
                
                defects.append({
                    "type": random.choice(defect_types),
                    "severity": random.choice(severities),
                    "location": {
                        "x": random.randint(0, 512),
                        "y": random.randint(0, 512)
                    },
                    "size": {
                        "width": random.uniform(0.1, 5.0),
                        "height": random.uniform(0.1, 5.0)
                    },
                    "confidence": random.uniform(0.60, 0.95)
                })
            
            return defects
        else:
            return []
    
    pass_fail_status = factory.LazyAttribute(
        lambda obj: "FAIL" if obj.quality_metrics["defect_probability"] > 0.5 else "PASS"
    )
    
    @factory.lazy_attribute
    def compliance_flags(self):
        """Generate compliance flags."""
        return {
            "fda_21_cfr_part_11": True,
            "iso_9001": True,
            "traceability_complete": True,
            "electronic_signature": random.random() > 0.1,  # 90% have e-signature
            "audit_trail_complete": True,
            "data_integrity_verified": True
        }
    
    @factory.lazy_attribute
    def processing_metadata(self):
        """Generate processing metadata."""
        return {
            "processing_time_ms": random.randint(150, 500),
            "ml_model_version": f"v{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 20)}",
            "confidence_threshold": random.uniform(0.75, 0.95),
            "image_quality_score": random.uniform(0.80, 0.99),
            "preprocessing_steps": random.choice([
                ["normalize", "resize", "enhance"],
                ["normalize", "denoise", "resize"],
                ["crop", "normalize", "augment"]
            ])
        }


class UserFactory(factory.Factory):
    """Factory for creating realistic user data."""
    
    class Meta:
        model = dict
    
    user_id = factory.Sequence(lambda n: f"USER_{n:06d}")
    username = factory.LazyAttribute(lambda obj: fake.user_name() + str(random.randint(10, 99)))
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@company.com")
    first_name = factory.LazyFunction(fake.first_name)
    last_name = factory.LazyFunction(fake.last_name)
    employee_id = factory.Sequence(lambda n: f"EMP_{n:05d}")
    
    roles = factory.fuzzy.FuzzyChoice([
        ["operator"],
        ["operator", "quality_inspector"],
        ["quality_inspector"],
        ["quality_inspector", "supervisor"],
        ["supervisor"],
        ["admin"],
        ["viewer"]
    ])
    
    @factory.lazy_attribute
    def permissions(self):
        """Generate permissions based on roles."""
        permission_map = {
            "operator": ["read:inspections", "write:inspections", "read:batches"],
            "quality_inspector": [
                "read:inspections", "write:inspections", "update:inspections",
                "read:batches", "write:batches", "read:reports", "write:reports"
            ],
            "supervisor": [
                "read:inspections", "write:inspections", "update:inspections",
                "read:batches", "write:batches", "approve:batches",
                "read:reports", "write:reports", "read:admin"
            ],
            "admin": [
                "read:*", "write:*", "update:*", "delete:*", "admin:*"
            ],
            "viewer": ["read:inspections", "read:batches", "read:reports"]
        }
        
        all_permissions = set()
        for role in self.roles:
            all_permissions.update(permission_map.get(role, []))
        
        return list(all_permissions)
    
    is_active = factory.fuzzy.FuzzyChoice([True, True, True, False])  # 75% active
    created_at = factory.LazyFunction(
        lambda: fake.date_time_between(start_date="-2y", end_date="now").isoformat()
    )
    last_login = factory.LazyAttribute(
        lambda obj: fake.date_time_between(
            start_date="-30d", end_date="now"
        ).isoformat() if obj.is_active else None
    )
    
    @factory.lazy_attribute
    def profile(self):
        """Generate user profile data."""
        return {
            "department": random.choice([
                "Production", "Quality Assurance", "Maintenance", 
                "Engineering", "Management", "IT"
            ]),
            "shift_preference": random.choice(["DAY", "NIGHT", "ROTATING"]),
            "certification_level": random.choice(["LEVEL_1", "LEVEL_2", "LEVEL_3", "EXPERT"]),
            "training_completed": [
                "Basic Safety",
                "Equipment Operation",
                "Quality Standards",
                "Emergency Procedures"
            ] + (["Advanced Troubleshooting"] if random.random() > 0.5 else []),
            "phone": fake.phone_number(),
            "emergency_contact": {
                "name": fake.name(),
                "relationship": random.choice(["Spouse", "Parent", "Sibling", "Friend"]),
                "phone": fake.phone_number()
            }
        }


class QualityAlertFactory(factory.Factory):
    """Factory for creating realistic quality alert data."""
    
    class Meta:
        model = dict
    
    alert_id = factory.Sequence(lambda n: f"ALERT_{n:08d}")
    batch_id = factory.LazyFunction(lambda: BatchFactory().batch_id)
    alert_type = factory.fuzzy.FuzzyChoice([
        "quality_degradation",
        "defect_rate_spike", 
        "yield_drop",
        "equipment_drift",
        "process_variation",
        "contamination_detected"
    ])
    severity = factory.fuzzy.FuzzyChoice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
    triggered_at = factory.LazyFunction(lambda: datetime.utcnow().isoformat())
    
    @factory.lazy_attribute
    def metrics(self):
        """Generate alert metrics based on type."""
        base_metrics = {
            "current_defect_rate": random.uniform(0.02, 0.15),
            "threshold_defect_rate": 0.05,
            "current_yield": random.uniform(0.80, 0.95),
            "target_yield": 0.98
        }
        
        if self.alert_type == "quality_degradation":
            base_metrics.update({
                "quality_score_avg": random.uniform(0.75, 0.90),
                "quality_score_target": 0.95,
                "trend": "decreasing"
            })
        elif self.alert_type == "defect_rate_spike":
            base_metrics.update({
                "spike_magnitude": random.uniform(2.0, 5.0),  # 2x-5x normal rate
                "spike_duration": random.randint(15, 120),    # minutes
                "affected_stations": random.sample(
                    ["STATION_A01", "STATION_A02", "STATION_B01", "STATION_B02"],
                    random.randint(1, 3)
                )
            })
        
        return base_metrics
    
    @factory.lazy_attribute
    def recommended_actions(self):
        """Generate recommended actions based on alert type."""
        action_map = {
            "quality_degradation": [
                "Review recent process changes",
                "Check equipment calibration",
                "Analyze raw material quality",
                "Increase inspection frequency"
            ],
            "defect_rate_spike": [
                "Halt production for investigation",
                "Inspect equipment for malfunction",
                "Review operator procedures",
                "Check environmental conditions"
            ],
            "yield_drop": [
                "Analyze process parameters",
                "Review material specifications",
                "Check for contamination sources",
                "Validate test procedures"
            ]
        }
        
        return action_map.get(self.alert_type, ["Investigate root cause", "Document findings"])
    
    status = factory.fuzzy.FuzzyChoice(["ACTIVE", "INVESTIGATING", "RESOLVED", "ESCALATED"])
    
    @factory.lazy_attribute
    def response_data(self):
        """Generate response data if alert has been addressed."""
        if self.status in ["INVESTIGATING", "RESOLVED"]:
            return {
                "response_time_minutes": random.randint(5, 120),
                "investigating_team": random.choice([
                    "Quality Team A", "Production Team B", "Engineering", "Maintenance"
                ]),
                "preliminary_findings": fake.sentence(),
                "actions_taken": random.sample([
                    "Equipment recalibration",
                    "Process parameter adjustment", 
                    "Material batch quarantine",
                    "Additional training provided",
                    "Preventive maintenance scheduled"
                ], random.randint(1, 3)),
                "root_cause": fake.sentence() if self.status == "RESOLVED" else None
            }
        return None


# ================================================================================================
# 🖼️ IMAGE DATA FACTORIES
# ================================================================================================

class ChipImageFactory:
    """Factory for creating realistic chip images for testing."""
    
    @staticmethod
    def create_chip_image(
        size: tuple = (512, 512),
        chip_type: str = "normal",
        defect_type: Optional[str] = None,
        noise_level: float = 0.1
    ) -> Image.Image:
        """Create synthetic chip image with realistic features."""
        
        # Create base image
        img_array = np.random.normal(128, 20, (*size, 3)).astype(np.uint8)
        
        # Add chip-like pattern
        center_x, center_y = size[0] // 2, size[1] // 2
        
        # Add circuit-like patterns
        for i in range(10, size[0] - 10, 20):
            for j in range(10, size[1] - 10, 20):
                # Add small rectangular "components"
                img_array[j:j+5, i:i+5] = [180, 180, 180]
                
                # Add "traces" (lines)
                if i < size[0] - 30:
                    img_array[j+2:j+3, i+5:i+15] = [160, 160, 160]
                if j < size[1] - 30:
                    img_array[j+5:j+15, i+2:i+3] = [160, 160, 160]
        
        # Add defects if specified
        if defect_type:
            ChipImageFactory._add_defect(img_array, defect_type, size)
        
        # Add noise
        noise = np.random.normal(0, noise_level * 255, img_array.shape)
        img_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
        
        return Image.fromarray(img_array)
    
    @staticmethod
    def _add_defect(img_array: np.ndarray, defect_type: str, size: tuple):
        """Add specific defect type to image."""
        center_x, center_y = size[0] // 2, size[1] // 2
        
        if defect_type == "scratch":
            # Add a diagonal scratch
            start_x = random.randint(50, size[0] - 50)
            start_y = random.randint(50, size[1] - 50)
            length = random.randint(20, 100)
            
            for i in range(length):
                x = min(start_x + i, size[0] - 1)
                y = min(start_y + i, size[1] - 1)
                img_array[y-1:y+2, x-1:x+2] = [50, 50, 50]  # Dark scratch
        
        elif defect_type == "crack":
            # Add a crack pattern
            crack_x = random.randint(100, size[0] - 100)
            crack_y = random.randint(100, size[1] - 100)
            
            # Jagged crack line
            for i in range(50):
                offset_x = random.randint(-2, 2)
                offset_y = random.randint(-1, 1)
                x = min(max(crack_x + i + offset_x, 0), size[0] - 1)
                y = min(max(crack_y + offset_y, 0), size[1] - 1)
                img_array[y, x] = [30, 30, 30]  # Very dark crack
        
        elif defect_type == "contamination":
            # Add circular contamination spots
            for _ in range(random.randint(1, 3)):
                spot_x = random.randint(20, size[0] - 20)
                spot_y = random.randint(20, size[1] - 20)
                radius = random.randint(5, 15)
                
                y, x = np.ogrid[:size[1], :size[0]]
                mask = (x - spot_x)**2 + (y - spot_y)**2 <= radius**2
                img_array[mask] = [255, 200, 150]  # Yellowish contamination
        
        elif defect_type == "discoloration":
            # Add area of discoloration
            start_x = random.randint(50, size[0] - 150)
            start_y = random.randint(50, size[1] - 150)
            width = random.randint(50, 100)
            height = random.randint(50, 100)
            
            color_shift = random.choice([
                [50, 0, 0],    # Reddish
                [0, 50, 0],    # Greenish
                [0, 0, 50],    # Bluish
                [-30, -30, -30] # Darker
            ])
            
            region = img_array[start_y:start_y+height, start_x:start_x+width]
            img_array[start_y:start_y+height, start_x:start_x+width] = np.clip(
                region + color_shift, 0, 255
            )


# ================================================================================================
# 🎯 SCENARIO-BASED FACTORIES
# ================================================================================================

class ComplianceScenarioFactory:
    """Factory for creating FDA 21 CFR Part 11 compliance test scenarios."""
    
    @staticmethod
    def create_audit_trail_scenario() -> Dict[str, Any]:
        """Create complete audit trail scenario."""
        user = UserFactory()
        batch = BatchFactory()
        
        # Create sequence of events
        events = []
        current_time = datetime.utcnow() - timedelta(hours=8)
        
        event_types = [
            "batch_created",
            "inspection_started", 
            "quality_check_performed",
            "supervisor_review",
            "batch_approved",
            "compliance_verification"
        ]
        
        for event_type in event_types:
            events.append({
                "event_id": f"EVENT_{uuid.uuid4().hex[:8].upper()}",
                "event_type": event_type,
                "timestamp": current_time.isoformat(),
                "user_id": user["user_id"],
                "batch_id": batch["batch_id"],
                "electronic_signature": {
                    "signer_id": user["user_id"],
                    "signing_method": "digital_certificate",
                    "signature_hash": f"SHA256_{uuid.uuid4().hex}",
                    "timestamp": current_time.isoformat()
                },
                "data_integrity": {
                    "checksum": f"MD5_{uuid.uuid4().hex}",
                    "verification_status": "VERIFIED"
                }
            })
            current_time += timedelta(minutes=random.randint(30, 120))
        
        return {
            "scenario_id": f"COMPLIANCE_{uuid.uuid4().hex[:8].upper()}",
            "user": user,
            "batch": batch,
            "audit_trail": events,
            "compliance_requirements": {
                "fda_21_cfr_part_11": True,
                "electronic_signatures": True,
                "audit_trail_complete": True,
                "data_integrity_verified": True
            }
        }
    
    @staticmethod
    def create_data_retention_scenario() -> Dict[str, Any]:
        """Create data retention compliance scenario."""
        records = []
        
        # Create records of different ages
        retention_periods = {
            "inspection_results": timedelta(days=2555),  # 7 years
            "audit_logs": timedelta(days=2555),
            "user_activity": timedelta(days=1095),       # 3 years
            "system_logs": timedelta(days=365),          # 1 year
            "temporary_data": timedelta(days=30)
        }
        
        for record_type, retention_period in retention_periods.items():
            for age_multiplier in [0.5, 1.0, 1.5, 2.0]:  # Various ages
                created_date = datetime.utcnow() - (retention_period * age_multiplier)
                
                records.append({
                    "record_id": f"REC_{uuid.uuid4().hex[:8].upper()}",
                    "record_type": record_type,
                    "created_date": created_date.isoformat(),
                    "retention_period_days": retention_period.days,
                    "legal_hold": random.random() < 0.1,  # 10% under legal hold
                    "should_be_deleted": (
                        age_multiplier > 1.0 and random.random() > 0.1
                    ),
                    "data_size_mb": random.uniform(0.1, 100.0)
                })
        
        return {
            "scenario_id": f"RETENTION_{uuid.uuid4().hex[:8].upper()}",
            "records": records,
            "total_records": len(records),
            "retention_policies": retention_periods
        }


class PerformanceScenarioFactory:
    """Factory for creating performance testing scenarios."""
    
    @staticmethod
    def create_high_load_scenario(
        concurrent_users: int = 100,
        duration_minutes: int = 30
    ) -> Dict[str, Any]:
        """Create high load testing scenario."""
        
        # Generate user profiles for load testing
        user_profiles = []
        for i in range(concurrent_users):
            user_profiles.append({
                "user_id": f"LOAD_USER_{i:04d}",
                "user_type": random.choice([
                    "heavy_operator",    # Frequent API calls
                    "normal_operator",   # Moderate API calls
                    "light_viewer",      # Occasional API calls
                    "batch_processor"    # Bulk operations
                ]),
                "request_pattern": {
                    "requests_per_minute": random.randint(5, 60),
                    "think_time_seconds": random.randint(1, 10),
                    "session_duration_minutes": random.randint(10, duration_minutes)
                }
            })
        
        # Generate expected API endpoints and their usage patterns
        endpoint_patterns = {
            "/api/v1/inspections": {"weight": 40, "avg_response_ms": 250},
            "/api/v1/batches": {"weight": 20, "avg_response_ms": 150},
            "/api/v1/quality/metrics": {"weight": 15, "avg_response_ms": 500},
            "/api/v1/user/profile": {"weight": 10, "avg_response_ms": 100},
            "/api/v1/health": {"weight": 10, "avg_response_ms": 50},
            "/api/v1/reports": {"weight": 5, "avg_response_ms": 1000}
        }
        
        return {
            "scenario_id": f"LOAD_{uuid.uuid4().hex[:8].upper()}",
            "concurrent_users": concurrent_users,
            "duration_minutes": duration_minutes,
            "user_profiles": user_profiles,
            "endpoint_patterns": endpoint_patterns,
            "performance_targets": {
                "max_response_time_ms": 2000,
                "error_rate_threshold": 0.05,  # 5%
                "min_throughput_rps": 50,       # requests per second
                "cpu_usage_threshold": 0.80,    # 80%
                "memory_usage_threshold": 0.85  # 85%
            }
        }


# ================================================================================================
# 🏭 FACTORY UTILITIES
# ================================================================================================

class FactoryUtils:
    """Utility functions for working with test factories."""
    
    @staticmethod
    def create_production_day_scenario() -> Dict[str, Any]:
        """Create complete production day scenario with realistic data flow."""
        
        # Create shifts
        shifts = ["DAY", "NIGHT"]
        operators_per_shift = 3
        batches_per_shift = 5
        
        scenario_data = {
            "scenario_id": f"PROD_DAY_{uuid.uuid4().hex[:8].upper()}",
            "date": datetime.utcnow().date().isoformat(),
            "shifts": {}
        }
        
        for shift in shifts:
            # Create operators for this shift
            operators = [
                UserFactory(
                    roles=["operator"],
                    profile__shift_preference=shift
                ) for _ in range(operators_per_shift)
            ]
            
            # Create batches for this shift
            batches = [
                BatchFactory(
                    metadata__shift=shift,
                    metadata__line_operator=random.choice(operators)["user_id"]
                ) for _ in range(batches_per_shift)
            ]
            
            # Create inspections for each batch
            shift_inspections = []
            for batch in batches:
                chips_per_batch = random.randint(50, 200)
                for chip_num in range(chips_per_batch):
                    inspection = InspectionFactory(
                        batch_id=batch["batch_id"],
                        operator_id=random.choice(operators)["user_id"]
                    )
                    shift_inspections.append(inspection)
            
            scenario_data["shifts"][shift] = {
                "operators": operators,
                "batches": batches,
                "inspections": shift_inspections,
                "total_chips_processed": len(shift_inspections),
                "average_quality": np.mean([
                    insp["quality_metrics"]["overall_quality_score"] 
                    for insp in shift_inspections
                ])
            }
        
        return scenario_data
    
    @staticmethod
    def create_quality_crisis_scenario() -> Dict[str, Any]:
        """Create quality crisis scenario with escalating defect rates."""
        
        crisis_batch = BatchFactory(
            status="ON_HOLD",
            priority="CRITICAL"
        )
        
        # Create timeline of escalating quality issues
        crisis_events = []
        current_time = datetime.utcnow() - timedelta(hours=6)
        
        # Initial minor quality degradation
        for hour in range(6):
            defect_rate = 0.02 + (hour * 0.02)  # Escalating from 2% to 12%
            
            # Create inspections with increasing defect rate
            hourly_inspections = []
            for inspection_num in range(20):  # 20 inspections per hour
                inspection = InspectionFactory(
                    batch_id=crisis_batch["batch_id"],
                    timestamp=(current_time + timedelta(minutes=inspection_num * 3)).isoformat()
                )
                
                # Override quality metrics to simulate crisis
                if random.random() < defect_rate:
                    inspection["quality_metrics"]["defect_probability"] = random.uniform(0.7, 0.95)
                    inspection["quality_metrics"]["overall_quality_score"] = random.uniform(0.2, 0.5)
                    inspection["pass_fail_status"] = "FAIL"
                
                hourly_inspections.append(inspection)
            
            # Create quality alert if defect rate exceeds threshold
            if defect_rate > 0.05:
                alert = QualityAlertFactory(
                    batch_id=crisis_batch["batch_id"],
                    triggered_at=(current_time + timedelta(minutes=30)).isoformat(),
                    severity="HIGH" if defect_rate > 0.08 else "MEDIUM",
                    metrics__current_defect_rate=defect_rate
                )
                
                crisis_events.append({
                    "event_type": "quality_alert",
                    "timestamp": alert["triggered_at"],
                    "data": alert
                })
            
            crisis_events.append({
                "event_type": "hourly_inspection_batch",
                "timestamp": current_time.isoformat(),
                "defect_rate": defect_rate,
                "inspections": hourly_inspections
            })
            
            current_time += timedelta(hours=1)
        
        return {
            "scenario_id": f"CRISIS_{uuid.uuid4().hex[:8].upper()}",
            "crisis_batch": crisis_batch,
            "timeline": crisis_events,
            "impact_analysis": {
                "total_inspections": sum(len(event["inspections"]) for event in crisis_events if "inspections" in event),
                "final_defect_rate": defect_rate,
                "estimated_loss": random.randint(50000, 200000),  # USD
                "downtime_hours": random.uniform(2.0, 8.0)
            }
        }

# ================================================================================================
# 🧪 TEST FIXTURE SUMMARY
# ================================================================================================
"""
🏭 TEST FIXTURES SUMMARY
========================

📋 Available Factories:
   ✅ BatchFactory - Realistic production batch data
   ✅ ChipFactory - Individual chip manufacturing data
   ✅ InspectionFactory - Quality inspection results
   ✅ UserFactory - User accounts with roles and permissions
   ✅ QualityAlertFactory - Quality alerts and notifications
   ✅ ChipImageFactory - Synthetic chip images with defects

🎯 Scenario Factories:
   ✅ ComplianceScenarioFactory - FDA 21 CFR Part 11 scenarios
   ✅ PerformanceScenarioFactory - Load testing scenarios
   ✅ FactoryUtils - Complete production workflows

🚀 Usage Examples:
   batch = BatchFactory()                           # Single batch
   batches = BatchFactory.create_batch(10)          # 10 batches
   crisis = FactoryUtils.create_quality_crisis_scenario()  # Crisis scenario
   
   # Create chip image with defects
   defective_image = ChipImageFactory.create_chip_image(
       defect_type="scratch",
       noise_level=0.2
   )

📊 Realistic Data Features:
   • Manufacturing process variations
   • Compliance audit trails
   • Realistic defect distributions
   • User role hierarchies
   • Quality alert scenarios
   • Performance load patterns
"""