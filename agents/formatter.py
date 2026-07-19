"""Output formatting module for travel agent responses."""

from typing import Dict, Any, Optional
from datetime import datetime


class TravelFormatter:
    """Formats travel agent outputs into structured, readable formats."""

    @staticmethod
    def format_constraint_summary(preferences: Dict[str, Any]) -> str:
        """Generate a readable constraint summary from preferences.
        
        Args:
            preferences: Normalized travel preferences dictionary
            
        Returns:
            Formatted constraint summary string
        """
        if not preferences:
            return "No preferences collected yet."
        
        summary_lines = []
        
        # Destination
        if preferences.get('destination'):
            summary_lines.append(f"**目的地**: {preferences['destination']}")
        
        # Dates
        if preferences.get('start_date') and preferences.get('end_date'):
            summary_lines.append(f"**时间**: {preferences['start_date']} 至 {preferences['end_date']}")
            # Calculate duration
            try:
                start = datetime.strptime(preferences['start_date'], '%Y-%m-%d')
                end = datetime.strptime(preferences['end_date'], '%Y-%m-%d')
                duration = (end - start).days + 1
                summary_lines.append(f"**行程天数**: {duration} 天")
            except ValueError:
                pass
        elif preferences.get('start_date'):
            summary_lines.append(f"**开始日期**: {preferences['start_date']}")
        elif preferences.get('end_date'):
            summary_lines.append(f"**结束日期**: {preferences['end_date']}")
        
        # Budget
        if preferences.get('budget'):
            budget = preferences['budget']
            if isinstance(budget, dict):
                summary_lines.append(f"**预算**: {budget.get('amount', 0)} {budget.get('currency', 'USD')}")
            else:
                summary_lines.append(f"**预算**: {budget}")
        
        # Interests
        if preferences.get('interests'):
            interests_str = ', '.join(preferences['interests'])
            summary_lines.append(f"**兴趣**: {interests_str}")
        
        # Companions
        if preferences.get('companions'):
            companions_str = ', '.join(preferences['companions'])
            summary_lines.append(f"**同行人**: {companions_str}")
        
        # Constraints
        if preferences.get('constraints'):
            constraints_str = ', '.join(preferences['constraints'])
            summary_lines.append(f"**约束**: {constraints_str}")
        
        # Accessibility needs
        if preferences.get('accessibility_needs'):
            accessibility_str = ', '.join(preferences['accessibility_needs'])
            summary_lines.append(f"**无障碍需求**: {accessibility_str}")
        
        # Accommodation type
        if preferences.get('accommodation_type'):
            summary_lines.append(f"**住宿类型**: {preferences['accommodation_type']}")
        
        # Transportation preference
        if preferences.get('transportation_preference'):
            summary_lines.append(f"**交通偏好**: {preferences['transportation_preference']}")
        
        # Meal preferences
        if preferences.get('meal_preferences'):
            meal_str = ', '.join(preferences['meal_preferences'])
            summary_lines.append(f"**饮食偏好**: {meal_str}")
        
        return '\n'.join(summary_lines) if summary_lines else "No preferences collected."

    @staticmethod
    def format_clarification_request(missing_fields: list[str]) -> str:
        """Generate a clarification request for missing fields.
        
        Args:
            missing_fields: List of missing field names
            
        Returns:
            Formatted clarification request string
        """
        field_questions = {
            'destination': "您想去哪里旅行？请告诉我目的地城市或国家。",
            'start_date': "您计划什么时候开始旅行？请提供开始日期（格式：YYYY-MM-DD）。",
            'end_date': "您计划什么时候结束旅行？请提供结束日期（格式：YYYY-MM-DD）。",
            'budget': "您的总预算是多少？请说明金额和货币（例如：1000 USD）。",
            'interests': "您对什么感兴趣？例如：博物馆、美食、自然风光、历史、购物等。",
            'companions': "谁和您一起旅行？例如：独自、情侣、家庭、朋友等。",
            'accommodation_type': "您偏好什么类型的住宿？例如：酒店、民宿、青年旅社等。",
            'transportation_preference': "您偏好什么交通方式？例如：公共交通、租车、步行等。"
        }
        
        questions = []
        for field in missing_fields:
            if field in field_questions:
                questions.append(f"- {field_questions[field]}")
        
        if questions:
            return "为了更好地为您规划旅行，请补充以下信息：\n\n" + '\n'.join(questions)
        return "请提供更多旅行偏好信息。"

    @staticmethod
    def format_itinerary_overview(itinerary: Dict[str, Any]) -> str:
        """Format itinerary overview table.
        
        Args:
            itinerary: Itinerary data dictionary
            
        Returns:
            Formatted overview table string
        """
        # This will be implemented in later phases
        return "Itinerary overview formatting - to be implemented in Phase 2"

    @staticmethod
    def format_daily_plan(day_plan: Dict[str, Any]) -> str:
        """Format daily detailed plan.
        
        Args:
            day_plan: Daily plan data dictionary
            
        Returns:
            Formatted daily plan string
        """
        # This will be implemented in later phases
        return "Daily plan formatting - to be implemented in Phase 2"

    @staticmethod
    def format_budget_breakdown(budget: Dict[str, Any]) -> str:
        """Format budget breakdown.
        
        Args:
            budget: Budget data dictionary
            
        Returns:
            Formatted budget breakdown string
        """
        # This will be implemented in later phases
        return "Budget breakdown formatting - to be implemented in Phase 3"

    @staticmethod
    def format_risks_and_alternatives(risks: list[str], alternatives: list[str]) -> str:
        """Format risks and alternative solutions.
        
        Args:
            risks: List of potential risks
            alternatives: List of alternative solutions
            
        Returns:
            Formatted risks and alternatives string
        """
        # This will be implemented in later phases
        return "Risks and alternatives formatting - to be implemented in Phase 3"

    @staticmethod
    def format_confirmation_items(items: list[str]) -> str:
        """Format items requiring user confirmation.
        
        Args:
            items: List of items needing confirmation
            
        Returns:
            Formatted confirmation items string
        """
        # This will be implemented in later phases
        return "Confirmation items formatting - to be implemented in Phase 4"
