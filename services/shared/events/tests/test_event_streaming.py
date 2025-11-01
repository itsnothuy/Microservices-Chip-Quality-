"""Unit tests for event streaming infrastructure."""

import pytest
import json
from pathlib import Path
from events.utils.serialization import AvroSerializer, SchemaRegistrySerializer


class TestAvroSerializer:
    """Test Avro serialization utilities."""
    
    @pytest.fixture
    def inspection_schema(self):
        """Load inspection schema for testing."""
        schema_path = Path(__file__).parent.parent / "schemas" / "inspection.avsc"
        with open(schema_path, "r") as f:
            return json.load(f)
    
    @pytest.fixture
    def serializer(self, inspection_schema):
        """Create Avro serializer."""
        return AvroSerializer(inspection_schema)
    
    def test_serialize_deserialize(self, serializer):
        """Test serialization and deserialization roundtrip."""
        event_data = {
            "event_id": "test-123",
            "event_type": "INSPECTION_CREATED",
            "timestamp": 1699000000000,
            "inspection_id": "INS-001",
            "batch_id": "BATCH-001",
            "chip_id": "CHIP-001",
            "inspection_type": "visual",
            "status": "pending",
            "quality_score": None,
            "defects": [],
            "metadata": {"test": "data"}
        }
        
        # Serialize
        serialized = serializer.serialize(event_data)
        assert isinstance(serialized, bytes)
        assert len(serialized) > 0
        
        # Deserialize
        deserialized = serializer.deserialize(serialized)
        assert deserialized["event_id"] == event_data["event_id"]
        assert deserialized["event_type"] == event_data["event_type"]
        assert deserialized["inspection_id"] == event_data["inspection_id"]
    
    def test_validate_valid_data(self, serializer):
        """Test validation with valid data."""
        event_data = {
            "event_id": "test-123",
            "event_type": "INSPECTION_CREATED",
            "timestamp": 1699000000000,
            "inspection_id": "INS-001",
            "batch_id": "BATCH-001",
            "chip_id": "CHIP-001",
            "inspection_type": "visual",
            "status": "pending",
            "quality_score": None,
            "defects": [],
            "metadata": {}
        }
        
        assert serializer.validate(event_data) is True
    
    def test_validate_invalid_data(self, serializer):
        """Test validation with invalid data."""
        # Missing required fields
        event_data = {
            "event_id": "test-123",
            "event_type": "INSPECTION_CREATED",
        }
        
        assert serializer.validate(event_data) is False
    
    def test_serialize_with_defects(self, serializer):
        """Test serialization with defects array."""
        event_data = {
            "event_id": "test-123",
            "event_type": "DEFECT_DETECTED",
            "timestamp": 1699000000000,
            "inspection_id": "INS-001",
            "batch_id": "BATCH-001",
            "chip_id": "CHIP-001",
            "inspection_type": "visual",
            "status": "defect_detected",
            "quality_score": 0.75,
            "defects": [
                {
                    "defect_type": "scratch",
                    "severity": "minor",
                    "confidence": 0.95,
                    "location": "corner"
                }
            ],
            "metadata": {}
        }
        
        # Serialize and deserialize
        serialized = serializer.serialize(event_data)
        deserialized = serializer.deserialize(serialized)
        
        assert len(deserialized["defects"]) == 1
        assert deserialized["defects"][0]["defect_type"] == "scratch"


class TestSchemaRegistrySerializer:
    """Test Schema Registry serializer."""
    
    @pytest.fixture
    def inspection_schema(self):
        """Load inspection schema for testing."""
        schema_path = Path(__file__).parent.parent / "schemas" / "inspection.avsc"
        with open(schema_path, "r") as f:
            return json.load(f)
    
    @pytest.fixture
    def serializer(self, inspection_schema):
        """Create Schema Registry serializer."""
        return SchemaRegistrySerializer(schema_id=1, schema=inspection_schema)
    
    def test_serialize_with_schema_id(self, serializer):
        """Test serialization with schema ID prefix."""
        event_data = {
            "event_id": "test-123",
            "event_type": "INSPECTION_CREATED",
            "timestamp": 1699000000000,
            "inspection_id": "INS-001",
            "batch_id": "BATCH-001",
            "chip_id": "CHIP-001",
            "inspection_type": "visual",
            "status": "pending",
            "quality_score": None,
            "defects": [],
            "metadata": {}
        }
        
        serialized = serializer.serialize(event_data)
        
        # Check magic byte
        assert serialized[0] == 0
        
        # Check schema ID
        schema_id = int.from_bytes(serialized[1:5], byteorder="big")
        assert schema_id == 1
    
    def test_deserialize_with_schema_id(self, serializer):
        """Test deserialization with schema ID prefix."""
        event_data = {
            "event_id": "test-123",
            "event_type": "INSPECTION_CREATED",
            "timestamp": 1699000000000,
            "inspection_id": "INS-001",
            "batch_id": "BATCH-001",
            "chip_id": "CHIP-001",
            "inspection_type": "visual",
            "status": "pending",
            "quality_score": None,
            "defects": [],
            "metadata": {}
        }
        
        # Serialize and deserialize
        serialized = serializer.serialize(event_data)
        deserialized = serializer.deserialize(serialized)
        
        assert deserialized["event_id"] == event_data["event_id"]
        assert deserialized["inspection_id"] == event_data["inspection_id"]


class TestKafkaConfig:
    """Test Kafka configuration."""
    
    def test_config_from_env(self, monkeypatch):
        """Test configuration from environment variables."""
        from events.utils.kafka_client import KafkaConfig
        
        monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        monkeypatch.setenv("SCHEMA_REGISTRY_URL", "http://schema-registry:8081")
        
        config = KafkaConfig.from_env()
        
        assert config.bootstrap_servers == "kafka:9092"
        assert config.schema_registry_url == "http://schema-registry:8081"
    
    def test_producer_config(self):
        """Test producer configuration generation."""
        from events.utils.kafka_client import KafkaConfig
        
        config = KafkaConfig(bootstrap_servers="localhost:9092")
        producer_config = config.get_producer_config()
        
        assert producer_config["bootstrap_servers"] == "localhost:9092"
        assert producer_config["acks"] == "all"
        assert producer_config["enable_idempotence"] is True
    
    def test_consumer_config(self):
        """Test consumer configuration generation."""
        from events.utils.kafka_client import KafkaConfig
        
        config = KafkaConfig(
            bootstrap_servers="localhost:9092",
            group_id="test-group"
        )
        consumer_config = config.get_consumer_config()
        
        assert consumer_config["bootstrap_servers"] == "localhost:9092"
        assert consumer_config["group_id"] == "test-group"
        assert consumer_config["enable_auto_commit"] is False
