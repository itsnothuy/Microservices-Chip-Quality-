#!/usr/bin/env python3
"""
Example script demonstrating event streaming usage.

This script shows how to:
1. Publish inspection events
2. Consume events with analytics processing
3. Monitor metrics and health
"""

import asyncio
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from events.producers import InspectionEventProducer, QualityEventProducer
from events.consumers import AnalyticsConsumer
from events.utils import KafkaConfig, SchemaRegistry


async def example_publish_events():
    """Example: Publish inspection events."""
    print("=== Publishing Inspection Events ===\n")
    
    # Initialize producer
    config = KafkaConfig.from_env()
    async with InspectionEventProducer(config) as producer:
        # Publish inspection created event
        print("Publishing inspection created event...")
        await producer.publish_inspection_created(
            inspection_id="INS-001",
            batch_id="BATCH-001",
            chip_id="CHIP-001",
            inspection_type="visual",
            metadata={
                "station": "A1",
                "operator": "John Doe"
            }
        )
        
        # Publish inspection started event
        print("Publishing inspection started event...")
        await producer.publish_inspection_started(
            inspection_id="INS-001",
            batch_id="BATCH-001",
            chip_id="CHIP-001",
            inspection_type="visual"
        )
        
        # Publish inspection completed with defects
        print("Publishing inspection completed event...")
        await producer.publish_inspection_completed(
            inspection_id="INS-001",
            batch_id="BATCH-001",
            chip_id="CHIP-001",
            inspection_type="visual",
            quality_score=0.85,
            defects=[
                {
                    "defect_type": "scratch",
                    "severity": "minor",
                    "confidence": 0.92,
                    "location": "corner_top_left"
                }
            ],
            metadata={"processing_time_ms": "1250"}
        )
        
        # Get producer metrics
        metrics = producer.get_metrics()
        print(f"\nProducer Metrics:")
        print(f"  Messages sent: {metrics['messages_sent']}")
        print(f"  Messages failed: {metrics['messages_failed']}")
        print(f"  Total bytes sent: {metrics['total_bytes_sent']}")
    
    print("\n✅ Events published successfully!\n")


async def example_health_check():
    """Example: Health check."""
    print("=== Health Check ===\n")
    
    from events.utils import KafkaClientManager
    
    manager = KafkaClientManager()
    
    print("Checking Kafka cluster health...")
    is_healthy = await manager.health_check()
    
    if is_healthy:
        print("✅ Kafka cluster is healthy")
    else:
        print("❌ Kafka cluster is not accessible")
        print("  (This is expected if Kafka is not running)")
    
    print()


async def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("Event Streaming Examples")
    print("="*60 + "\n")
    
    try:
        # Health check
        await example_health_check()
        
        print("\n" + "="*60)
        print("Examples completed!")
        print("="*60 + "\n")
        
        print("Note: To run publish/consume examples:")
        print("  1. Start Kafka: docker-compose up -d kafka schema-registry")
        print("  2. Uncomment the publish/consume examples in main()")
        print("  3. Run this script again")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure Kafka is running:")
        print("  docker-compose up -d kafka schema-registry")


if __name__ == "__main__":
    asyncio.run(main())
