"""Destination search node for the Phase 2 workflow."""

import json
import os
from typing import Any, Dict

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI


class DestinationSearchNode:
    """Use an LLM to propose structured places until a real API is added."""

    def __init__(self, llm=None):
        self.llm = llm or ChatOpenAI(
            model="qwen3.7-max",
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=(
                "https://ws-701qztd515ek1e5g.cn-beijing.maas.aliyuncs.com/"
                "compatible-mode/v1"
            ),
            temperature=0.3,
        )

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        preferences = state.get('preferences', {})
        destination = preferences.get('destination')
        interests = preferences.get('interests') or []

        if not destination:
            return {
                'messages': [AIMessage(content="缺少目的地，无法搜索地点。")],
                'places': [],
            }

        prompt = f"""Suggest 5-10 places in {destination} matching these interests:
{', '.join(interests) if interests else 'general sightseeing'}.

Return only a JSON list. Each object must contain:
name, type, description, rating (1-5), estimated_cost
(free, low, medium, or high).
"""

        try:
            response = self.llm.invoke(
                [
                    {
                        "role": "system",
                        "content": (
                            "You produce grounded, conservative destination "
                            "suggestions as structured JSON."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ]
            )
            places = self._parse_places(response.content)
            message = f"已找到 {len(places)} 个候选地点。"
        except Exception:
            places = [
                {
                    "name": f"{destination}热门景点",
                    "type": "sightseeing",
                    "description": "地点搜索暂时不可用时生成的占位建议。",
                    "rating": 0.0,
                    "estimated_cost": "medium",
                    "is_fallback": True,
                }
            ]
            message = (
                "地点搜索响应无法解析，已使用占位建议；"
                "该地点需要人工核实。"
            )

        return {
            'messages': [AIMessage(content=message)],
            'places': places,
        }

    @staticmethod
    def _parse_places(content: str) -> list[dict]:
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        value = json.loads(text)
        if not isinstance(value, list) or not value:
            raise ValueError("Destination response must be a non-empty list")

        places = []
        for item in value:
            if not isinstance(item, dict) or not item.get('name'):
                continue
            places.append(
                {
                    'name': str(item['name']),
                    'type': str(item.get('type') or 'sightseeing'),
                    'description': str(
                        item.get('description') or 'No description available'
                    ),
                    'rating': float(item.get('rating') or 0),
                    'estimated_cost': str(
                        item.get('estimated_cost') or 'medium'
                    ).lower(),
                }
            )

        if not places:
            raise ValueError("Destination response contains no usable places")
        return places


def destination_search(state: Dict[str, Any]) -> Dict[str, Any]:
    """Compatibility wrapper for direct node use."""

    return DestinationSearchNode()(state)
