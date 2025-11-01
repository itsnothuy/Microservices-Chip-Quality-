"""Event streaming infrastructure for Chip Quality Platform.

This module provides comprehensive event streaming capabilities using Apache Kafka,
including event producers, consumers, stream processors, and schema management.
"""

from events.producers.base_producer import BaseEventProducer
from events.consumers.base_consumer import BaseEventConsumer

__all__ = [
    "BaseEventProducer",
    "BaseEventConsumer",
]
