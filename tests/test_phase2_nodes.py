"""Offline unit tests for deterministic Phase 2 nodes and formatting."""

from langchain_core.messages import AIMessage

from agents.formatter import TravelFormatter
from agents.nodes.budget_estimator import BudgetEstimatorNode
from agents.nodes.itinerary_synthesizer import ItinerarySynthesizerNode
from agents.nodes.route_planner import RoutePlannerNode
from agents.nodes.safety_reviewer import SafetyReviewerNode


def sample_places(count=5):
    return [
        {
            'name': f'Place {index}',
            'type': 'museum',
            'description': f'Description {index}',
            'rating': 4.5,
            'estimated_cost': ['free', 'low', 'medium'][index % 3],
        }
        for index in range(count)
    ]


def sample_preferences(**overrides):
    value = {
        'destination': 'Tokyo',
        'start_date': '2026-10-15',
        'end_date': '2026-10-17',
        'budget': {'amount': 1000.0, 'currency': 'USD'},
        'interests': ['culture'],
        'companions': ['solo'],
        'constraints': [],
        'accessibility_needs': None,
        'accommodation_type': None,
        'transportation_preference': 'walking',
        'meal_preferences': [],
    }
    value.update(overrides)
    return value


def test_route_planner_connects_places_sequentially():
    result = RoutePlannerNode()(
        {
            'preferences': sample_preferences(),
            'places': sample_places(3),
        }
    )

    assert len(result['routes']) == 2
    assert result['routes'][0]['from'] == 'Place 0'
    assert result['routes'][0]['to'] == 'Place 1'
    assert result['routes'][0]['is_estimate'] is True


def test_budget_estimator_handles_null_accommodation_and_dates():
    routes = RoutePlannerNode()(
        {
            'preferences': sample_preferences(),
            'places': sample_places(3),
        }
    )['routes']
    result = BudgetEstimatorNode()(
        {
            'preferences': sample_preferences(accommodation_type=None),
            'places': sample_places(3),
            'routes': routes,
        }
    )

    assert result['budget']['days'] == 3
    assert result['budget']['nights'] == 2
    assert result['budget']['breakdown']['accommodation']['type'] == 'hotel'
    assert result['budget']['breakdown']['accommodation']['total'] == 200
    assert result['budget']['currency'] == 'USD'


def test_itinerary_assigns_every_place_without_dropping_remainder():
    places = sample_places(5)
    budget = {
        'days': 3,
        'currency': 'USD',
        'total_estimated': 500,
        'comparison': {'within_budget': True},
    }
    result = ItinerarySynthesizerNode()(
        {
            'preferences': sample_preferences(),
            'places': places,
            'routes': [],
            'budget': budget,
        }
    )

    plans = result['itinerary']['daily_plans']
    assigned = [
        place['name']
        for plan in plans
        for place in plan['places']
    ]
    assert len(plans) == 3
    assert assigned == [place['name'] for place in places]
    assert [len(plan['places']) for plan in plans] == [2, 2, 1]


def test_itinerary_keeps_empty_days_for_full_trip_duration():
    result = ItinerarySynthesizerNode()(
        {
            'preferences': sample_preferences(),
            'places': sample_places(1),
            'routes': [],
            'budget': {
                'days': 3,
                'currency': 'USD',
                'comparison': {},
            },
        }
    )

    plans = result['itinerary']['daily_plans']
    assert len(plans) == 3
    assert [len(plan['places']) for plan in plans] == [1, 0, 0]


def test_safety_reviewer_produces_complete_standard_output():
    preferences = sample_preferences()
    budget = BudgetEstimatorNode()(
        {
            'preferences': preferences,
            'places': sample_places(2),
            'routes': [],
        }
    )['budget']
    itinerary = ItinerarySynthesizerNode()(
        {
            'preferences': preferences,
            'places': sample_places(2),
            'routes': [],
            'budget': budget,
        }
    )['itinerary']

    result = SafetyReviewerNode()(
        {
            'messages': [AIMessage(content="Planning complete")],
            'preferences': preferences,
            'budget': budget,
            'itinerary': itinerary,
        }
    )
    content = result['messages'][0].content

    assert '# 旅行规划结果' in content
    assert '## 行程总览' in content
    assert '### 第 1 天' in content
    assert '## 预算拆分' in content
    assert 'USD' in content
    assert result['itinerary']['safety_review']['approved'] is True


def test_formatter_uses_budget_currency_instead_of_hardcoded_dollars():
    text = TravelFormatter.format_budget_breakdown(
        {
            'currency': 'CNY',
            'breakdown': {
                'accommodation': {
                    'type': 'hotel',
                    'per_night': 100,
                    'nights': 2,
                    'total': 200,
                },
                'transportation': {'mode': 'walking', 'total': 0},
                'food': {'daily': 50, 'days': 3, 'total': 150},
                'activities': {'places_count': 2, 'total': 20},
                'miscellaneous': {
                    'description': 'buffer',
                    'total': 55.5,
                },
                'total': 425.5,
            },
            'comparison': {
                'within_budget': True,
                'difference': 574.5,
                'percentage': 42.55,
            },
        }
    )

    assert '425.50 CNY' in text
    assert '$425.50' not in text
