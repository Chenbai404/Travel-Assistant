"""Preference memory module for persistent user preference storage."""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path


class PreferenceMemory:
    """Manages persistent storage and retrieval of user travel preferences."""

    def __init__(self, storage_dir: str = "data/memory"):
        """Initialize preference memory storage.
        
        Args:
            storage_dir: Directory to store preference files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.preferences_file = self.storage_dir / "user_preferences.json"
        self._ensure_storage_file()

    def _ensure_storage_file(self):
        """Ensure the storage file exists."""
        if not self.preferences_file.exists():
            self._save_data({})

    def _load_data(self) -> Dict[str, Any]:
        """Load preference data from storage.
        
        Returns:
            Dictionary of user preferences
        """
        try:
            with open(self.preferences_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_data(self, data: Dict[str, Any]):
        """Save preference data to storage.
        
        Args:
            data: Dictionary of user preferences to save
        """
        with open(self.preferences_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Retrieve all preferences for a specific user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Dictionary of user preferences, empty dict if none found
        """
        data = self._load_data()
        return data.get(user_id, {})

    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences with new data.
        
        This method merges new preferences with existing ones, preferring
        non-null values from the new preferences.
        
        Args:
            user_id: Unique identifier for the user
            preferences: New preferences to merge
            
        Returns:
            Updated complete preferences dictionary
        """
        data = self._load_data()
        
        if user_id not in data:
            data[user_id] = {}
        
        # Merge preferences, preferring non-null values
        for key, value in preferences.items():
            if value is not None and value != []:
                data[user_id][key] = value
            elif key not in data[user_id]:
                # Keep existing value if new value is null/empty
                data[user_id][key] = value
        
        # Add metadata
        data[user_id]['last_updated'] = datetime.now().isoformat()
        
        self._save_data(data)
        return data[user_id]

    def add_interest(self, user_id: str, interest: str) -> List[str]:
        """Add a single interest to user's preferences.
        
        Args:
            user_id: Unique identifier for the user
            interest: Interest to add
            
        Returns:
            Updated list of interests
        """
        data = self._load_data()
        
        if user_id not in data:
            data[user_id] = {}
        
        if 'interests' not in data[user_id]:
            data[user_id]['interests'] = []
        
        if interest not in data[user_id]['interests']:
            data[user_id]['interests'].append(interest)
        
        data[user_id]['last_updated'] = datetime.now().isoformat()
        self._save_data(data)
        
        return data[user_id]['interests']

    def remove_interest(self, user_id: str, interest: str) -> List[str]:
        """Remove an interest from user's preferences.
        
        Args:
            user_id: Unique identifier for the user
            interest: Interest to remove
            
        Returns:
            Updated list of interests
        """
        data = self._load_data()
        
        if user_id in data and 'interests' in data[user_id]:
            if interest in data[user_id]['interests']:
                data[user_id]['interests'].remove(interest)
            
            data[user_id]['last_updated'] = datetime.now().isoformat()
            self._save_data(data)
        
        return data.get(user_id, {}).get('interests', [])

    def get_interests(self, user_id: str) -> List[str]:
        """Get user's list of interests.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            List of interests, empty list if none found
        """
        preferences = self.get_user_preferences(user_id)
        return preferences.get('interests', [])

    def clear_user_preferences(self, user_id: str) -> bool:
        """Clear all preferences for a specific user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            True if successful, False otherwise
        """
        data = self._load_data()
        
        if user_id in data:
            del data[user_id]
            self._save_data(data)
            return True
        
        return False

    def get_preference_summary(self, user_id: str) -> str:
        """Get a human-readable summary of user preferences.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Formatted string summarizing preferences
        """
        preferences = self.get_user_preferences(user_id)
        
        if not preferences:
            return "No preferences stored for this user."
        
        summary_parts = []
        
        if 'interests' in preferences and preferences['interests']:
            summary_parts.append(f"Interests: {', '.join(preferences['interests'])}")
        
        if 'destination' in preferences and preferences['destination']:
            summary_parts.append(f"Preferred destination: {preferences['destination']}")
        
        if 'budget' in preferences and preferences['budget']:
            budget = preferences['budget']
            if isinstance(budget, dict):
                summary_parts.append(f"Budget: {budget.get('amount', 'N/A')} {budget.get('currency', 'N/A')}")
        
        if 'companions' in preferences and preferences['companions']:
            summary_parts.append(f"Travel companions: {', '.join(preferences['companions'])}")
        
        if 'accommodation_type' in preferences and preferences['accommodation_type']:
            summary_parts.append(f"Accommodation preference: {preferences['accommodation_type']}")
        
        if 'transportation_preference' in preferences and preferences['transportation_preference']:
            summary_parts.append(f"Transportation preference: {preferences['transportation_preference']}")
        
        if 'meal_preferences' in preferences and preferences['meal_preferences']:
            summary_parts.append(f"Meal preferences: {', '.join(preferences['meal_preferences'])}")
        
        if 'constraints' in preferences and preferences['constraints']:
            summary_parts.append(f"Constraints: {', '.join(preferences['constraints'])}")
        
        if 'accessibility_needs' in preferences and preferences['accessibility_needs']:
            summary_parts.append(f"Accessibility needs: {', '.join(preferences['accessibility_needs'])}")
        
        if summary_parts:
            return "\n".join(summary_parts)
        else:
            return "No specific preferences stored."

    def merge_with_memory(self, user_id: str, current_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Merge current preferences with stored memory.
        
        This is useful when starting a new conversation - it combines
        the current session's preferences with historically stored preferences.
        
        Args:
            user_id: Unique identifier for the user
            current_preferences: Preferences from current session
            
        Returns:
            Merged preferences dictionary
        """
        stored_preferences = self.get_user_preferences(user_id)
        
        merged = {}
        
        # Start with stored preferences
        for key, value in stored_preferences.items():
            if key != 'last_updated':
                merged[key] = value
        
        # Override with current preferences (current takes precedence)
        for key, value in current_preferences.items():
            if value is not None and value != []:
                merged[key] = value
        
        return merged


# Global instance for easy access
_memory_instance: Optional[PreferenceMemory] = None


def get_preference_memory() -> PreferenceMemory:
    """Get or create the global preference memory instance.
    
    Returns:
        PreferenceMemory instance
    """
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = PreferenceMemory()
    return _memory_instance
