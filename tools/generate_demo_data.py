#!/usr/bin/env python3
"""
Demo data generator for Chip Quality Platform

Generates realistic demo data for development and testing:
- Manufacturing batches
- Chip inspections  
- Artifacts and images
- ML inference results
- Quality reports
"""

import asyncio
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

import asyncpg
import aiofiles
import httpx
from faker import Faker


fake = Faker()


class DemoDataGenerator:
    """Generates realistic demo data for the platform"""
    
    def __init__(self, database_url: str, api_base_url: str):
        self.database_url = database_url
        self.api_base_url = api_base_url
        self.facilities = ["FAB_1", "FAB_2", "FAB_3", "FAB_4", "FAB_5"]
        self.inspection_types = ["visual", "electrical", "thermal", "mechanical"]
        self.defect_types = [
            "scratches", "particles", "discoloration", "cracks", 
            "contamination", "alignment_issues", "dimension_errors"
        ]
        
    async def generate_all_data(self, num_batches: int = 50):
        """Generate complete demo dataset"""
        print(f"🚀 Generating demo data for {num_batches} batches...")
        
        # Connect to database
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # Generate batches and inspections
            batches = await self.generate_batches(conn, num_batches)
            
            # Generate inspections for each batch
            all_inspections = []
            for batch in batches:
                inspections = await self.generate_inspections_for_batch(conn, batch)
                all_inspections.extend(inspections)
            
            # Generate artifacts for inspections
            for inspection in all_inspections:
                await self.generate_artifacts_for_inspection(conn, inspection)
            
            # Generate inference results
            for inspection in all_inspections:
                await self.generate_inference_results(conn, inspection)
            
            print(f"✅ Generated {len(batches)} batches with {len(all_inspections)} inspections")
            
        finally:
            await conn.close()
    
    async def generate_batches(self, conn: asyncpg.Connection, count: int) -> List[Dict[str, Any]]:
        """Generate manufacturing batches"""
        batches = []
        
        for i in range(count):
            batch_id = f"BATCH_{fake.date_this_year().strftime('%Y%m%d')}_{i:04d}"
            
            batch = {
                "id": batch_id,
                "facility": random.choice(self.facilities),
                "lot_number": f"LOT_{fake.random_int(10000, 99999)}",
                "wafer_id": f"WAFER_{fake.random_int(100, 999)}",
                "chip_count": random.randint(50, 500),
                "created_at": fake.date_time_this_year(),
                "process_parameters": {
                    "temperature": round(random.uniform(20.0, 85.0), 1),
                    "humidity": round(random.uniform(30.0, 70.0), 1),
                    "pressure": round(random.uniform(0.9, 1.1), 3),
                    "gas_flow_rate": round(random.uniform(10.0, 50.0), 1)
                }
            }
            
            # Insert batch into database
            await conn.execute("""
                INSERT INTO batches (id, facility, lot_number, wafer_id, chip_count, created_at, process_parameters)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, batch["id"], batch["facility"], batch["lot_number"], 
                batch["wafer_id"], batch["chip_count"], batch["created_at"], 
                json.dumps(batch["process_parameters"]))
            
            batches.append(batch)
        
        return batches
    
    async def generate_inspections_for_batch(
        self, 
        conn: asyncpg.Connection, 
        batch: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate inspections for a batch"""
        inspections = []
        
        # Each batch can have multiple inspection types
        num_inspections = random.randint(1, 3)
        
        for i in range(num_inspections):
            inspection_id = str(uuid.uuid4())
            
            # Generate chip IDs for this inspection
            chips_to_inspect = random.randint(
                min(10, batch["chip_count"]), 
                min(50, batch["chip_count"])
            )
            chip_ids = [
                f"CHIP_{batch['id']}_{j:03d}" 
                for j in random.sample(range(batch["chip_count"]), chips_to_inspect)
            ]
            
            inspection = {
                "id": inspection_id,
                "batch_id": batch["id"],
                "chip_ids": chip_ids,
                "inspection_type": random.choice(self.inspection_types),
                "status": random.choices(
                    ["completed", "processing", "failed", "pending"],
                    weights=[0.7, 0.15, 0.1, 0.05]
                )[0],
                "priority": random.choices(
                    ["normal", "high", "low", "critical"],
                    weights=[0.6, 0.25, 0.1, 0.05]
                )[0],
                "created_at": batch["created_at"] + timedelta(
                    hours=random.randint(1, 24)
                ),
                "metadata": {
                    "operator": fake.name(),
                    "equipment": f"INSP_{random.randint(1, 10):02d}",
                    "shift": random.choice(["day", "night", "weekend"])
                }
            }
            
            # Insert inspection
            await conn.execute("""
                INSERT INTO inspections 
                (id, batch_id, chip_ids, inspection_type, status, priority, created_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, inspection["id"], inspection["batch_id"], inspection["chip_ids"],
                inspection["inspection_type"], inspection["status"], inspection["priority"],
                inspection["created_at"], json.dumps(inspection["metadata"]))
            
            inspections.append(inspection)
        
        return inspections
    
    async def generate_artifacts_for_inspection(
        self, 
        conn: asyncpg.Connection, 
        inspection: Dict[str, Any]
    ):
        """Generate artifacts for an inspection"""
        
        # Generate 1-5 artifacts per chip
        for chip_id in inspection["chip_ids"][:10]:  # Limit for demo
            num_artifacts = random.randint(1, 5)
            
            for i in range(num_artifacts):
                artifact_id = str(uuid.uuid4())
                
                artifact_type = random.choice(["image", "measurement", "log"])
                
                if artifact_type == "image":
                    filename = f"{chip_id}_image_{i}.png"
                    content_type = "image/png"
                    size_bytes = random.randint(50000, 500000)
                elif artifact_type == "measurement":
                    filename = f"{chip_id}_measurement_{i}.json"
                    content_type = "application/json"
                    size_bytes = random.randint(1000, 10000)
                else:  # log
                    filename = f"{chip_id}_log_{i}.txt"
                    content_type = "text/plain"
                    size_bytes = random.randint(500, 5000)
                
                storage_path = f"artifacts/{inspection['batch_id']}/{chip_id}/{filename}"
                
                artifact = {
                    "id": artifact_id,
                    "inspection_id": inspection["id"],
                    "chip_id": chip_id,
                    "artifact_type": artifact_type,
                    "filename": filename,
                    "content_type": content_type,
                    "size_bytes": size_bytes,
                    "storage_path": storage_path,
                    "created_at": inspection["created_at"] + timedelta(
                        minutes=random.randint(1, 60)
                    ),
                    "metadata": {
                        "resolution": "1920x1080" if artifact_type == "image" else None,
                        "camera_id": f"CAM_{random.randint(1, 8):02d}" if artifact_type == "image" else None,
                        "measurement_tool": f"TOOL_{random.randint(1, 5):02d}" if artifact_type == "measurement" else None
                    }
                }
                
                # Insert artifact
                await conn.execute("""
                    INSERT INTO artifacts 
                    (id, inspection_id, chip_id, artifact_type, filename, content_type, 
                     size_bytes, storage_path, created_at, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, artifact["id"], artifact["inspection_id"], artifact["chip_id"],
                    artifact["artifact_type"], artifact["filename"], artifact["content_type"],
                    artifact["size_bytes"], artifact["storage_path"], artifact["created_at"],
                    json.dumps(artifact["metadata"]))
    
    async def generate_inference_results(
        self, 
        conn: asyncpg.Connection, 
        inspection: Dict[str, Any]
    ):
        """Generate ML inference results"""
        
        if inspection["status"] != "completed":
            return
        
        # Generate inference results for some chips
        chips_with_inference = random.sample(
            inspection["chip_ids"], 
            min(5, len(inspection["chip_ids"]))
        )
        
        for chip_id in chips_with_inference:
            inference_id = str(uuid.uuid4())
            
            # Simulate different models
            model_name = random.choice([
                "defect_detection_v2", 
                "quality_classification_v1", 
                "anomaly_detection_v3"
            ])
            
            # Generate realistic predictions based on model type
            if "defect" in model_name:
                predictions = {
                    "defects_detected": random.choice([True, False]),
                    "defect_types": random.sample(self.defect_types, random.randint(0, 3)),
                    "defect_locations": [
                        {
                            "x": random.randint(0, 1920),
                            "y": random.randint(0, 1080),
                            "width": random.randint(10, 100),
                            "height": random.randint(10, 100),
                            "confidence": round(random.uniform(0.7, 0.99), 3)
                        }
                        for _ in range(random.randint(0, 5))
                    ]
                }
                confidence_score = round(random.uniform(0.8, 0.99), 3)
            elif "quality" in model_name:
                predictions = {
                    "quality_grade": random.choice(["A", "B", "C", "D", "F"]),
                    "pass_fail": random.choice([True, False]),
                    "quality_score": round(random.uniform(0.6, 1.0), 3)
                }
                confidence_score = round(random.uniform(0.75, 0.95), 3)
            else:  # anomaly
                predictions = {
                    "is_anomaly": random.choice([True, False]),
                    "anomaly_score": round(random.uniform(0.0, 1.0), 3),
                    "anomaly_type": random.choice(["process", "material", "equipment", "environmental"])
                }
                confidence_score = round(random.uniform(0.7, 0.98), 3)
            
            inference = {
                "id": inference_id,
                "inspection_id": inspection["id"],
                "chip_id": chip_id,
                "model_name": model_name,
                "model_version": "1.0.0",
                "status": "completed",
                "confidence_score": confidence_score,
                "predictions": predictions,
                "created_at": inspection["created_at"] + timedelta(
                    hours=random.randint(2, 6)
                ),
                "completed_at": inspection["created_at"] + timedelta(
                    hours=random.randint(2, 6),
                    minutes=random.randint(1, 30)
                ),
                "metadata": {
                    "inference_time_ms": random.randint(50, 500),
                    "gpu_utilization": round(random.uniform(0.3, 0.9), 2),
                    "batch_size": random.choice([1, 4, 8, 16])
                }
            }
            
            # Insert inference result
            await conn.execute("""
                INSERT INTO inference_results 
                (id, inspection_id, chip_id, model_name, model_version, status, 
                 confidence_score, predictions, created_at, completed_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, inference["id"], inference["inspection_id"], inference["chip_id"],
                inference["model_name"], inference["model_version"], inference["status"],
                inference["confidence_score"], json.dumps(inference["predictions"]),
                inference["created_at"], inference["completed_at"], 
                json.dumps(inference["metadata"]))
    
    async def create_database_schema(self, conn: asyncpg.Connection):
        """Create demo database schema"""
        schema_sql = """
        -- Batches table
        CREATE TABLE IF NOT EXISTS batches (
            id VARCHAR PRIMARY KEY,
            facility VARCHAR NOT NULL,
            lot_number VARCHAR NOT NULL,
            wafer_id VARCHAR NOT NULL,
            chip_count INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL,
            process_parameters JSONB
        );
        
        -- Inspections table
        CREATE TABLE IF NOT EXISTS inspections (
            id UUID PRIMARY KEY,
            batch_id VARCHAR REFERENCES batches(id),
            chip_ids TEXT[] NOT NULL,
            inspection_type VARCHAR NOT NULL,
            status VARCHAR NOT NULL,
            priority VARCHAR NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT NOW(),
            metadata JSONB
        );
        
        -- Artifacts table
        CREATE TABLE IF NOT EXISTS artifacts (
            id UUID PRIMARY KEY,
            inspection_id UUID REFERENCES inspections(id),
            chip_id VARCHAR NOT NULL,
            artifact_type VARCHAR NOT NULL,
            filename VARCHAR NOT NULL,
            content_type VARCHAR NOT NULL,
            size_bytes BIGINT NOT NULL,
            storage_path VARCHAR NOT NULL,
            created_at TIMESTAMP NOT NULL,
            metadata JSONB
        );
        
        -- Inference results table
        CREATE TABLE IF NOT EXISTS inference_results (
            id UUID PRIMARY KEY,
            inspection_id UUID REFERENCES inspections(id),
            chip_id VARCHAR NOT NULL,
            model_name VARCHAR NOT NULL,
            model_version VARCHAR NOT NULL,
            status VARCHAR NOT NULL,
            confidence_score FLOAT,
            predictions JSONB,
            created_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            metadata JSONB
        );
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_inspections_batch_id ON inspections(batch_id);
        CREATE INDEX IF NOT EXISTS idx_inspections_status ON inspections(status);
        CREATE INDEX IF NOT EXISTS idx_artifacts_inspection_id ON artifacts(inspection_id);
        CREATE INDEX IF NOT EXISTS idx_inference_inspection_id ON inference_results(inspection_id);
        """
        
        await conn.execute(schema_sql)
        print("✅ Database schema created")


async def main():
    """Main entry point"""
    import os
    
    # Configuration
    database_url = os.getenv(
        "DATABASE_URL", 
        "postgresql://chip_quality_user:password@localhost:5432/chip_quality"
    )
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    generator = DemoDataGenerator(database_url, api_base_url)
    
    # Connect and create schema
    conn = await asyncpg.connect(database_url)
    try:
        await generator.create_database_schema(conn)
    finally:
        await conn.close()
    
    # Generate demo data
    await generator.generate_all_data(num_batches=100)
    
    print("🎉 Demo data generation complete!")
    print(f"   📊 Database: {database_url}")
    print(f"   🌐 API: {api_base_url}")


if __name__ == "__main__":
    asyncio.run(main())