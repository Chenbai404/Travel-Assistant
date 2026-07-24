"""Rule-based budget estimator for the Phase 2 workflow."""

from datetime import datetime
from typing import Any, Dict

from langchain_core.messages import AIMessage


class BudgetEstimatorNode:
    """Estimate a deterministic budget from preferences, places, and routes."""

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        preferences = state.get('preferences', {})
        places = state.get('places', [])
        routes = state.get('routes', [])
        trip_days, nights = self._trip_duration(
            preferences.get('start_date'),
            preferences.get('end_date'),
        )
        user_budget = preferences.get('budget') or {}
        currency = user_budget.get('currency') or 'USD'

        breakdown = self._estimate_budget(
            preferences,
            places,
            routes,
            trip_days,
            nights,
        )
        comparison = self._compare_with_user_budget(breakdown, user_budget)
        budget = {
            'breakdown': breakdown,
            'comparison': comparison,
            'total_estimated': breakdown['total'],
            'user_budget': user_budget,
            'days': trip_days,
            'nights': nights,
            'currency': currency,
            'is_estimate': True,
        }

        return {
            'messages': [
                AIMessage(
                    content=(
                        f"已完成 {trip_days} 天行程的规则预算估算："
                        f"{breakdown['total']:.2f} {currency}。"
                    )
                )
            ],
            'budget': budget,
        }

    @staticmethod
    def _trip_duration(start_date: str | None, end_date: str | None) -> tuple[int, int]:
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                if end >= start:
                    nights = (end - start).days
                    return nights + 1, nights
            except (ValueError, TypeError):
                pass
        return 1, 0

    def _estimate_budget(
        self,
        preferences: Dict[str, Any],
        places: list,
        routes: list,
        days: int,
        nights: int,
    ) -> Dict[str, Any]:
        accommodation_type = preferences.get('accommodation_type') or 'hotel'
        accommodation_per_night = self._get_accommodation_cost(
            accommodation_type
        )
        accommodation_total = accommodation_per_night * nights

        transportation_cost = self._estimate_transportation_cost(routes)
        daily_food_cost = self._get_daily_food_cost(
            preferences.get('meal_preferences') or []
        )
        food_total = daily_food_cost * days
        activities_cost = self._estimate_activities_cost(places)
        subtotal = (
            accommodation_total
            + transportation_cost
            + food_total
            + activities_cost
        )
        miscellaneous = subtotal * 0.15

        return {
            'accommodation': {
                'per_night': accommodation_per_night,
                'total': accommodation_total,
                'nights': nights,
                'type': accommodation_type,
            },
            'transportation': {
                'total': transportation_cost,
                'mode': (
                    preferences.get('transportation_preference')
                    or 'public transit'
                ),
            },
            'food': {
                'daily': daily_food_cost,
                'total': food_total,
                'days': days,
            },
            'activities': {
                'total': activities_cost,
                'places_count': len(places),
            },
            'miscellaneous': {
                'total': miscellaneous,
                'description': '15% buffer for unexpected expenses',
            },
            'total': subtotal + miscellaneous,
        }

    @staticmethod
    def _get_accommodation_cost(accommodation_type: str | None) -> float:
        costs = {
            'hotel': 100,
            'hostel': 40,
            'airbnb': 80,
            'resort': 200,
            'budget': 30,
        }
        normalized_type = str(accommodation_type or 'hotel').lower()
        return float(costs.get(normalized_type, 100))

    @staticmethod
    def _estimate_transportation_cost(routes: list) -> float:
        if not routes:
            return 0.0
        costs = {'low': 10, 'medium': 25, 'high': 50}
        return float(
            sum(costs.get(route.get('estimated_cost'), 20) for route in routes)
        )

    @staticmethod
    def _get_daily_food_cost(meal_preferences: list) -> float:
        normalized = {str(item).lower() for item in meal_preferences}
        base_cost = 50.0
        if {'vegetarian', 'vegan'} & normalized:
            base_cost *= 0.9
        if 'fine dining' in normalized:
            base_cost *= 2
        return base_cost

    @staticmethod
    def _estimate_activities_cost(places: list) -> float:
        costs = {'free': 0, 'low': 10, 'medium': 25, 'high': 50}
        return float(
            sum(costs.get(place.get('estimated_cost'), 20) for place in places)
        )

    @staticmethod
    def _compare_with_user_budget(
        breakdown: Dict[str, Any],
        user_budget: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not user_budget or user_budget.get('amount') is None:
            return {
                'within_budget': None,
                'difference': None,
                'percentage': None,
                'message': 'No user budget specified for comparison',
            }

        user_amount = float(user_budget.get('amount', 0))
        estimated = float(breakdown['total'])
        difference = user_amount - estimated
        percentage = (estimated / user_amount * 100) if user_amount > 0 else 0
        return {
            'within_budget': difference >= 0,
            'difference': difference,
            'percentage': percentage,
            'message': f"Estimated cost is {percentage:.1f}% of the budget",
        }


def budget_estimator(state: Dict[str, Any]) -> Dict[str, Any]:
    """Compatibility wrapper for direct node use."""

    return BudgetEstimatorNode()(state)
