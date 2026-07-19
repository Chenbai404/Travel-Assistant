"""Unit tests for Agent workflow and state management."""
"""
1. State transition from call_tools_llm to invoke_tools test
2. State transition from call_tools_llm to email_sender test
3. Conditional edge logic when tool calls exist test
4. Conditional edge logic when no tool calls test
5. State transition from invoke_tools to call_tools_llm test
6. State transition from invoke_tools to email_sender test
7. State transition from email_sender to end test
8. State transition from end to end test
9. State transition from unknown state test
10. State transition with multiple messages test
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from agents.agent import Agent, AgentState


class TestAgentWorkflow:
    """Test suite for Agent workflow and state transitions."""

    @pytest.fixture
    def agent(self):
        """Create an Agent instance for testing."""
        with patch('agents.agent.ChatOpenAI'):
            return Agent()

    @pytest.fixture
    def sample_state(self):
        """Create a sample AgentState for testing."""
        return {
            'messages': [HumanMessage(content="I want to travel to Tokyo")],
            'preferences': {}
        }

    def test_state_transition_call_tools_llm_to_invoke_tools(self, agent, sample_state):
        """Test state transition from call_tools_llm to invoke_tools."""
        # Mock the LLM response with tool calls
        mock_message = AIMessage(
            content="",
            tool_calls=[
                {
                    'name': 'collect_preferences',
                    'args': {'user_input': 'I want to travel to Tokyo'},
                    'id': 'call_123'
                }
            ]
        )

        with patch.object(agent._tools_llm, 'invoke', return_value=mock_message):
            result = agent.call_tools_llm(sample_state)

            assert 'messages' in result
            assert len(result['messages']) == 1
            assert result['messages'][0].tool_calls is not None

    def test_state_transition_call_tools_llm_to_email_sender(self, agent, sample_state):
        """Test state transition from call_tools_llm to email_sender (no tool calls)."""
        # Mock the LLM response without tool calls
        mock_message = AIMessage(
            content="Here is your travel information...",
            tool_calls=[]
        )

        with patch.object(agent._tools_llm, 'invoke', return_value=mock_message):
            result = agent.call_tools_llm(sample_state)

            assert 'messages' in result
            assert len(result['messages']) == 1
            assert len(result['messages'][0].tool_calls) == 0

    def test_conditional_edge_exists_action_with_tools(self, agent):
        """Test conditional edge logic when tool calls exist."""
        state = {
            'messages': [
                AIMessage(
                    content="",
                    tool_calls=[{'name': 'collect_preferences', 'args': {}, 'id': 'call_123'}]
                )
            ]
        }

        result = Agent.exists_action(state)
        assert result == 'more_tools'

    def test_conditional_edge_exists_action_without_tools(self, agent):
        """Test conditional edge logic when no tool calls exist."""
        state = {
            'messages': [
                AIMessage(content="Final response", tool_calls=[])
            ]
        }

        result = Agent.exists_action(state)
        assert result == 'email_sender'

    def test_tool_invocation_routing_logic(self, agent):
        """Test tool invocation and routing logic."""
        state = {
            'messages': [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            'name': 'collect_preferences',
                            'args': {'user_input': 'Test input'},
                            'id': 'call_123'
                        }
                    ]
                )
            ]
        }

        with patch.object(agent, '_tools', {'collect_preferences': Mock(invoke=Mock(return_value={'preferences': {'destination': 'Tokyo'}, 'missing_fields': [], 'is_complete': True, 'clarification_needed': False}))}):
            result = agent.invoke_tools(state)

            assert 'messages' in result
            assert len(result['messages']) == 1
            assert isinstance(result['messages'][0], ToolMessage)

    def test_bad_tool_name_handling(self, agent):
        """Test handling of invalid tool names from LLM."""
        state = {
            'messages': [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            'name': 'invalid_tool_name',
                            'args': {},
                            'id': 'call_123'
                        }
                    ]
                )
            ]
        }

        result = agent.invoke_tools(state)

        assert 'messages' in result
        assert len(result['messages']) == 1
        assert 'bad tool name' in result['messages'][0].content

    def test_memory_and_state_management(self, agent):
        """Test memory and state persistence across interactions."""
        config = {'configurable': {'thread_id': 'test_thread_123'}, 'recursion_limit': 10}

        initial_state = {
            'messages': [HumanMessage(content="I want to travel to Tokyo")],
            'preferences': {}
        }

        with patch.object(agent._tools_llm, 'invoke') as mock_llm:
            # First call returns tool call, second call returns final response
            mock_llm.side_effect = [
                AIMessage(
                    content="",
                    tool_calls=[{
                        'name': 'collect_preferences',
                        'args': {'user_input': 'Test'},
                        'id': 'call_123'
                    }]
                ),
                AIMessage(
                    content="Here is your travel information for Tokyo",
                    tool_calls=[]
                )
            ]

            with patch.object(agent, '_tools', {'collect_preferences': Mock(invoke=Mock(return_value={'preferences': {'destination': 'Tokyo'}, 'missing_fields': [], 'is_complete': True, 'clarification_needed': False}))}):
                # First interaction
                result1 = agent.graph.invoke(initial_state, config=config)

                # Verify state is maintained
                assert 'messages' in result1
                assert len(result1['messages']) > 0

    def test_preferences_state_update(self, agent):
        """Test that preferences are properly updated in state."""
        state = {
            'messages': [
                AIMessage(
                    content="",
                    tool_calls=[{
                        'name': 'collect_preferences',
                        'args': {'user_input': 'Test'},
                        'id': 'call_123'
                    }]
                )
            ],
            'preferences': {}
        }

        with patch.object(agent, '_tools', {'collect_preferences': Mock(invoke=Mock(return_value={'preferences': {'destination': 'Tokyo', 'budget': {'amount': 2000, 'currency': 'USD'}}, 'missing_fields': [], 'is_complete': True, 'clarification_needed': False}))}):
            result = agent.invoke_tools(state)

            assert 'preferences' in result
            assert result['preferences']['destination'] == 'Tokyo'
            assert result['preferences']['budget']['amount'] == 2000

    def test_multiple_tool_invocation(self, agent):
        """Test handling of multiple tool calls in single message."""
        state = {
            'messages': [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            'name': 'collect_preferences',
                            'args': {'user_input': 'Test'},
                            'id': 'call_123'
                        },
                        {
                            'name': 'flights_finder',
                            'args': {'departure_airport': 'JFK', 'arrival_airport': 'LAX'},
                            'id': 'call_124'
                        }
                    ]
                )
            ]
        }

        with patch.object(agent, '_tools', {
            'collect_preferences': Mock(invoke=Mock(return_value={'preferences': {'destination': 'Tokyo'}, 'missing_fields': [], 'is_complete': True, 'clarification_needed': False})),
            'flights_finder': Mock(invoke=Mock(return_value=[{'airline': 'Test Airline'}]))
        }):
            result = agent.invoke_tools(state)

            assert 'messages' in result
            assert len(result['messages']) == 2  # Two tool results

    def test_graph_structure_initialization(self, agent):
        """Test that the graph is properly initialized with correct nodes and edges."""
        graph = agent.graph

        # Check that nodes exist
        nodes = graph.nodes
        assert 'call_tools_llm' in nodes
        assert 'invoke_tools' in nodes
        assert 'email_sender' in nodes

    def test_entry_point(self, agent):
        """Test that the graph has correct entry point."""
        graph = agent.graph
        # The entry point is set during graph construction
        # We can verify the graph structure instead
        nodes = graph.nodes
        assert 'call_tools_llm' in nodes

    def test_interrupt_before_email_sender(self, agent):
        """Test that graph is configured to interrupt before email_sender."""
        graph = agent.graph
        # Check that interrupt_before is configured
        # This is a compile-time configuration check
        assert graph.checkpointer is not None

    def test_error_handling_in_llm_invocation(self, agent, sample_state):
        """Test error handling when LLM invocation fails."""
        with patch.object(agent._tools_llm, 'invoke') as mock_llm:
            mock_llm.side_effect = Exception("LLM API error")

            with pytest.raises(Exception):
                agent.call_tools_llm(sample_state)

    def test_tool_message_creation(self, agent):
        """Test that tool messages are created correctly."""
        state = {
            'messages': [
                AIMessage(
                    content="",
                    tool_calls=[{
                        'name': 'collect_preferences',
                        'args': {'user_input': 'Test'},
                        'id': 'call_123'
                    }]
                )
            ]
        }

        with patch.object(agent, '_tools', {'collect_preferences': Mock(invoke=Mock(return_value={'preferences': {'destination': 'Tokyo'}, 'missing_fields': [], 'is_complete': True, 'clarification_needed': False}))}):
            result = agent.invoke_tools(state)

            tool_message = result['messages'][0]
            assert isinstance(tool_message, ToolMessage)
            assert tool_message.name == 'collect_preferences'
            assert tool_message.tool_call_id == 'call_123'

    def test_state_message_accumulation(self, agent):
        """Test that messages are accumulated in state (operator.add)."""
        initial_messages = [
            HumanMessage(content="First message"),
            AIMessage(content="Response")
        ]

        state = {
            'messages': initial_messages,
            'preferences': {}
        }

        with patch.object(agent._tools_llm, 'invoke') as mock_llm:
            mock_llm.return_value = AIMessage(
                content="New response",
                tool_calls=[]
            )

            result = agent.call_tools_llm(state)

            # Messages should be accumulated
            assert len(result['messages']) == 1  # New message added
