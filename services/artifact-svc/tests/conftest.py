"""Pytest configuration for artifact service tests"""

import pytest
from httpx import AsyncClient


@pytest.fixture
def anyio_backend():
    """Configure async backend for pytest-asyncio"""
    return "asyncio"
