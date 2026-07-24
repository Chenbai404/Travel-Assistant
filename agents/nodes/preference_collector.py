"""Preference collection node for the LangGraph workflow."""

import json
import os
from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

from agents.formatter import TravelFormatter
from agents.memory.preference_memory import get_preference_memory
from agents.normalizer import ConstraintNormalizer


REQUIRED_PREFERENCE_FIELDS = (
    'destination',
    'start_date',
    'end_date',
    'budget',
    'interests',
)

PREFERENCE_EXTRACTION_PROMPT = """You are a travel preference extraction expert.
Extract travel preferences from the latest user input and return only one valid
JSON object.

Supported fields:
- destination
- start_date (YYYY-MM-DD)
- end_date (YYYY-MM-DD)
- budget: {"amount": number, "currency": "ISO currency code"}
- interests: list[str]
- companions: list[str]
- constraints: list[str]
- accessibility_needs: list[str]
- accommodation_type
- transportation_preference
- meal_preferences: list[str]

Use null for fields not stated by the user. Do not wrap the JSON in prose.
"""


def missing_preference_fields(preferences: Dict[str, Any]) -> list[str]:
    """Return required preference fields that still have no useful value."""

    missing = []
    for field in REQUIRED_PREFERENCE_FIELDS:
        value = preferences.get(field)
        if value is None or value == '' or value == []:
            missing.append(field)
    return missing


def preferences_are_complete(state: Dict[str, Any]) -> bool:
    """Conditional-edge predicate used by the graph."""

    return bool(state.get('preferences_complete'))


class PreferenceCollectorNode:
    """Collect, normalize, merge, and persist travel preferences."""

    def __init__(self, llm=None, memory=None):
        self.llm = llm or ChatOpenAI(
            model="qwen3.7-max",
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=(
                "https://ws-701qztd515ek1e5g.cn-beijing.maas.aliyuncs.com/"
                "compatible-mode/v1"
            ),
            temperature=0.1,
        )
        self.memory = memory or get_preference_memory()

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        messages = state.get('messages', [])
        current_preferences = state.get('preferences', {})
        user_id = state.get('user_id', 'default')
        clarification_count = int(state.get('clarification_count', 0))

        user_message = next(
            (
                message.content
                for message in reversed(messages)
                if isinstance(message, HumanMessage)
            ),
            None,
        )

        if not user_message:
            return {
                'messages': [
                    AIMessage(content="请先告诉我你的旅行需求。")
                ],
                'preferences': current_preferences,
                'missing_fields': missing_preference_fields(current_preferences),
                'preferences_complete': False,
                'clarification_count': clarification_count,
            }

        stored_preferences = self.memory.get_user_preferences(user_id)
        extracted, extraction_error = self._extract_preferences_with_llm(
            user_message,
            stored_preferences,
            current_preferences,
        )

        merged = self._merge_preferences(
            stored_preferences,
            current_preferences,
            extracted,
        )
        normalized = ConstraintNormalizer.normalize_preferences(merged)
        self.memory.update_user_preferences(user_id, normalized)

        missing_fields = missing_preference_fields(normalized)
        is_complete = not missing_fields

        if is_complete:
            response = (
                "已完成旅行偏好收集。\n\n"
                + TravelFormatter.format_constraint_summary(normalized)
            )
        elif clarification_count == 0:
            response = TravelFormatter.format_clarification_request(missing_fields)
            clarification_count = 1
        else:
            response = (
                "偏好信息仍不完整，本轮不会继续生成可能不可靠的行程。\n\n"
                f"仍缺少：{', '.join(missing_fields)}。"
            )

        if extraction_error:
            response += (
                "\n\n偏好解析暂时失败，已保留此前收集的信息；"
                "请补充或重新描述缺失内容。"
            )

        return {
            'messages': [AIMessage(content=response)],
            'preferences': normalized,
            'missing_fields': missing_fields,
            'preferences_complete': is_complete,
            'clarification_count': clarification_count,
        }

    def _extract_preferences_with_llm(
        self,
        user_input: str,
        stored_preferences: dict,
        current_preferences: dict,
    ) -> tuple[dict, bool]:
        context = {
            'stored_preferences': self._without_metadata(stored_preferences),
            'current_preferences': current_preferences,
            'latest_user_input': user_input,
        }

        try:
            response = self.llm.invoke(
                [
                    {"role": "system", "content": PREFERENCE_EXTRACTION_PROMPT},
                    {
                        "role": "user",
                        "content": json.dumps(context, ensure_ascii=False),
                    },
                ]
            )
            return self._parse_json_object(response.content), False
        except (json.JSONDecodeError, TypeError, ValueError, AttributeError):
            return {}, True
        except Exception:
            return {}, True

    @staticmethod
    def _parse_json_object(content: str) -> dict:
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        value = json.loads(text)
        if not isinstance(value, dict):
            raise ValueError("Preference response must be a JSON object")
        return value

    @staticmethod
    def _without_metadata(preferences: dict) -> dict:
        return {
            key: value
            for key, value in preferences.items()
            if key != 'last_updated'
        }

    @classmethod
    def _merge_preferences(cls, *sources: dict) -> dict:
        merged: dict[str, Any] = {}
        for source in sources:
            for key, value in cls._without_metadata(source or {}).items():
                if value is not None and value != [] and value != '':
                    merged[key] = value
                elif key not in merged:
                    merged[key] = value
        return merged


def preference_collector(state: Dict[str, Any]) -> Dict[str, Any]:
    """Compatibility wrapper for direct node use."""

    return PreferenceCollectorNode()(state)
