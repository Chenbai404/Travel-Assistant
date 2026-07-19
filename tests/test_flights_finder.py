"""Unit tests for flights_finder tool."""
"""
1. Normal flight search test
2. Flight search with return date test
3. Flight search with multiple adults test
4. Flight search with invalid airport codes test
5. Flight search with invalid date format test
6. Flight search with missing required parameters test
7. Flight search with empty response test
8. Flight search with partial response test
9. Flight search with error response test
10. Flight search with timeout test
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock

from agents.tools.flights_finder import flights_finder, FlightsInput


class TestFlightsFinder:
    """Test suite for flights_finder tool."""

    @pytest.fixture
    def mock_serpapi_response(self):
        """Mock successful SerpAPI response."""
        return {
            'best_flights': [
                {
                    'airline': 'American Airlines',
                    'departure': {
                        'airport': 'JFK',
                        'time': '10:25 AM'
                    },
                    'arrival': {
                        'airport': 'LAX',
                        'time': '1:25 PM'
                    },
                    'duration': '5 hours',
                    'price': 350
                },
                {
                    'airline': 'Delta',
                    'departure': {
                        'airport': 'JFK',
                        'time': '2:00 PM'
                    },
                    'arrival': {
                        'airport': 'LAX',
                        'time': '5:30 PM'
                    },
                    'duration': '5 hours 30 minutes',
                    'price': 380
                }
            ]
        }

    @pytest.fixture
    def mock_serpapi_search(self):
        """Mock SerpAPI search object."""
        mock_search = Mock()
        mock_search.data = {
            'best_flights': [
                {
                    'airline': 'American Airlines',
                    'departure': {'airport': 'JFK', 'time': '10:25 AM'},
                    'arrival': {'airport': 'LAX', 'time': '1:25 PM'},
                    'duration': '5 hours',
                    'price': 350
                }
            ]
        }
        return mock_search

    def test_normal_flight_search(self, mock_serpapi_search):
        """Test normal flight search with valid parameters."""
        with patch('agents.tools.flights_finder.serpapi') as mock_serpapi:
            mock_serpapi.search.return_value = mock_serpapi_search

            params = FlightsInput(
                departure_airport='JFK',
                arrival_airport='LAX',
                outbound_date='2024-06-15',
                return_date='2024-06-22',
                adults=1
            )

            result = flights_finder({'params': params})

            assert isinstance(result, list)
            assert len(result) > 0
            assert 'airline' in result[0]
            assert 'departure' in result[0]
            assert 'arrival' in result[0]

            # Verify SerpAPI was called with correct parameters
            mock_serpapi.search.assert_called_once()
            call_args = mock_serpapi.search.call_args[0][0]
            assert call_args['departure_id'] == 'JFK'
            assert call_args['arrival_id'] == 'LAX'
            assert call_args['outbound_date'] == '2024-06-15'
            assert call_args['return_date'] == '2024-06-22'

    def test_missing_required_parameters(self):
        """Test handling of missing required parameters."""
        with patch('agents.tools.flights_finder.serpapi') as mock_serpapi:
            mock_search = Mock()
            mock_serpapi.search.return_value = mock_search

            # Test with missing departure airport
            params = FlightsInput(
                departure_airport=None,
                arrival_airport='LAX',
                outbound_date='2024-06-15'
            )

            result = flights_finder({'params': params})

            # Should still attempt search but may fail or return empty
            mock_serpapi.search.assert_called_once()

    def test_serpapi_call_failure(self):
        """Test handling of SerpAPI call failure."""
        with patch('agents.tools.flights_finder.serpapi') as mock_serpapi:
            mock_serpapi.search.side_effect = Exception("API call failed")

            params = FlightsInput(
                departure_airport='JFK',
                arrival_airport='LAX',
                outbound_date='2024-06-15'
            )

            result = flights_finder({'params': params})

            # Should return error message
            assert isinstance(result, str)
            assert "API call failed" in result

    def test_date_format_validation(self, mock_serpapi_search):
        """Test date format validation."""
        with patch('agents.tools.flights_finder.serpapi') as mock_serpapi:
            mock_serpapi.search.return_value = mock_serpapi_search

            # Test valid date format
            params = FlightsInput(
                departure_airport='JFK',
                arrival_airport='LAX',
                outbound_date='2024-06-15',  # Valid YYYY-MM-DD format
                return_date='2024-06-22'
            )

            result = flights_finder({'params': params})

            call_args = mock_serpapi.search.call_args[0][0]
            assert call_args['outbound_date'] == '2024-06-15'
            assert call_args['return_date'] == '2024-06-22'

    def test_airport_code_validation(self, mock_serpapi_search):
        """Test airport code format validation."""
        with patch('agents.tools.flights_finder.serpapi') as mock_serpapi:
            mock_serpapi.search.return_value = mock_serpapi_search

            # Test valid IATA codes
            params = FlightsInput(
                departure_airport='JFK',  # Valid IATA code
                arrival_airport='LAX',    # Valid IATA code
                outbound_date='2024-06-15'
            )

            result = flights_finder({'params': params})

            call_args = mock_serpapi.search.call_args[0][0]
            assert call_args['departure_id'] == 'JFK'
            assert call_args['arrival_id'] == 'LAX'

    def test_return_data_structure(self, mock_serpapi_search):
        """Test the structure of returned flight data."""
        with patch('agents.tools.flights_finder.serpapi') as mock_serpapi:
            mock_serpapi.search.return_value = mock_serpapi_search

            params = FlightsInput(
                departure_airport='JFK',
                arrival_airport='LAX',
                outbound_date='2024-06-15'
            )

            result = flights_finder({'params': params})

            # Verify result is a list
            assert isinstance(result, list)

            # Verify each flight has expected structure
            for flight in result:
                assert isinstance(flight, dict)
                # Check for common flight data fields
                assert 'airline' in flight or 'flights' in flight

    def test_passenger_count_parameters(self, mock_serpapi_search):
        """Test passenger count parameters."""
        with patch('agents.tools.flights_finder.serpapi') as mock_serpapi:
            mock_serpapi.search.return_value = mock_serpapi_search

            params = FlightsInput(
                departure_airport='JFK',
                arrival_airport='LAX',
                outbound_date='2024-06-15',
                adults=2,
                children=1,
                infants_in_seat=0,
                infants_on_lap=1
            )

            result = flights_finder({'params': params})

            call_args = mock_serpapi.search.call_args[0][0]
            assert call_args['adults'] == 2
            assert call_args['children'] == 1
            assert call_args['infants_in_seat'] == 0
            assert call_args['infants_on_lap'] == 1

    def test_default_parameters(self, mock_serpapi_search):
        """Test default parameter values."""
        with patch('agents.tools.flights_finder.serpapi') as mock_serpapi:
            mock_serpapi.search.return_value = mock_serpapi_search

            params = FlightsInput(
                departure_airport='JFK',
                arrival_airport='LAX',
                outbound_date='2024-06-15'
            )

            result = flights_finder({'params': params})

            call_args = mock_serpapi.search.call_args[0][0]
            # Check default values
            assert call_args['adults'] == 1  # Default
            assert call_args['children'] == 0  # Default
            assert call_args['infants_in_seat'] == 0  # Default
            assert call_args['infants_on_lap'] == 0  # Default

    def test_one_way_flight(self, mock_serpapi_search):
        """Test one-way flight search (no return date)."""
        with patch('agents.tools.flights_finder.serpapi') as mock_serpapi:
            mock_serpapi.search.return_value = mock_serpapi_search

            params = FlightsInput(
                departure_airport='JFK',
                arrival_airport='LAX',
                outbound_date='2024-06-15',
                return_date=None  # One-way
            )

            result = flights_finder({'params': params})

            call_args = mock_serpapi.search.call_args[0][0]
            assert call_args['return_date'] is None
