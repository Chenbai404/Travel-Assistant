"""Deterministic safety review and final Phase 2 response formatting."""

from datetime import datetime
from typing import Any, Dict, List

from langchain_core.messages import AIMessage

from agents.formatter import TravelFormatter


class SafetyReviewerNode:
    """Detect risky text and produce the final reviewed travel plan."""

    high_risk_keywords = [
        'password',
        'credit card',
        'creditcard',
        'debit card',
        'bank account',
        'passport number',
        'id number',
        'ssn',
        'cvv',
        'pin',
        'routing number',
        'account number',
        'wire transfer',
        'western union',
        'moneygram',
        'send money',
        '密码',
        '银行卡',
        '信用卡',
        '护照号码',
        '身份证号码',
        '转账',
        '付款',
        '预订',
    ]

    non_refundable_keywords = [
        'non-refundable',
        'non refundable',
        'nonrefundable',
        'no refund',
        'cannot be refunded',
        'final sale',
        'no cancellation',
        '不可退款',
        '不予退款',
        '不可取消',
    ]

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        preferences = state.get('preferences', {})
        itinerary = state.get('itinerary', {})
        budget = state.get('budget', {})
        text = self._collect_text_for_review(
            preferences,
            itinerary,
            state.get('messages', []),
        )
        issues = self._check_safety_issues(text)
        needs_approval = bool(
            issues['high_risk'] or issues['non_refundable']
        )
        risks, alternatives = self._planning_risks(
            itinerary,
            budget,
            issues,
        )
        confirmation_items = self._confirmation_items(issues)

        review = {
            'issues': issues,
            'needs_approval': needs_approval,
            'approved': not needs_approval,
            'reviewed_at': datetime.now().isoformat(),
        }
        reviewed_itinerary = {
            **itinerary,
            'risks': risks,
            'alternatives': alternatives,
            'confirmation_items': confirmation_items,
            'safety_review': review,
        }
        final_message = self._format_final_response(
            preferences,
            reviewed_itinerary,
            budget,
            risks,
            alternatives,
            confirmation_items,
            issues,
            needs_approval,
        )

        return {
            'messages': [AIMessage(content=final_message)],
            'itinerary': reviewed_itinerary,
        }

    @staticmethod
    def _collect_text_for_review(
        preferences: Dict[str, Any],
        itinerary: Dict[str, Any],
        messages: list,
    ) -> str:
        parts = [str(preferences), str(itinerary)]
        parts.extend(
            str(message.content)
            for message in messages
            if hasattr(message, 'content')
        )
        return ' '.join(parts).lower()

    def _check_safety_issues(self, text: str) -> Dict[str, List[str]]:
        high_risk = [
            keyword for keyword in self.high_risk_keywords if keyword in text
        ]
        non_refundable = [
            keyword
            for keyword in self.non_refundable_keywords
            if keyword in text
        ]
        warnings = []
        if high_risk:
            warnings.append("检测到高风险操作或敏感信息，需要人工确认。")
        if non_refundable:
            warnings.append("检测到不可退款或不可取消条款。")
        return {
            'high_risk': high_risk,
            'non_refundable': non_refundable,
            'warnings': warnings,
        }

    @staticmethod
    def _planning_risks(
        itinerary: Dict[str, Any],
        budget: Dict[str, Any],
        issues: Dict[str, List[str]],
    ) -> tuple[list[str], list[str]]:
        risks = list(issues['warnings'])
        alternatives = []

        if not itinerary.get('total_places'):
            risks.append("当前没有经过验证的候选地点。")
            alternatives.append("补充兴趣偏好后重新生成地点建议。")

        if budget.get('comparison', {}).get('within_budget') is False:
            risks.append("当前规则估算超过用户预算。")
            alternatives.append("减少付费活动或选择更经济的住宿类型。")

        risks.append("营业时间、价格和交通时间可能变化，当前路线非实时。")
        alternatives.append("出发前通过官方渠道核对开放时间和交通信息。")
        return risks, alternatives

    @staticmethod
    def _confirmation_items(
        issues: Dict[str, List[str]],
    ) -> list[str]:
        items = []
        if issues['high_risk']:
            items.append("确认不在对话中提供付款凭证、密码或证件号码。")
        if issues['non_refundable']:
            items.append("确认已理解相关服务的退款与取消条款。")
        return items

    def _format_final_response(
        self,
        preferences: dict,
        itinerary: dict,
        budget: dict,
        risks: list[str],
        alternatives: list[str],
        confirmation_items: list[str],
        issues: Dict[str, List[str]],
        needs_approval: bool,
    ) -> str:
        sections = [
            "# 旅行规划结果",
            "## 约束摘要\n\n"
            + TravelFormatter.format_constraint_summary(preferences),
            TravelFormatter.format_itinerary_overview(itinerary),
        ]
        sections.extend(
            TravelFormatter.format_daily_plan(day_plan)
            for day_plan in itinerary.get('daily_plans', [])
        )
        sections.extend(
            [
                TravelFormatter.format_budget_breakdown(budget),
                TravelFormatter.format_risks_and_alternatives(
                    risks,
                    alternatives,
                ),
                TravelFormatter.format_confirmation_items(
                    confirmation_items
                ),
                self._format_safety_message(issues, needs_approval),
            ]
        )
        return "\n\n".join(section for section in sections if section)

    @staticmethod
    def _format_safety_message(
        issues: Dict[str, List[str]],
        needs_approval: bool,
    ) -> str:
        if not needs_approval:
            return "## 安全审查\n\n✅ 未检测到需要人工确认的高风险动作。"

        lines = ["## 安全审查", "", "⚠️ 检测到需要人工确认的内容。"]
        if issues['high_risk']:
            lines.append(
                "- 高风险关键词：" + ", ".join(issues['high_risk'])
            )
        if issues['non_refundable']:
            lines.append(
                "- 不可退款关键词：" + ", ".join(issues['non_refundable'])
            )
        lines.append("- 系统不会代替用户付款、预订或提交敏感信息。")
        return "\n".join(lines)


def safety_reviewer(state: Dict[str, Any]) -> Dict[str, Any]:
    """Compatibility wrapper for direct node use."""

    return SafetyReviewerNode()(state)
