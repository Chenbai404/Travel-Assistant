"""Travel preference data models."""

from typing import Optional, TypedDict


class TravelPreference(TypedDict, total=False):
    """Structured travel preferences accumulated across conversation turns."""

    destination: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    budget: Optional[dict]  # {"amount": float, "currency": str}
    interests: Optional[list[str]]
    companions: Optional[list[str]]
    constraints: Optional[list[str]]
    accessibility_needs: Optional[list[str]]
    accommodation_type: Optional[str]
    transportation_preference: Optional[str]
    meal_preferences: Optional[list[str]]


class PreferenceExtractionResult(TypedDict):
    """Result of preference extraction."""
    preferences: TravelPreference
    missing_fields: list[str]
    is_complete: bool
    clarification_needed: bool
