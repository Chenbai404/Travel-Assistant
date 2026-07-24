"""Offline tests for the Phase 2 LangGraph workflow."""

import json

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from agents.agent import Agent
from agents.memory.preference_memory import PreferenceMemory


class StubLLM:
    """Small deterministic LLM replacement used by all workflow tests."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        if not self.responses:
            raise AssertionError("Unexpected LLM invocation in offline test")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return AIMessage(content=response)


def preference_json(**overrides):
    value = {
        "destination": "Tokyo",
        "start_date": "2026-10-15",
        "end_date": "2026-10-20",
        "budget": {"amount": 2000, "currency": "USD"},
        "interests": ["food", "culture"],
        "companions": ["solo"],
        "constraints": [],
        "accessibility_needs": None,
        "accommodation_type": "hotel",
        "transportation_preference": "public transit",
        "meal_preferences": [],
    }
    value.update(overrides)
    return json.dumps(value)


def places_json():
    return json.dumps(
        [
            {
                "name": "Senso-ji",
                "type": "temple",
                "description": "Historic temple",
                "rating": 4.7,
                "estimated_cost": "free",
            },
            {
                "name": "Ueno Park",
                "type": "park",
                "description": "Large public park",
                "rating": 4.5,
                "estimated_cost": "low",
            },
            {
                "name": "Tokyo National Museum",
                "type": "museum",
                "description": "Japanese art and history",
                "rating": 4.6,
                "estimated_cost": "medium",
            },
        ]
    )


@pytest.fixture
def agent(tmp_path):
    sent_messages = []

    def record_email(sender, receiver, subject, html):
        sent_messages.append(
            {
                'sender': sender,
                'receiver': receiver,
                'subject': subject,
                'html': html,
            }
        )

    instance = Agent(
        preference_llm=StubLLM(preference_json()),
        destination_llm=StubLLM(places_json()),
        email_llm=StubLLM("<html><body>Offline itinerary</body></html>"),
        preference_memory=PreferenceMemory(str(tmp_path / "preferences")),
        email_transport=record_email,
    )
    instance.sent_messages = sent_messages
    return instance


def test_graph_contains_phase2_nodes(agent):
    nodes = agent.graph.nodes
    assert {
        'preference_collector',
        'destination_search',
        'route_planner',
        'budget_estimator',
        'itinerary_synthesizer',
        'safety_reviewer',
        'email_sender',
    }.issubset(nodes)
    assert 'call_tools_llm' not in nodes
    assert 'invoke_tools' not in nodes


def test_complete_workflow_runs_offline_and_interrupts_before_email(agent):
    config = {'configurable': {'thread_id': 'complete-trip'}}
    result = agent.graph.invoke(
        {
            'messages': [HumanMessage(content="Plan my Tokyo trip")],
            'user_id': 'offline-user',
        },
        config=config,
    )

    assert result['preferences_complete'] is True
    assert len(result['places']) == 3
    assert len(result['routes']) == 2
    assert result['budget']['days'] == 6
    assert result['budget']['nights'] == 5
    assert len(result['itinerary']['daily_plans']) == 6
    assert agent.graph.get_state(config).next == ('email_sender',)

    final_output = result['messages'][-1].content
    assert '# 旅行规划结果' in final_output
    assert '## 约束摘要' in final_output
    assert '## 行程总览' in final_output
    assert '## 预算拆分' in final_output
    assert '## 风险与备选方案' in final_output
    assert '## 安全审查' in final_output


def test_incomplete_preferences_stop_before_destination(tmp_path):
    preference_llm = StubLLM(
        preference_json(
            start_date=None,
            end_date=None,
            budget=None,
            interests=[],
        )
    )
    destination_llm = StubLLM()
    instance = Agent(
        preference_llm=preference_llm,
        destination_llm=destination_llm,
        email_llm=StubLLM(),
        preference_memory=PreferenceMemory(str(tmp_path / "preferences")),
        email_transport=lambda *_: None,
    )

    result = instance.graph.invoke(
        {
            'messages': [HumanMessage(content="I want to visit Tokyo")],
            'user_id': 'incomplete-user',
        },
        config={'configurable': {'thread_id': 'incomplete-trip'}},
    )

    assert result['preferences_complete'] is False
    assert set(result['missing_fields']) == {
        'start_date',
        'end_date',
        'budget',
        'interests',
    }
    assert result.get('places') is None
    assert not destination_llm.calls
    assert "请补充以下信息" in result['messages'][-1].content


def test_second_turn_merges_preferences_and_continues(tmp_path):
    preference_llm = StubLLM(
        preference_json(
            start_date=None,
            end_date=None,
            budget=None,
            interests=[],
        ),
        preference_json(),
    )
    instance = Agent(
        preference_llm=preference_llm,
        destination_llm=StubLLM(places_json()),
        email_llm=StubLLM("<html>ok</html>"),
        preference_memory=PreferenceMemory(str(tmp_path / "preferences")),
        email_transport=lambda *_: None,
    )
    config = {'configurable': {'thread_id': 'two-turn-trip'}}

    first = instance.graph.invoke(
        {
            'messages': [HumanMessage(content="Tokyo")],
            'user_id': 'two-turn-user',
        },
        config=config,
    )
    assert first['preferences_complete'] is False
    assert first['clarification_count'] == 1

    second = instance.graph.invoke(
        {
            'messages': [
                HumanMessage(
                    content="October 15-20, 2000 USD, food and culture"
                )
            ],
            'user_id': 'two-turn-user',
        },
        config=config,
    )
    assert second['preferences_complete'] is True
    assert second['preferences']['destination'] == 'Tokyo'
    assert len(second['itinerary']['daily_plans']) == 6


def test_clarification_is_requested_at_most_once(tmp_path):
    incomplete = preference_json(
        start_date=None,
        end_date=None,
        budget=None,
        interests=[],
    )
    instance = Agent(
        preference_llm=StubLLM(incomplete, incomplete),
        destination_llm=StubLLM(),
        email_llm=StubLLM(),
        preference_memory=PreferenceMemory(str(tmp_path / "preferences")),
        email_transport=lambda *_: None,
    )
    config = {'configurable': {'thread_id': 'one-clarification'}}

    instance.graph.invoke(
        {
            'messages': [HumanMessage(content="Tokyo")],
            'user_id': 'clarification-user',
        },
        config=config,
    )
    second = instance.graph.invoke(
        {
            'messages': [HumanMessage(content="Still not sure")],
            'user_id': 'clarification-user',
        },
        config=config,
    )

    assert second['clarification_count'] == 1
    assert "本轮不会继续生成" in second['messages'][-1].content


def test_email_resume_uses_injected_transport(agent):
    config = {'configurable': {'thread_id': 'email-trip'}}
    agent.graph.invoke(
        {
            'messages': [HumanMessage(content="Plan Tokyo")],
            'user_id': 'email-user',
        },
        config=config,
    )

    completed = agent.graph.invoke(None, config=config)

    assert completed['messages'][-1].content == "邮件已成功发送。"
    assert len(agent.sent_messages) == 1
    assert agent.sent_messages[0]['sender'] == 'test@example.com'
    assert agent.sent_messages[0]['html'].startswith('<html>')


def test_sensitive_request_requires_confirmation(tmp_path):
    instance = Agent(
        preference_llm=StubLLM(
            preference_json(
                constraints=["use my passport number to make a booking"]
            )
        ),
        destination_llm=StubLLM(places_json()),
        email_llm=StubLLM("<html>ok</html>"),
        preference_memory=PreferenceMemory(str(tmp_path / "preferences")),
        email_transport=lambda *_: None,
    )
    result = instance.graph.invoke(
        {
            'messages': [
                HumanMessage(
                    content="Use my passport number to make a booking"
                )
            ],
            'user_id': 'safety-user',
        },
        config={'configurable': {'thread_id': 'safety-trip'}},
    )

    review = result['itinerary']['safety_review']
    assert review['needs_approval'] is True
    assert review['approved'] is False
    assert result['itinerary']['confirmation_items']
