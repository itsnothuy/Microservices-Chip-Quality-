"""
Load testing script for Chip Quality Platform API Gateway

This script simulates realistic usage patterns for the chip quality inspection system:
- User authentication
- Inspection creation and management
- Artifact uploads
- Inference requests
- Report generation
"""

import random
import json
import base64
from locust import HttpUser, task, between
from locust.exception import RescheduleTask


class ChipQualityUser(HttpUser):
    """Simulates a user of the chip quality platform"""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between requests
    
    def on_start(self):
        """Called when a user starts"""
        self.auth_token = None
        self.current_inspection_id = None
        self.current_artifact_ids = []
        self.login()
    
    def login(self):
        """Authenticate user and get access token"""
        # Use different user types with different probabilities
        user_types = [
            ("admin", "admin123", 0.1),      # 10% admin users
            ("operator", "operator123", 0.7), # 70% operator users  
            ("viewer", "viewer123", 0.2),    # 20% viewer users
        ]
        
        username, password, _ = random.choices(
            user_types, 
            weights=[prob for _, _, prob in user_types]
        )[0]
        
        response = self.client.post("/auth/login", json={
            "username": username,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data["access_token"]
            self.client.headers.update({
                "Authorization": f"Bearer {self.auth_token}"
            })
        else:
            raise RescheduleTask("Failed to login")
    
    @task(10)
    def list_inspections(self):
        """List inspections with pagination"""
        params = {
            "limit": random.randint(10, 50),
            "status": random.choice(["pending", "processing", "completed", None])
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        self.client.get("/api/v1/inspections", params=params)
    
    @task(5)
    def create_inspection(self):
        """Create a new inspection"""
        batch_id = f"BATCH_{random.randint(1000, 9999)}"
        chip_count = random.randint(1, 20)
        chip_ids = [f"CHIP_{batch_id}_{i:03d}" for i in range(chip_count)]
        
        inspection_data = {
            "batch_id": batch_id,
            "chip_ids": chip_ids,
            "inspection_type": random.choice(["visual", "electrical", "thermal", "mechanical"]),
            "priority": random.choice(["low", "normal", "high", "critical"]),
            "metadata": {
                "facility": f"FAB_{random.randint(1, 5)}",
                "lot_number": f"LOT_{random.randint(10000, 99999)}",
                "wafer_id": f"WAFER_{random.randint(100, 999)}"
            }
        }
        
        response = self.client.post("/api/v1/inspections", json=inspection_data)
        
        if response.status_code == 201:
            self.current_inspection_id = response.json()["id"]
    
    @task(3)
    def get_inspection_details(self):
        """Get details for a specific inspection"""
        if self.current_inspection_id:
            self.client.get(f"/api/v1/inspections/{self.current_inspection_id}")
    
    @task(2)
    def upload_artifact(self):
        """Upload an artifact file"""
        if not self.current_inspection_id:
            return
            
        # Generate fake image data
        fake_image_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        
        files = {
            'file': ('test_chip_image.png', fake_image_data, 'image/png')
        }
        
        data = {
            'inspection_id': self.current_inspection_id,
            'chip_id': f"CHIP_{random.randint(1000, 9999)}",
            'artifact_type': random.choice(['image', 'measurement', 'log'])
        }
        
        response = self.client.post("/api/v1/artifacts/upload", files=files, data=data)
        
        if response.status_code == 201:
            artifact_id = response.json()["id"]
            self.current_artifact_ids.append(artifact_id)
    
    @task(3)
    def list_artifacts(self):
        """List artifacts with filtering"""
        params = {
            "limit": random.randint(10, 30),
            "artifact_type": random.choice(["image", "measurement", "log", None])
        }
        
        if self.current_inspection_id and random.random() < 0.5:
            params["inspection_id"] = self.current_inspection_id
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        self.client.get("/api/v1/artifacts", params=params)
    
    @task(2)
    def create_inference_request(self):
        """Create an inference request"""
        if not self.current_inspection_id or not self.current_artifact_ids:
            return
            
        inference_data = {
            "inspection_id": self.current_inspection_id,
            "chip_id": f"CHIP_{random.randint(1000, 9999)}",
            "artifact_ids": random.sample(
                self.current_artifact_ids, 
                min(3, len(self.current_artifact_ids))
            ),
            "model_name": random.choice([
                "defect_detection_v2", 
                "quality_classification_v1", 
                "anomaly_detection_v3"
            ]),
            "inference_config": {
                "confidence_threshold": random.uniform(0.7, 0.95),
                "batch_size": random.choice([1, 4, 8, 16])
            }
        }
        
        self.client.post("/api/v1/inference", json=inference_data)
    
    @task(1)
    def list_inference_requests(self):
        """List inference requests"""
        params = {
            "limit": random.randint(10, 30),
            "status": random.choice(["pending", "processing", "completed", "failed", None])
        }
        
        if self.current_inspection_id and random.random() < 0.5:
            params["inspection_id"] = self.current_inspection_id
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        self.client.get("/api/v1/inference", params=params)
    
    @task(1)
    def list_available_models(self):
        """List available ML models"""
        self.client.get("/api/v1/inference/models/")
    
    @task(1)
    def create_report(self):
        """Generate a report"""
        from datetime import date, timedelta
        
        end_date = date.today()
        start_date = end_date - timedelta(days=random.randint(1, 30))
        
        report_data = {
            "report_type": random.choice([
                "batch_summary", 
                "quality_trends", 
                "defect_analysis", 
                "performance_metrics"
            ]),
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "format": random.choice(["pdf", "excel", "csv"]),
            "filters": {
                "facility": f"FAB_{random.randint(1, 5)}",
                "inspection_type": random.choice(["visual", "electrical", None])
            },
            "include_charts": random.choice([True, False])
        }
        
        # Remove None values from filters
        report_data["filters"] = {
            k: v for k, v in report_data["filters"].items() if v is not None
        }
        
        self.client.post("/api/v1/reports", json=report_data)
    
    @task(2)
    def list_reports(self):
        """List generated reports"""
        params = {
            "limit": random.randint(10, 30),
            "status": random.choice(["pending", "processing", "completed", "failed", None]),
            "format": random.choice(["pdf", "excel", "csv", None])
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        self.client.get("/api/v1/reports", params=params)
    
    @task(15)
    def health_check(self):
        """Check service health"""
        self.client.get("/health/live")
    
    def on_stop(self):
        """Called when a user stops"""
        if self.auth_token:
            self.client.post("/auth/logout")


class HighVolumeUser(ChipQualityUser):
    """Simulates high-volume automated processing"""
    
    wait_time = between(0.1, 0.5)  # Much faster requests
    weight = 1  # Lower weight means fewer of these users
    
    @task(20)
    def batch_operations(self):
        """Perform batch operations rapidly"""
        # Create inspection
        self.create_inspection()
        
        # Upload multiple artifacts quickly
        for _ in range(random.randint(3, 8)):
            self.upload_artifact()
        
        # Create inference requests
        for _ in range(random.randint(2, 5)):
            self.create_inference_request()


class AdminUser(ChipQualityUser):
    """Simulates admin user with different usage patterns"""
    
    weight = 1  # Lower weight means fewer admin users
    
    def on_start(self):
        """Admin always logs in as admin"""
        self.auth_token = None
        self.current_inspection_id = None
        self.current_artifact_ids = []
        
        response = self.client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data["access_token"]
            self.client.headers.update({
                "Authorization": f"Bearer {self.auth_token}"
            })
        else:
            raise RescheduleTask("Failed to login as admin")
    
    @task(5)
    def admin_operations(self):
        """Admin-specific operations"""
        # List all reports
        self.client.get("/api/v1/reports", params={"limit": 100})
        
        # Check system metrics
        self.client.get("/metrics")
        
        # Generate comprehensive reports
        from datetime import date, timedelta
        
        report_data = {
            "report_type": "system_overview",
            "date_range": {
                "start_date": (date.today() - timedelta(days=7)).isoformat(),
                "end_date": date.today().isoformat()
            },
            "format": "pdf",
            "include_charts": True
        }
        
        self.client.post("/api/v1/reports", json=report_data)