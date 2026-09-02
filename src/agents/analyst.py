import logging
from typing import Dict, Any
from ..models.state import MarketIntelligenceState
from ..services.llm_provider import LLMService

logger = logging.getLogger(__name__)


class AnalystAgent:
    """Extracts structured competitor profiles, positioning, pricing, and claims from source chunks."""

    def __init__(self, llm_service: LLMService = None):
        self.llm = llm_service or LLMService()

    def run(self, state: MarketIntelligenceState) -> Dict[str, Any]:
        company_name = state.get("company_name", "Our Organization")
        industry = state.get("industry", "Digital Services")
        raw_sources = state.get("raw_sources", [])

        logger.info(f"Analyst Agent synthesizing intelligence across {len(raw_sources)} source chunks...")

        intelligence = self.llm.analyze_competitors(
            company_name=company_name,
            industry=industry,
            raw_sources=raw_sources,
        )

        return {
            "extracted_intelligence": intelligence,
            "current_stage": "analyzed",
        }
