"""LangGraph orchestration for the travel-planning agent."""

import operator
import os
from typing import Annotated, Any, Callable, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from agents.nodes.budget_estimator import BudgetEstimatorNode
from agents.nodes.destination_search import DestinationSearchNode
from agents.nodes.itinerary_synthesizer import ItinerarySynthesizerNode
from agents.nodes.preference_collector import PreferenceCollectorNode
from agents.nodes.route_planner import RoutePlannerNode
from agents.nodes.safety_reviewer import SafetyReviewerNode

load_dotenv()


class AgentState(TypedDict, total=False):
    """Shared state passed between Phase 2 workflow nodes."""

    messages: Annotated[list[AnyMessage], operator.add]
    user_id: str
    preferences: dict
    missing_fields: list[str]
    preferences_complete: bool
    clarification_count: int
    places: list[dict]
    routes: list[dict]
    budget: dict
    itinerary: dict


EMAIL_SYSTEM_PROMPT = """Convert the supplied travel plan into a valid HTML email.
Return only the HTML document. Preserve headings, tables, warnings, prices, and
confirmation items. Do not invent facts, bookings, prices, or links.
"""


class Agent:
    """Build and expose the Phase 2 travel planning workflow."""

    def __init__(
        self,
        *,
        preference_llm=None,
        destination_llm=None,
        email_llm=None,
        preference_memory=None,
        email_transport: Callable[[str, str, str, str], Any] | None = None,
        checkpointer=None,
        verbose: bool = False,
    ):
        self._email_llm = email_llm
        self._email_transport = email_transport or self._send_via_sendgrid

        preference_node = PreferenceCollectorNode(
            llm=preference_llm,
            memory=preference_memory,
        )
        destination_node = DestinationSearchNode(llm=destination_llm)
        route_node = RoutePlannerNode()
        budget_node = BudgetEstimatorNode()
        itinerary_node = ItinerarySynthesizerNode()
        safety_node = SafetyReviewerNode()

        builder = StateGraph(AgentState)
        builder.add_node('preference_collector', preference_node)
        builder.add_node('destination_search', destination_node)
        builder.add_node('route_planner', route_node)
        builder.add_node('budget_estimator', budget_node)
        builder.add_node('itinerary_synthesizer', itinerary_node)
        builder.add_node('safety_reviewer', safety_node)
        builder.add_node('email_sender', self.email_sender)

        builder.set_entry_point('preference_collector')
        builder.add_conditional_edges(
            'preference_collector',
            self._route_after_preferences,
            {
                'complete': 'destination_search',
                'incomplete': END,
            },
        )
        builder.add_edge('destination_search', 'route_planner')
        builder.add_edge('route_planner', 'budget_estimator')
        builder.add_edge('budget_estimator', 'itinerary_synthesizer')
        builder.add_edge('itinerary_synthesizer', 'safety_reviewer')
        builder.add_edge('safety_reviewer', 'email_sender')
        builder.add_edge('email_sender', END)

        self.graph = builder.compile(
            checkpointer=checkpointer or MemorySaver(),
            interrupt_before=['email_sender'],
        )

        if verbose:
            print(self.graph.get_graph().draw_mermaid())

    @staticmethod
    def _route_after_preferences(state: AgentState) -> str:
        return 'complete' if state.get('preferences_complete') else 'incomplete'

    def email_sender(self, state: AgentState) -> dict:
        """Render the reviewed plan to HTML and send it through the transport."""

        content = self._email_source_content(state)
        llm = self._email_llm or self._build_email_llm()
        response = llm.invoke(
            [
                SystemMessage(content=EMAIL_SYSTEM_PROMPT),
                HumanMessage(content=content),
            ]
        )

        sender = self._required_env('FROM_EMAIL')
        receiver = self._required_env('TO_EMAIL')
        subject = self._required_env('EMAIL_SUBJECT')
        self._email_transport(sender, receiver, subject, response.content)

        return {
            'messages': [AIMessage(content="邮件已成功发送。")],
        }

    @staticmethod
    def _email_source_content(state: AgentState) -> str:
        messages = state.get('messages', [])
        if messages:
            return str(messages[-1].content)
        itinerary = state.get('itinerary', {})
        if itinerary:
            return str(itinerary)
        raise ValueError("No reviewed itinerary is available for email")

    @staticmethod
    def _build_email_llm():
        return ChatOpenAI(
            model="qwen3.7-max",
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=(
                "https://ws-701qztd515ek1e5g.cn-beijing.maas.aliyuncs.com/"
                "compatible-mode/v1"
            ),
            temperature=0.1,
        )

    @staticmethod
    def _required_env(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise ValueError(f"Missing required environment variable: {name}")
        return value

    @staticmethod
    def _send_via_sendgrid(
        sender: str,
        receiver: str,
        subject: str,
        html_content: str,
    ) -> None:
        api_key = Agent._required_env('SENDGRID_API_KEY')
        message = Mail(
            from_email=sender,
            to_emails=receiver,
            subject=subject,
            html_content=html_content,
        )
        SendGridAPIClient(api_key).send(message)
