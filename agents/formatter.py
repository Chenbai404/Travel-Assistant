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
        if not itinerary or 'summary' not in itinerary:
            return "No itinerary data available."

        summary = itinerary['summary']

        overview = f"## 行程总览\n\n"
        overview += f"| 项目 | 详情 |\n"
        overview += f"|------|------|\n"
        overview += f"| 目的地 | {summary.get('destination', 'N/A')} |\n"
        overview += f"| 开始日期 | {summary.get('start_date', 'N/A')} |\n"
        overview += f"| 结束日期 | {summary.get('end_date', 'N/A')} |\n"
        overview += f"| 行程天数 | {summary.get('total_days', 0)} 天 |\n"
        overview += f"| 景点数量 | {summary.get('total_places', 0)} 个 |\n"

        interests = summary.get('interests', [])
        if interests:
            overview += f"| 兴趣标签 | {', '.join(interests)} |\n"

        budget = summary.get('budget_estimate', 0)
        currency = summary.get('currency', 'USD')
        overview += f"| 预算估算 | {budget:.2f} {currency} |\n"

        within_budget = summary.get('within_budget')
        if within_budget is not None:
            status = "✅ 在预算内" if within_budget else "⚠️ 超出预算"
            overview += f"| 预算状态 | {status} |\n"

        return overview

    @staticmethod
    def format_daily_plan(day_plan: Dict[str, Any]) -> str:
        """Format daily detailed plan.

        Args:
            day_plan: Daily plan data dictionary

        Returns:
            Formatted daily plan string
        """
        if not day_plan:
            return "No daily plan data available."

        day_num = day_plan.get('day', 1)
        date = day_plan.get('date', 'TBD')
        places = day_plan.get('places', [])

        plan = f"### 第 {day_num} 天 - {date}\n\n"

        if places:
            plan += f"**今日景点 ({len(places)} 个):**\n\n"
            for i, place in enumerate(places, 1):
                plan += f"{i}. **{place.get('name', 'Unknown')}** ({place.get('type', 'N/A')})\n"
                plan += f"   - 描述: {place.get('description', 'No description')}\n"
                plan += f"   - 评分: {place.get('rating', 0)}/5\n"
                plan += f"   - 预估费用: {place.get('estimated_cost', 'N/A')}\n\n"

        plan += f"**交通方式:** {day_plan.get('transportation', 'N/A')}\n"
        currency = day_plan.get('currency', 'USD')
        plan += (
            f"**预估当日费用:** "
            f"{day_plan.get('estimated_cost', 0):.2f} {currency}\n"
        )
        routes = day_plan.get('routes', [])
        if routes:
            plan += "**地点间路线:**\n"
            for route in routes:
                plan += (
                    f"- {route.get('from', 'N/A')} → "
                    f"{route.get('to', 'N/A')}，"
                    f"{route.get('transportation_mode', 'N/A')}，"
                    f"{route.get('estimated_duration', 'N/A')}\n"
                )
        plan += f"**备注:** {day_plan.get('notes', 'No notes')}\n"

        return plan

    @staticmethod
    def format_budget_breakdown(budget: Dict[str, Any]) -> str:
        """Format budget breakdown.

        Args:
            budget: Budget data dictionary

        Returns:
            Formatted budget breakdown string
        """
        if not budget or 'breakdown' not in budget:
            return "No budget data available."

        breakdown = budget['breakdown']
        currency = budget.get('currency', 'USD')

        breakdown_str = "## 预算拆分\n\n"
        breakdown_str += f"| 类别 | 详情 | 金额 |\n"
        breakdown_str += f"|------|------|------|\n"

        # Accommodation
        acc = breakdown.get('accommodation', {})
        breakdown_str += (
            f"| 住宿 | {acc.get('type', 'N/A')} "
            f"({acc.get('per_night', 0):.2f} {currency}/晚 × "
            f"{acc.get('nights', 0)} 晚) | "
            f"{acc.get('total', 0):.2f} {currency} |\n"
        )

        # Transportation
        trans = breakdown.get('transportation', {})
        breakdown_str += (
            f"| 交通 | {trans.get('mode', 'N/A')} | "
            f"{trans.get('total', 0):.2f} {currency} |\n"
        )

        # Food
        food = breakdown.get('food', {})
        breakdown_str += (
            f"| 餐饮 | ({food.get('daily', 0):.2f} {currency}/天 × "
            f"{food.get('days', 0)} 天) | "
            f"{food.get('total', 0):.2f} {currency} |\n"
        )

        # Activities
        activities = breakdown.get('activities', {})
        breakdown_str += (
            f"| 活动 | {activities.get('places_count', 0)} 个景点 | "
            f"{activities.get('total', 0):.2f} {currency} |\n"
        )

        # Miscellaneous
        misc = breakdown.get('miscellaneous', {})
        breakdown_str += (
            f"| 其他 | {misc.get('description', 'N/A')} | "
            f"{misc.get('total', 0):.2f} {currency} |\n"
        )

        # Total
        total = breakdown.get('total', 0)
        breakdown_str += f"| **总计** | | **{total:.2f} {currency}** |\n"

        # Comparison
        comparison = budget.get('comparison', {})
        if comparison.get('within_budget') is not None:
            breakdown_str += f"\n**预算对比:**\n"
            breakdown_str += f"- 预算状态: {'✅ 在预算内' if comparison['within_budget'] else '⚠️ 超出预算'}\n"
            breakdown_str += (
                f"- 差额: {comparison.get('difference', 0):.2f} "
                f"{currency}\n"
            )
            breakdown_str += f"- 占比: {comparison.get('percentage', 0):.1f}%\n"

        return breakdown_str

    @staticmethod
    def format_risks_and_alternatives(risks: list[str], alternatives: list[str]) -> str:
        """Format risks and alternative solutions.

        Args:
            risks: List of potential risks
            alternatives: List of alternative solutions

        Returns:
            Formatted risks and alternatives string
        """
        output = "## 风险与备选方案\n\n"

        if risks:
            output += "### 潜在风险\n\n"
            for i, risk in enumerate(risks, 1):
                output += f"{i}. {risk}\n"
            output += "\n"

        if alternatives:
            output += "### 备选方案\n\n"
            for i, alt in enumerate(alternatives, 1):
                output += f"{i}. {alt}\n"
            output += "\n"

        if not risks and not alternatives:
            output += "暂无风险或备选方案。\n"

        return output

    @staticmethod
    def format_confirmation_items(items: list[str]) -> str:
        """Format items requiring user confirmation.

        Args:
            items: List of items needing confirmation

        Returns:
            Formatted confirmation items string
        """
        if not items:
            return "无需确认事项。"

        output = "## 用户确认事项\n\n"
        output += "请在继续之前确认以下事项：\n\n"

        for i, item in enumerate(items, 1):
            output += f"{i}. {item}\n"

        output += "\n请回复 '确认' 继续或提供修改意见。"

        return output
