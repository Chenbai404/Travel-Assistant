"""Pytest configuration and shared fixtures."""

import os
import socket
import sys
import pytest
from unittest.mock import patch


TEST_ENV_VARS = {
    'OPENAI_API_KEY': 'offline-test-key',
    'SERPAPI_API_KEY': 'offline-serpapi-key',
    'FROM_EMAIL': 'test@example.com',
    'TO_EMAIL': 'recipient@example.com',
    'EMAIL_SUBJECT': 'Test Travel Information',
    'SENDGRID_API_KEY': 'offline-sendgrid-key',
    'LANGCHAIN_TRACING_V2': 'false',
    'LANGSMITH_TRACING': 'false',
}

# Set safe values before application modules import and call load_dotenv().
os.environ.update(TEST_ENV_VARS)

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, TEST_ENV_VARS):
        yield TEST_ENV_VARS


@pytest.fixture(autouse=True)
def isolate_external_state(tmp_path, monkeypatch):
    """Keep every test offline and isolate the global preference store."""

    for name, value in TEST_ENV_VARS.items():
        monkeypatch.setenv(name, value)

    def reject_network(*_args, **_kwargs):
        raise RuntimeError("Network access is disabled in the offline test suite")

    monkeypatch.setattr(socket, 'create_connection', reject_network)
    monkeypatch.setattr(socket.socket, 'connect', reject_network)

    from agents.memory import preference_memory

    memory = preference_memory.PreferenceMemory(
        storage_dir=str(tmp_path / "memory")
    )
    monkeypatch.setattr(preference_memory, '_memory_instance', memory)
    yield


@pytest.fixture
def sample_travel_preferences():
    """Sample travel preferences for testing."""
    return {
        'destination': 'Tokyo',
        'start_date': '2026-10-15',
        'end_date': '2026-10-20',
        'budget': {'amount': 2000, 'currency': 'USD'},
        'interests': ['food', 'technology', 'culture'],
        'companions': ['solo'],
        'constraints': [],
        'accessibility_needs': None,
        'accommodation_type': 'hotel',
        'transportation_preference': 'public transit',
        'meal_preferences': []
    }


@pytest.fixture
def sample_flight_data():
    """Sample flight data for testing."""
    return [
        {
            'airline': 'American Airlines',
            'departure': {'airport': 'JFK', 'time': '10:25 AM'},
            'arrival': {'airport': 'LAX', 'time': '1:25 PM'},
            'duration': '5 hours',
            'price': 350
        },
        {
            'airline': 'Delta',
            'departure': {'airport': 'JFK', 'time': '2:00 PM'},
            'arrival': {'airport': 'LAX', 'time': '5:30 PM'},
            'duration': '5 hours 30 minutes',
            'price': 380
        }
    ]


@pytest.fixture
def sample_hotel_data():
    """Sample hotel data for testing."""
    return [
        {
            'name': 'Grand Hotel',
            'description': 'Luxury hotel in city center',
            'rate_per_night': {'extracted': 250, 'currency': 'USD'},
            'total_rate': {'extracted': 1750, 'currency': 'USD'},
            'rating': 4.5,
            'reviews': 500,
            'location': 'Downtown'
        },
        {
            'name': 'City Inn',
            'description': 'Budget-friendly accommodation',
            'rate_per_night': {'extracted': 120, 'currency': 'USD'},
            'total_rate': {'extracted': 840, 'currency': 'USD'},
            'rating': 4.0,
            'reviews': 300,
            'location': 'Midtown'
        }
    ]
