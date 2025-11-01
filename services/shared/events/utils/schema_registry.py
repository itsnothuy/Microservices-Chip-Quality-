"""Schema Registry integration for Avro schema management.

This module provides integration with Confluent Schema Registry for
schema evolution and compatibility checking.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)


class SchemaRegistry:
    """Schema Registry client for Avro schema management."""
    
    def __init__(self, url: Optional[str] = None):
        """Initialize Schema Registry client.
        
        Args:
            url: Schema Registry URL. If None, loads from environment.
        """
        self.url = url or os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")
        self.client = httpx.AsyncClient(base_url=self.url)
        self.logger = logger.bind(schema_registry_url=self.url)
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
    
    async def register_schema(
        self, 
        subject: str, 
        schema: Dict[str, Any]
    ) -> int:
        """Register a schema with the Schema Registry.
        
        Args:
            subject: Subject name (typically topic-value or topic-key)
            schema: Avro schema as dictionary
            
        Returns:
            Schema ID assigned by the registry
        """
        try:
            schema_str = json.dumps(schema)
            response = await self.client.post(
                f"/subjects/{subject}/versions",
                json={"schema": schema_str}
            )
            response.raise_for_status()
            
            schema_id = response.json()["id"]
            self.logger.info(
                "schema.registered",
                subject=subject,
                schema_id=schema_id
            )
            return schema_id
        except Exception as e:
            self.logger.error(
                "schema.register.failed",
                subject=subject,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def get_schema(self, schema_id: int) -> Dict[str, Any]:
        """Get schema by ID.
        
        Args:
            schema_id: Schema ID
            
        Returns:
            Schema definition as dictionary
        """
        if schema_id in self._schema_cache:
            return self._schema_cache[schema_id]
        
        try:
            response = await self.client.get(f"/schemas/ids/{schema_id}")
            response.raise_for_status()
            
            schema_str = response.json()["schema"]
            schema = json.loads(schema_str)
            self._schema_cache[schema_id] = schema
            return schema
        except Exception as e:
            self.logger.error(
                "schema.get.failed",
                schema_id=schema_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def get_latest_schema(self, subject: str) -> tuple[int, Dict[str, Any]]:
        """Get latest schema for a subject.
        
        Args:
            subject: Subject name
            
        Returns:
            Tuple of (schema_id, schema)
        """
        try:
            response = await self.client.get(
                f"/subjects/{subject}/versions/latest"
            )
            response.raise_for_status()
            
            data = response.json()
            schema_id = data["id"]
            schema = json.loads(data["schema"])
            
            self._schema_cache[schema_id] = schema
            return schema_id, schema
        except Exception as e:
            self.logger.error(
                "schema.get_latest.failed",
                subject=subject,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def check_compatibility(
        self, 
        subject: str, 
        schema: Dict[str, Any]
    ) -> bool:
        """Check if schema is compatible with existing versions.
        
        Args:
            subject: Subject name
            schema: Schema to check
            
        Returns:
            True if compatible, False otherwise
        """
        try:
            schema_str = json.dumps(schema)
            response = await self.client.post(
                f"/compatibility/subjects/{subject}/versions/latest",
                json={"schema": schema_str}
            )
            response.raise_for_status()
            
            is_compatible = response.json().get("is_compatible", False)
            self.logger.info(
                "schema.compatibility_check",
                subject=subject,
                compatible=is_compatible
            )
            return is_compatible
        except Exception as e:
            self.logger.error(
                "schema.compatibility_check.failed",
                subject=subject,
                error=str(e),
                exc_info=True
            )
            return False
    
    async def load_schema_from_file(self, schema_path: Path) -> Dict[str, Any]:
        """Load Avro schema from file.
        
        Args:
            schema_path: Path to .avsc schema file
            
        Returns:
            Schema as dictionary
        """
        try:
            with open(schema_path, "r") as f:
                schema = json.load(f)
            
            self.logger.info(
                "schema.loaded_from_file",
                schema_path=str(schema_path),
                schema_name=schema.get("name")
            )
            return schema
        except Exception as e:
            self.logger.error(
                "schema.load_from_file.failed",
                schema_path=str(schema_path),
                error=str(e),
                exc_info=True
            )
            raise
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()


async def register_all_schemas(schema_dir: Path) -> Dict[str, int]:
    """Register all schemas from a directory.
    
    Args:
        schema_dir: Directory containing .avsc schema files
        
    Returns:
        Dictionary mapping schema names to schema IDs
    """
    registry = SchemaRegistry()
    schema_ids = {}
    
    try:
        for schema_file in schema_dir.glob("*.avsc"):
            schema = await registry.load_schema_from_file(schema_file)
            schema_name = schema.get("name")
            subject = f"{schema_name.lower()}-value"
            
            schema_id = await registry.register_schema(subject, schema)
            schema_ids[schema_name] = schema_id
        
        logger.info(
            "schemas.registered_all",
            count=len(schema_ids),
            schemas=list(schema_ids.keys())
        )
        return schema_ids
    finally:
        await registry.close()
