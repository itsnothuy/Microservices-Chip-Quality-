"""Avro serialization utilities for event data.

This module provides utilities for serializing and deserializing event data
using Avro format with schema validation.
"""

import io
from typing import Dict, Any, Optional

import fastavro
import structlog

logger = structlog.get_logger(__name__)


class AvroSerializer:
    """Avro serializer for event data."""
    
    def __init__(self, schema: Dict[str, Any]):
        """Initialize Avro serializer.
        
        Args:
            schema: Avro schema definition
        """
        self.schema = schema
        self.parsed_schema = fastavro.parse_schema(schema)
        self.logger = logger.bind(
            schema_name=schema.get("name"),
            schema_namespace=schema.get("namespace")
        )
    
    def serialize(self, data: Dict[str, Any]) -> bytes:
        """Serialize data to Avro format.
        
        Args:
            data: Data dictionary to serialize
            
        Returns:
            Serialized bytes
        """
        try:
            output = io.BytesIO()
            fastavro.schemaless_writer(output, self.parsed_schema, data)
            serialized = output.getvalue()
            
            self.logger.debug(
                "avro.serialized",
                data_size=len(serialized)
            )
            return serialized
        except Exception as e:
            self.logger.error(
                "avro.serialize.failed",
                error=str(e),
                data_keys=list(data.keys()),
                exc_info=True
            )
            raise
    
    def deserialize(self, data: bytes) -> Dict[str, Any]:
        """Deserialize Avro data.
        
        Args:
            data: Serialized bytes
            
        Returns:
            Deserialized data dictionary
        """
        try:
            input_stream = io.BytesIO(data)
            deserialized = fastavro.schemaless_reader(
                input_stream, 
                self.parsed_schema
            )
            
            self.logger.debug(
                "avro.deserialized",
                data_size=len(data)
            )
            return deserialized
        except Exception as e:
            self.logger.error(
                "avro.deserialize.failed",
                error=str(e),
                data_size=len(data),
                exc_info=True
            )
            raise
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate data against schema.
        
        Args:
            data: Data dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            fastavro.validate(data, self.parsed_schema)
            return True
        except Exception as e:
            self.logger.warning(
                "avro.validation.failed",
                error=str(e),
                data_keys=list(data.keys())
            )
            return False


class SchemaRegistrySerializer:
    """Serializer that integrates with Schema Registry.
    
    This serializer prepends the schema ID to the serialized data
    for use with Confluent Schema Registry.
    """
    
    def __init__(self, schema_id: int, schema: Dict[str, Any]):
        """Initialize Schema Registry serializer.
        
        Args:
            schema_id: Schema ID from registry
            schema: Avro schema definition
        """
        self.schema_id = schema_id
        self.avro_serializer = AvroSerializer(schema)
        self.logger = logger.bind(schema_id=schema_id)
    
    def serialize(self, data: Dict[str, Any]) -> bytes:
        """Serialize data with schema ID prefix.
        
        The format is:
        - Byte 0: Magic byte (0)
        - Bytes 1-4: Schema ID (big-endian int)
        - Bytes 5+: Avro serialized data
        
        Args:
            data: Data dictionary to serialize
            
        Returns:
            Serialized bytes with schema ID prefix
        """
        try:
            # Serialize with Avro
            avro_data = self.avro_serializer.serialize(data)
            
            # Prepend magic byte and schema ID
            output = io.BytesIO()
            output.write(b"\x00")  # Magic byte
            output.write(self.schema_id.to_bytes(4, byteorder="big"))
            output.write(avro_data)
            
            serialized = output.getvalue()
            self.logger.debug(
                "schema_registry.serialized",
                data_size=len(serialized)
            )
            return serialized
        except Exception as e:
            self.logger.error(
                "schema_registry.serialize.failed",
                error=str(e),
                exc_info=True
            )
            raise
    
    def deserialize(self, data: bytes) -> Dict[str, Any]:
        """Deserialize data with schema ID prefix.
        
        Args:
            data: Serialized bytes with schema ID prefix
            
        Returns:
            Deserialized data dictionary
        """
        try:
            # Verify magic byte
            if data[0] != 0:
                raise ValueError(f"Invalid magic byte: {data[0]}")
            
            # Extract schema ID
            schema_id = int.from_bytes(data[1:5], byteorder="big")
            if schema_id != self.schema_id:
                self.logger.warning(
                    "schema_registry.schema_id_mismatch",
                    expected=self.schema_id,
                    actual=schema_id
                )
            
            # Deserialize Avro data
            avro_data = data[5:]
            deserialized = self.avro_serializer.deserialize(avro_data)
            
            self.logger.debug(
                "schema_registry.deserialized",
                data_size=len(data)
            )
            return deserialized
        except Exception as e:
            self.logger.error(
                "schema_registry.deserialize.failed",
                error=str(e),
                exc_info=True
            )
            raise


def create_serializer(
    schema: Dict[str, Any],
    schema_id: Optional[int] = None
) -> AvroSerializer:
    """Create appropriate serializer based on schema ID availability.
    
    Args:
        schema: Avro schema definition
        schema_id: Optional schema ID for Schema Registry integration
        
    Returns:
        Serializer instance
    """
    if schema_id is not None:
        return SchemaRegistrySerializer(schema_id, schema)
    return AvroSerializer(schema)
