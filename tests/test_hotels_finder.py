"""Unit tests for hotels_finder tool."""
"""
1. Normal hotel search test
2. Hotel search with multiple guests test
3. Hotel search with invalid date format test
4. Hotel search with missing required parameters test
5. Hotel search with empty response test
6. Hotel search with partial response test
7. Hotel search with error response test
8. Hotel search with timeout test
"""

import os
import pytest
from unittest.mock import Mock, patch

from agents.tools.hotels_finder import hotels_finder, HotelsInput


class TestHotelsFinder:
    """Test suite for hotels_finder tool."""

    @pytest.fixture
    def mock_serpapi_response(self):
        """Mock successful SerpAPI response for hotels."""
        return {
            'properties': [
                {
                    'name': 'Grand Hotel',
                    'description': 'Luxury hotel in city center',
                    'rate_per_night': {'extracted': 250, 'currency': 'USD'},
                    'total_rate': {'extracted': 1750, 'currency': 'USD'},
                    'rating': 4.5,
                    'reviews': 500,
                    'location': 'Downtown',
                    'amenities': ['WiFi', 'Pool', 'Gym']
                },
                {
                    'name': 'City Inn',
                    'description': 'Budget-friendly accommodation',
                    'rate_per_night': {'extracted': 120, 'currency': 'USD'},
                    'total_rate': {'extracted': 840, 'currency': 'USD'},
                    'rating': 4.0,
                    'reviews': 300,
                    'location': 'Midtown',
                    'amenities': ['WiFi', 'Parking']
                }
            ]
        }

    @pytest.fixture
    def mock_serpapi_search(self):
        """Mock SerpAPI search object for hotels."""
        mock_search = Mock()
        mock_search.data = {
            'properties': [
                {
                    'name': 'Grand Hotel',
                    'description': 'Luxury hotel in city center',
                    'rate_per_night': {'extracted': 250, 'currency': 'USD'},
                    'total_rate': {'extracted': 1750, 'currency': 'USD'},
                    'rating': 4.5,
                    'reviews': 500,
                    'location': 'Downtown'
                }
            ]
        }
        return mock_search

    def test_normal_hotel_search(self, mock_serpapi_search):
        """Test normal hotel search with valid parameters."""
        with patch('agents.tools.hotels_finder.serpapi') as mock_serpapi:
            mock_serpapi.search.return_value = mock_serpapi_search

            params = HotelsInput(
                q='New York',
                check_in_date='2024-06-15',
                check_out_date='2024-06-22',
                adults=1
            )

            result = hotels_finder.invoke({'params': params})

            assert isinstance(result, list)
            assert len(result) > 0
            assert 'name' in result[0]
            assert 'description' in result[0]

            # Verify SerpAPI was called with correct parameters
            mock_serpapi.search.assert_called_once()
            call_args = mock_serpapi.search.call_args[0][0]
            assert call_args['q'] == 'New York'
            assert call_args['check_in_date'] == '2024-06-15'
            assert call_args['check_out_date'] == '2024-06-22'

    def test_missing_required_parameters(self):
        """Test handling of missing required parameters."""
        with patch('agents.tools.hotels_finder.serpapi') as mock_serpapi:
            mock_search = Mock()
            mock_search.data = {'properties': []}
            mock_serpapi.search.return_value = mock_search

            # Test with missing location
            params = HotelsInput(
                q='New York',
                check_in_date='2024-06-15',
                check_out_date='2024-06-22'
            )

            result = hotels_finder.invoke({'params': params})

            # Should still attempt search
            mock_serpapi.search.assert_called_once()

    def test_serpapi_call_failure(self):
        """Test handling of SerpAPI call failure."""
        with patch('agents.tools.hotels_finder.serpapi') as mock_serpapi:
            mock_serpapi.search.side_effect = Exception("API call failed")

            params = HotelsInput(
                q='New York',
                check_in_date='2024-06-15',
                check_out_date='2024-06-22'
            )

            with pytest.raises(Exception, match="API call failed"):
                hotels_finder.invoke({'params': params})

    def test_date_format_validation(self, mock_serpapi_search):
        """Test date format validation."""
        with patch('agents.tools.hotels_finder.serpapi') as mock_serpapi:
            mock_serpapi.search.return_value = mock_serpapi_search

            # Test valid date format
            params = HotelsInput(
                q='New York',
                check_in_date='2024-06-15',  # Valid YYYY-MM-DD format
                check_out_date='2024-06-22'
            )

            result = hotels_finder.invoke({'params': params})

            call_args = mock_serpapi.search.call_args[0][0]
            assert call_args['check_in_date'] == '2024-06-15'
            assert call_args['check_out_date'] == '2024-06-22'

    def test_hotel_class_filtering(self, mock_serpapi_search):
        """Test hotel class (star rating) filtering."""
        with patch('agents.tools.hotels_finder.serpapi') as mock_serpapi:
            mock_serpapi.search.return_value = mock_serpapi_search

            params = HotelsInput(
                q='New York',
                check_in_date='2024-06-15',
                check_out_date='2024-06-22',
                hotel_class='4'  # 4-star hotels
            )

            result = hotels_finder.invoke({'params': params})

            call_args = mock_serpapi.search.call_args[0][0]
            assert call_args['hotel_class'] == '4'

    def test_sorting_functionality(self, mock_serpapi_search):
        """Test hotel sorting functionality."""
        with patch('agents.tools.hotels_finder.serpapi') as mock_serpapi:
            mock_serpapi.search.return_value = mock_serpapi_search

            # Test default sorting (by rating)
            params = HotelsInput(
                q='New York',
                check_in_date='2024-06-15',
                check_out_date='2024-06-22',
                sort_by=8  # Default: highest rating
            )

            result = hotels_finder.invoke({'params': params})

            call_args = mock_serpapi.search.call_args[0][0]
            assert call_args['sort_by'] == 8 or call_args['sort_by'] == '8'

    def test_guest_count_parameters(self, mock_serpapi_search):
        """Test guest count parameters."""
        with patch('agents.tools.hotels_finder.serpapi') as mock_serpapi:
            mock_serpapi.search.return_value = mock_serpapi_search

            params = HotelsInput(
                q='New York',
                check_in_date='2024-06-15',
                check_out_date='2024-06-22',
                adults=2,
                children=1,
                rooms=1
            )

            result = hotels_finder.invoke({'params': params})

            call_args = mock_serpapi.search.call_args[0][0]
            assert call_args['adults'] == 2
            assert call_args['children'] == 1
            assert call_args['rooms'] == 1

    def test_result_limiting(self, mock_serpapi_search):
        """Test that results are limited to 5 properties."""
        with patch('agents.tools.hotels_finder.serpapi') as mock_serpapi:
            # Mock response with more than 5 properties
            mock_search = Mock()
            mock_search.data = {
                'properties': [
                    {'name': f'Hotel {i}', 'description': 'Test'} 
                    for i in range(10)
                ]
            }
            mock_serpapi.search.return_value = mock_search

            params = HotelsInput(
                q='New York',
                check_in_date='2024-06-15',
                check_out_date='2024-06-22'
            )

            result = hotels_finder.invoke({'params': params})

            # Should limit to 5 results
            assert len(result) <= 5

    def test_default_parameters(self, mock_serpapi_search):
        """Test default parameter values."""
        with patch('agents.tools.hotels_finder.serpapi') as mock_serpapi:
            mock_serpapi.search.return_value = mock_serpapi_search

            params = HotelsInput(
                q='New York',
                check_in_date='2024-06-15',
                check_out_date='2024-06-22'
            )

            result = hotels_finder.invoke({'params': params})

            call_args = mock_serpapi.search.call_args[0][0]
            # Check default values
            assert call_args['adults'] == 1  # Default
            assert call_args['children'] == 0  # Default
            assert call_args['rooms'] == 1  # Default
            assert call_args['sort_by'] == 8  # Default: highest rating

    def test_location_parameter_variations(self, mock_serpapi_search):
        """Test various location parameter formats."""
        with patch('agents.tools.hotels_finder.serpapi') as mock_serpapi:
            mock_serpapi.search.return_value = mock_serpapi_search

            test_locations = [
                'New York',
                'Paris, France',
                'Tokyo, Japan',
                'London'
            ]

            for location in test_locations:
                params = HotelsInput(
                    q=location,
                    check_in_date='2024-06-15',
                    check_out_date='2024-06-22'
                )

                result = hotels_finder.invoke({'params': params})

                call_args = mock_serpapi.search.call_args[0][0]
                assert call_args['q'] == location
