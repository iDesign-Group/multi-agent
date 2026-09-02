import logging
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END

from ..models.state import MarketIntelligenceState
from ..agents.scout import ScoutAgent
from ..agents.analyst import AnalystAgent
from ..agents.validator import ValidatorAgent
from ..agents.reporter import ReporterAgent

logger = logging.getLogger(__name__)


def create_market_intelligence_graph():
    """Constructs the compiled LangGraph workflow:

    Scout -> Analyst -> Validator -> Reporter
    """
    scout_agent = ScoutAgent()
    analyst_agent = AnalystAgent()
    validator_agent = ValidatorAgent()
    reporter_agent = ReporterAgent()

    workflow = StateGraph(MarketIntelligenceState)

    # Define nodes
    workflow.add_node("scout", scout_agent.run)
    workflow.add_node("analyst", analyst_agent.run)
    workflow.add_node("validator", validator_agent.run)
    workflow.add_node("reporter", reporter_agent.run)

    # Define linear state transitions
    workflow.add_edge(START, "scout")
    workflow.add_edge("scout", "analyst")
    workflow.add_edge("analyst", "validator")
    workflow.add_edge("validator", "reporter")
    workflow.add_edge("reporter", END)

    return workflow.compile()


def run_competitive_analysis(
    company_name: str,
    competitor_urls: List[str],
    industry: str = "Web Hosting / Digital Services",
    analysis_period: str = "Last 30 Days",
    demo_mode: bool = True,
) -> Dict[str, Any]:
    """High-level runner executing the compiled LangGraph state machine."""
    app = create_market_intelligence_graph()

    initial_state: MarketIntelligenceState = {
        "company_name": company_name,
        "competitor_urls": competitor_urls,
        "industry": industry,
        "analysis_period": analysis_period,
        "demo_mode": demo_mode,
        "raw_sources": [],
        "extracted_intelligence": None,
        "validation_report": None,
        "final_report": None,
        "errors": [],
        "current_stage": "initialized",
    }

    logger.info(f"Executing Market Intelligence Graph for {company_name}...")
    final_state = app.invoke(initial_state)
    return final_state
