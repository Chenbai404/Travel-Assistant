"""Route planner node for the Phase 2 workflow."""

from typing import Any, Dict

from langchain_core.messages import AIMessage


class RoutePlannerNode:
    """Create provisional sequential routes until OSRM is integrated."""

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        preferences = state.get('preferences', {})
        places = state.get('places', [])
        transportation = (
            preferences.get('transportation_preference') or 'public transit'
        )

        routes = []
        for current_place, next_place in zip(places, places[1:]):
            routes.append(
                {
                    "from": current_place.get('name', 'Unknown'),
                    "to": next_place.get('name', 'Unknown'),
                    "transportation_mode": transportation,
                    "estimated_duration": "15-30 minutes",
                    "estimated_cost": "low",
                    "distance": "2-5 km",
                    "is_estimate": True,
                }
            )

        if routes:
            message = (
                f"已生成 {len(routes)} 段临时路线；"
                "距离与时间为非实时估算。"
            )
        else:
            message = "候选地点不足，暂时无需生成地点间路线。"

        return {
            'messages': [AIMessage(content=message)],
            'routes': routes,
        }


def route_planner(state: Dict[str, Any]) -> Dict[str, Any]:
    """Compatibility wrapper for direct node use."""

    return RoutePlannerNode()(state)
