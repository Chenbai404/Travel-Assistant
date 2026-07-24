"""Tool for collecting and structuring user travel preferences."""

from typing import Optional
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import tool

from agents.models.preference import TravelPreference, PreferenceExtractionResult
from agents.normalizer import ConstraintNormalizer
from agents.memory.preference_memory import get_preference_memory


class PreferenceInput(BaseModel):
    """Input schema for preference collection."""
    user_input: str = Field(description="Natural language input from user describing their travel preferences")
    current_preferences: Optional[dict] = Field(default=None, description="Current collected preferences (if any)")
    user_id: Optional[str] = Field(default="default", description="User identifier for memory persistence")


class PreferenceInputSchema(BaseModel):
    """Schema wrapper for preference input."""
    params: PreferenceInput


@tool(args_schema=PreferenceInputSchema)
def collect_preferences(params: PreferenceInput) -> PreferenceExtractionResult:
    """Collect and structure user travel preferences from natural language input.

    This tool uses the LLM to extract structured travel preferences from user input,
    identifies missing fields, and determines if clarification is needed.

    Args:
        params: PreferenceInput containing user input and optional current preferences

    Returns:
        PreferenceExtractionResult with extracted preferences, missing fields, and completion status
    """
    preference_input = params
    from langchain_openai import ChatOpenAI
    import os
    import json

    # Initialize LLM for preference extraction
    preference_llm = ChatOpenAI(
        model="qwen3.7-max",
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://ws-701qztd515ek1e5g.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
        temperature=0.1
    )

    # System prompt for preference extraction
    system_prompt = """You are a travel preference extraction expert. Extract structured travel preferences from user input.

Extract the following fields if present:
- destination: City, country, or region they want to visit
- start_date: When they want to start the trip (YYYY-MM-DD format)
- end_date: When they want to end the trip (YYYY-MM-DD format)
- budget: Total budget with currency (e.g., {"amount": 1000, "currency": "USD"})
- interests: List of interests (e.g., ["museums", "food", "nature", "history"])
- companions: List of who is traveling (e.g., ["solo", "couple", "family", "friends"])
- constraints: List of constraints (e.g., ["no flights", "wheelchair accessible", "vegetarian"])
- accessibility_needs: List of accessibility requirements
- accommodation_type: Type of accommodation (e.g., "hotel", "hostel", "airbnb", "resort")
- transportation_preference: Preferred transportation (e.g., "public transit", "rental car", "walking")
- meal_preferences: Dietary preferences (e.g., ["vegetarian", "halal", "no restrictions"])

Return ONLY a valid JSON object. If a field is not mentioned, set it to null.
Do not include any explanation or text outside the JSON.

Example output:
{
    "destination": "Tokyo",
    "start_date": "2024-03-15",
    "end_date": "2024-03-20",
    "budget": {"amount": 2000, "currency": "USD"},
    "interests": ["food", "technology", "culture"],
    "companions": ["solo"],
    "constraints": [],
    "accessibility_needs": null,
    "accommodation_type": "hotel",
    "transportation_preference": "public transit",
    "meal_preferences": []
}
"""

    # Get memory instance
    memory = get_preference_memory()

    # Load stored preferences from memory
    stored_preferences = memory.get_user_preferences(preference_input.user_id)

    # Build user message
    user_message = f"Extract travel preferences from this input: {preference_input.user_input}"

    # Include stored preferences from memory
    if stored_preferences:
        user_message += f"\n\nStored preferences from memory: {json.dumps(stored_preferences, indent=2)}"

    # Include current session preferences if provided
    if preference_input.current_preferences:
        user_message += f"\n\nCurrent session preferences: {json.dumps(preference_input.current_preferences, indent=2)}"
        user_message += "\n\nUpdate or add to these preferences based on the new input."

    try:
        # Call LLM to extract preferences
        response = preference_llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ])

        # Parse JSON response
        response_text = response.content.strip()
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.strip("`").replace("json", "").strip()

        extracted_preferences = json.loads(response_text)

        # Normalize preferences
        normalized_preferences = ConstraintNormalizer.normalize_preferences(extracted_preferences)

        # Merge with stored preferences from memory
        if stored_preferences:
            for key, value in stored_preferences.items():
                if key != 'last_updated' and (key not in normalized_preferences or normalized_preferences[key] is None):
                    normalized_preferences[key] = value

        # Merge with current session preferences if provided
        if preference_input.current_preferences:
            for key, value in preference_input.current_preferences.items():
                if key not in normalized_preferences or normalized_preferences[key] is None:
                    normalized_preferences[key] = value

        # Save updated preferences to memory
        memory.update_user_preferences(preference_input.user_id, normalized_preferences)

        # Check for missing required fields
        required_fields = ['destination', 'start_date', 'end_date', 'budget']
        missing_fields = []

        for field in required_fields:
            if field not in normalized_preferences or normalized_preferences[field] is None:
                missing_fields.append(field)

        # Also check if interests are provided (important for itinerary)
        if 'interests' not in normalized_preferences or not normalized_preferences['interests']:
            missing_fields.append('interests')

        is_complete = len(missing_fields) == 0
        clarification_needed = not is_complete

        return PreferenceExtractionResult(
            preferences=normalized_preferences,
            missing_fields=missing_fields,
            is_complete=is_complete,
            clarification_needed=clarification_needed
        )

    except Exception as e:
        # Return error result
        return PreferenceExtractionResult(
            preferences={},
            missing_fields=['destination', 'start_date', 'end_date', 'budget', 'interests'],
            is_complete=False,
            clarification_needed=True
        )
