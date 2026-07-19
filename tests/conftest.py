"""Pytest configuration and shared fixtures."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        'OPENAI_API_KEY': 'test_api_key_12345',
        'SERPAPI_API_KEY': 'test_serpapi_key_67890',
        'FROM_EMAIL': 'test@example.com',
        'TO_EMAIL': 'recipient@example.com',
        'EMAIL_SUBJECT': 'Test Travel Information',
        'SENDGRID_API_KEY': 'test_sendgrid_key'
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars


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
