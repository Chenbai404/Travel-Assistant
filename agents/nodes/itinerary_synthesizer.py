"""Itinerary synthesizer for the Phase 2 workflow."""

from datetime import datetime, timedelta
from typing import Any, Dict

from langchain_core.messages import AIMessage


class ItinerarySynthesizerNode:
    """Distribute all candidate places into contiguous daily plans."""

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        preferences = state.get('preferences', {})
        places = state.get('places', [])
        routes = state.get('routes', [])
        budget = state.get('budget', {})
        days = max(1, int(budget.get('days') or 1))
        currency = budget.get('currency') or 'USD'

        daily_plans = self._generate_daily_itinerary(
            preferences,
            places,
            routes,
            days,
            currency,
        )
        summary = {
            'destination': preferences.get('destination', 'Unknown'),
            'start_date': preferences.get('start_date'),
            'end_date': preferences.get('end_date'),
            'total_days': days,
            'total_places': len(places),
            'interests': preferences.get('interests') or [],
            'budget_estimate': budget.get('total_estimated', 0),
            'currency': currency,
            'within_budget': budget.get('comparison', {}).get(
                'within_budget'
            ),
        }
        itinerary = {
            'summary': summary,
            'daily_plans': daily_plans,
            'total_places': len(places),
            'total_routes': len(routes),
            'created_at': datetime.now().isoformat(),
        }

        return {
            'messages': [
                AIMessage(
                    content=(
                        f"已生成 {days} 天行程，共安排 {len(places)} 个地点。"
                    )
                )
            ],
            'itinerary': itinerary,
        }

    def _generate_daily_itinerary(
        self,
        preferences: Dict[str, Any],
        places: list,
        routes: list,
        days: int,
        currency: str,
    ) -> list[dict]:
        start_date = preferences.get('start_date')
        place_groups = self._split_contiguously(places, days)
        plans = []

        for day_index, day_places in enumerate(place_groups):
            day_date = self._date_for_day(start_date, day_index)
            names = {place.get('name') for place in day_places}
            day_routes = [
                route
                for route in routes
                if route.get('from') in names and route.get('to') in names
            ]
            plans.append(
                {
                    'day': day_index + 1,
                    'date': day_date,
                    'places': day_places,
                    'routes': day_routes,
                    'estimated_cost': self._estimate_day_cost(day_places),
                    'currency': currency,
                    'transportation': (
                        preferences.get('transportation_preference')
                        or 'public transit'
                    ),
                    'notes': (
                        "营业时间和实时交通尚未接入，出发前请再次确认。"
                    ),
                }
            )
        return plans

    @staticmethod
    def _split_contiguously(items: list, group_count: int) -> list[list]:
        quotient, remainder = divmod(len(items), group_count)
        groups = []
        cursor = 0
        for index in range(group_count):
            size = quotient + (1 if index < remainder else 0)
            groups.append(items[cursor:cursor + size])
            cursor += size
        return groups

    @staticmethod
    def _date_for_day(start_date: str | None, day_index: int) -> str | None:
        if not start_date:
            return None
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            return (start + timedelta(days=day_index)).strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _estimate_day_cost(day_places: list) -> float:
        costs = {'free': 0, 'low': 10, 'medium': 25, 'high': 50}
        return float(
            sum(costs.get(place.get('estimated_cost'), 20) for place in day_places)
        )


def itinerary_synthesizer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Compatibility wrapper for direct node use."""

    return ItinerarySynthesizerNode()(state)
