"""Unit tests for collect_preferences tool."""
"""
1. Full preference extraction test
2. Partial preference extraction test
3. Preference merging logic test
4. JSON parsing error handling test
5. LLM call failure handling test
6. Date format validation test
7. Budget format validation test
8. Markdown JSON wrapper test
9. Interest field requirement test
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import AIMessage

from agents.tools.collect_preferences import collect_preferences, PreferenceInput


class TestCollectPreferences:
    """Test suite for collect_preferences tool."""

    @pytest.fixture
    def mock_llm_response_complete(self):
        """Mock LLM response with complete preferences."""
        return AIMessage(
            content=json.dumps({
                "destination": "Tokyo",
                "start_date": "2024-03-15",
                "end_date": "2024-03-20",
                "budget": {"amount": 2000, "currency": "USD"},
                "interests": ["food", "technology", "culture"],
                "companions": ["solo"],
                "constraints": [],
                "accessibility_needs": None,
                "accommodation_type": "hotel",
                "transportation_preference": "public transit",
                "meal_preferences": []
            })
        )

    @pytest.fixture
    def mock_llm_response_partial(self):
        """Mock LLM response with partial preferences."""
        return AIMessage(
            content=json.dumps({
                "destination": "Paris",
                "start_date": "2024-06-01",
                "end_date": None,
                "budget": None,
                "interests": ["museums"],
                "companions": None,
                "constraints": None,
                "accessibility_needs": None,
                "accommodation_type": None,
                "transportation_preference": None,
                "meal_preferences": None
            })
        )

    @pytest.fixture
    def mock_llm_response_invalid_json(self):
        """Mock LLM response with invalid JSON."""
        return AIMessage(content="This is not valid JSON")

    @pytest.fixture
    def mock_llm_response_markdown_json(self):
        """Mock LLM response with markdown-wrapped JSON."""
        return AIMessage(
            content='```json\n{"destination": "London", "start_date": "2024-07-01", "end_date": "2024-07-10", "budget": {"amount": 1500, "currency": "GBP"}, "interests": ["history", "museums"], "companions": ["couple"], "constraints": [], "accessibility_needs": null, "accommodation_type": "hotel", "transportation_preference": null, "meal_preferences": []}\n```'
        )

    def test_complete_preference_extraction(self, mock_llm_response_complete):
        """Test extraction of complete preferences with all required fields."""
        with patch('langchain_openai.ChatOpenAI') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.invoke.return_value = mock_llm_response_complete
            mock_llm_class.return_value = mock_llm

            params = PreferenceInput(
                user_input="I want to travel to Tokyo from March 15-20, 2024 with a budget of $2000. I'm interested in food, technology, and culture."
            )

            result = collect_preferences.invoke({'params': params})

            assert result['is_complete'] is True
            assert result['clarification_needed'] is False
            assert len(result['missing_fields']) == 0
            assert result['preferences']['destination'] == 'Tokyo'
            assert result['preferences']['start_date'] == '2024-03-15'
            assert result['preferences']['end_date'] == '2024-03-20'
            assert result['preferences']['budget']['amount'] == 2000
            assert result['preferences']['budget']['currency'] == 'USD'
            assert 'food' in result['preferences']['interests']

    def test_partial_preference_extraction(self, mock_llm_response_partial):
        """Test extraction of partial preferences with missing required fields."""
        with patch('langchain_openai.ChatOpenAI') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.invoke.return_value = mock_llm_response_partial
            mock_llm_class.return_value = mock_llm

            params = PreferenceInput(
                user_input="I want to go to Paris in June for museums"
            )

            result = collect_preferences.invoke({'params': params})

            assert result['is_complete'] is False
            assert result['clarification_needed'] is True
            assert len(result['missing_fields']) > 0
            assert 'end_date' in result['missing_fields']
            assert 'budget' in result['missing_fields']
            assert result['preferences']['destination'] == 'Paris'
            assert result['preferences']['start_date'] == '2024-06-01'

    def test_preference_merge_logic(self, mock_llm_response_partial):
        """Test merging new preferences with existing current_preferences."""
        with patch('langchain_openai.ChatOpenAI') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.invoke.return_value = mock_llm_response_partial
            mock_llm_class.return_value = mock_llm

            current_prefs = {
                "destination": "Paris",
                "start_date": "2024-06-01",
                "end_date": "2024-06-07",
                "budget": {"amount": 3000, "currency": "EUR"},
                "interests": ["food"]
            }

            params = PreferenceInput(
                user_input="I'm also interested in museums",
                current_preferences=current_prefs
            )

            result = collect_preferences.invoke({'params': params})

            # Should merge with current preferences
            assert result['preferences']['destination'] == 'Paris'
            assert result['preferences']['end_date'] == '2024-06-07'  # From current
            assert result['preferences']['budget']['amount'] == 3000  # From current
            assert 'museums' in result['preferences']['interests']  # From new

    def test_json_parsing_error_handling(self, mock_llm_response_invalid_json):
        """Test handling of invalid JSON response from LLM."""
        with patch('langchain_openai.ChatOpenAI') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.invoke.return_value = mock_llm_response_invalid_json
            mock_llm_class.return_value = mock_llm

            params = PreferenceInput(user_input="Test input")

            result = collect_preferences.invoke({'params': params})

            # Should return error result
            assert result['is_complete'] is False
            assert result['clarification_needed'] is True
            assert result['preferences'] == {}
            assert len(result['missing_fields']) == 5  # All required fields

    def test_llm_call_failure_handling(self):
        """Test handling of LLM call failure."""
        with patch('langchain_openai.ChatOpenAI') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.invoke.side_effect = Exception("API call failed")
            mock_llm_class.return_value = mock_llm

            params = PreferenceInput(user_input="Test input")

            result = collect_preferences.invoke({'params': params})

            # Should return error result
            assert result['is_complete'] is False
            assert result['clarification_needed'] is True
            assert result['preferences'] == {}

    def test_date_format_validation(self):
        """Test date format validation and normalization."""
        with patch('langchain_openai.ChatOpenAI') as mock_llm_class:
            # Test various date formats
            test_cases = [
                ("2024-03-15", "2024-03-15"),  # ISO format
                ("2024/03/15", "2024-03-15"),  # Slash format
                ("15-03-2024", "2024-03-15"),  # European format
                ("March 15, 2024", "2024-03-15"),  # Text format
            ]

            for input_date, expected_date in test_cases:
                mock_llm = Mock()
                mock_llm.invoke.return_value = AIMessage(
                    content=json.dumps({
                        "destination": "Tokyo",
                        "start_date": input_date,
                        "end_date": "2024-03-20",
                        "budget": {"amount": 2000, "currency": "USD"},
                        "interests": ["food"],
                        "companions": None,
                        "constraints": None,
                        "accessibility_needs": None,
                        "accommodation_type": None,
                        "transportation_preference": None,
                        "meal_preferences": None
                    })
                )
                mock_llm_class.return_value = mock_llm

                params = PreferenceInput(user_input="Test input")
                result = collect_preferences.invoke({'params': params})

                assert result['preferences']['start_date'] == expected_date

    def test_budget_format_validation(self):
        """Test budget format validation and normalization."""
        with patch('langchain_openai.ChatOpenAI') as mock_llm_class:
            # Test various budget formats
            test_cases = [
                ({"amount": 1000, "currency": "USD"}, {"amount": 1000.0, "currency": "USD"}),
                ("$1000", {"amount": 1000.0, "currency": "$"}),
                ("1000 USD", {"amount": 1000.0, "currency": "USD"}),
                (1000, {"amount": 1000.0, "currency": "USD"}),
            ]

            for input_budget, expected_budget in test_cases:
                mock_llm = Mock()
                mock_llm.invoke.return_value = AIMessage(
                    content=json.dumps({
                        "destination": "Tokyo",
                        "start_date": "2024-03-15",
                        "end_date": "2024-03-20",
                        "budget": input_budget,
                        "interests": ["food"],
                        "companions": None,
                        "constraints": None,
                        "accessibility_needs": None,
                        "accommodation_type": None,
                        "transportation_preference": None,
                        "meal_preferences": None
                    })
                )
                mock_llm_class.return_value = mock_llm

                params = PreferenceInput(user_input="Test input")
                result = collect_preferences.invoke({'params': params})

                if result['preferences']['budget']:
                    assert result['preferences']['budget']['amount'] == expected_budget['amount']

    def test_markdown_json_wrapping(self, mock_llm_response_markdown_json):
        """Test handling of markdown-wrapped JSON response."""
        with patch('langchain_openai.ChatOpenAI') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.invoke.return_value = mock_llm_response_markdown_json
            mock_llm_class.return_value = mock_llm

            params = PreferenceInput(user_input="Test input")
            result = collect_preferences.invoke({'params': params})

            assert result['is_complete'] is True
            assert result['preferences']['destination'] == 'London'

    def test_interests_field_required(self):
        """Test that interests field is required for completion."""
        with patch('langchain_openai.ChatOpenAI') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.invoke.return_value = AIMessage(
                content=json.dumps({
                    "destination": "Tokyo",
                    "start_date": "2024-03-15",
                    "end_date": "2024-03-20",
                    "budget": {"amount": 2000, "currency": "USD"},
                    "interests": [],  # Empty interests
                    "companions": None,
                    "constraints": None,
                    "accessibility_needs": None,
                    "accommodation_type": None,
                    "transportation_preference": None,
                    "meal_preferences": None
                })
            )
            mock_llm_class.return_value = mock_llm

            params = PreferenceInput(user_input="Test input")
            result = collect_preferences.invoke({'params': params})

            assert result['is_complete'] is False
            assert 'interests' in result['missing_fields']
