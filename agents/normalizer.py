"""Constraint normalization module for standardizing travel preferences."""

import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional


class ConstraintNormalizer:
    """Normalizes and standardizes travel constraint data."""

    CURRENCY_SYMBOLS = {
        '$': 'USD',
        '€': 'EUR',
        '£': 'GBP',
        '¥': 'CNY',
        '₹': 'INR',
    }

    @staticmethod
    def normalize_budget(budget_input: Any) -> Optional[Dict[str, Any]]:
        """Normalize budget input to standard format.
        
        Args:
            budget_input: Raw budget input (string, number, or dict)
            
        Returns:
            Normalized budget dict with 'amount' and 'currency', or None if invalid
        """
        if budget_input is None:
            return None
            
        # If already a dict, validate and return
        if isinstance(budget_input, dict):
            if 'amount' in budget_input and 'currency' in budget_input:
                try:
                    amount = float(budget_input['amount'])
                    currency = str(budget_input['currency']).strip()
                    return {
                        'amount': amount,
                        'currency': ConstraintNormalizer.CURRENCY_SYMBOLS.get(
                            currency, currency.upper()
                        ),
                    }
                except (ValueError, TypeError):
                    return None
            return None
        
        # If string, parse it
        if isinstance(budget_input, str):
            # Extract currency symbols and amounts
            # Common patterns: "$1000", "1000 USD", "¥5000", "€800"
            patterns = [
                r'([¥$€£₹])\s*([\d,]+\.?\d*)',  # Symbol before number
                r'([\d,]+\.?\d*)\s*([¥$€£₹A-Z]{3})',  # Number before symbol/code
                r'([\d,]+\.?\d*)\s*(USD|EUR|GBP|JPY|CNY|INR)',  # Number before currency code
            ]
            
            for pattern in patterns:
                match = re.search(pattern, budget_input, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    # Determine which group is currency and which is amount
                    if groups[0] in ['¥', '$', '€', '£', '₹', 'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'INR']:
                        currency = groups[0]
                        amount_str = groups[1]
                    else:
                        amount_str = groups[0]
                        currency = groups[1]
                    
                    try:
                        amount = float(amount_str.replace(',', ''))
                        return {
                            'amount': amount,
                            'currency': ConstraintNormalizer.CURRENCY_SYMBOLS.get(
                                currency, currency.upper()
                            ),
                        }
                    except (ValueError, TypeError):
                        continue
        
        # If number, assume default currency (USD)
        if isinstance(budget_input, (int, float)):
            try:
                return {
                    'amount': float(budget_input),
                    'currency': 'USD',
                }
            except (ValueError, TypeError):
                return None
        
        return None

    @staticmethod
    def normalize_date(date_input: Any) -> Optional[str]:
        """Normalize date input to YYYY-MM-DD format.
        
        Args:
            date_input: Raw date input (string or date object)
            
        Returns:
            Normalized date string in YYYY-MM-DD format, or None if invalid
        """
        if date_input is None:
            return None
            
        # If already a string, try to parse it
        if isinstance(date_input, str):
            # Try common date formats
            date_formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%d-%m-%Y',
                '%d/%m/%Y',
                '%m/%d/%Y',
                '%Y%m%d',
                '%B %d, %Y',
                '%b %d, %Y',
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_input, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # Try natural language parsing (simple cases)
            # e.g., "tomorrow", "next week", etc.
            # This is a simplified version - could be enhanced with dateparser
            today = datetime.now()
            date_input_lower = date_input.lower().strip()
            
            if date_input_lower == 'tomorrow':
                return (today + timedelta(days=1)).strftime('%Y-%m-%d')
            elif date_input_lower == 'today':
                return today.strftime('%Y-%m-%d')
            elif date_input_lower == 'next week':
                return (today + timedelta(days=7)).strftime('%Y-%m-%d')
        
        # If date object, format it
        if isinstance(date_input, datetime):
            return date_input.strftime('%Y-%m-%d')
        
        if isinstance(date_input, date):
            return date_input.strftime('%Y-%m-%d')
        
        return None

    @staticmethod
    def normalize_location(location_input: Any) -> Optional[str]:
        """Normalize location input.
        
        Args:
            location_input: Raw location input
            
        Returns:
            Normalized location string, or None if invalid
        """
        if location_input is None:
            return None
            
        if isinstance(location_input, str):
            # Clean up the location string
            location = location_input.strip()
            # Remove extra whitespace
            location = ' '.join(location.split())
            # Capitalize properly
            location = location.title()
            return location if location else None
        
        if isinstance(location_input, (int, float)):
            return str(location_input)
        
        return None

    @staticmethod
    def normalize_preferences(preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize all preference fields.
        
        Args:
            preferences: Raw preferences dictionary
            
        Returns:
            Normalized preferences dictionary
        """
        normalized = {}
        
        # Normalize budget
        if 'budget' in preferences:
            normalized['budget'] = ConstraintNormalizer.normalize_budget(preferences['budget'])
        
        # Normalize dates
        if 'start_date' in preferences:
            normalized['start_date'] = ConstraintNormalizer.normalize_date(preferences['start_date'])
        if 'end_date' in preferences:
            normalized['end_date'] = ConstraintNormalizer.normalize_date(preferences['end_date'])
        
        # Normalize location
        if 'destination' in preferences:
            normalized['destination'] = ConstraintNormalizer.normalize_location(preferences['destination'])
        
        # Copy other fields as-is (could add more normalization as needed)
        for key, value in preferences.items():
            if key not in ['budget', 'start_date', 'end_date', 'destination']:
                if key in {
                    'interests',
                    'companions',
                    'constraints',
                    'accessibility_needs',
                    'meal_preferences',
                }:
                    if value is None:
                        normalized[key] = None
                    elif isinstance(value, list):
                        normalized[key] = [
                            str(item).strip()
                            for item in value
                            if str(item).strip()
                        ]
                    else:
                        normalized[key] = [str(value).strip()]
                elif key in {'accommodation_type', 'transportation_preference'}:
                    normalized[key] = (
                        str(value).strip().lower() if value is not None else None
                    )
                else:
                    normalized[key] = value
        
        return normalized
