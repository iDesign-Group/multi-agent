import logging
from typing import Dict, Any, List
from ..models.state import MarketIntelligenceState, SourceChunk
from ..services.scraper import ScraperService

logger = logging.getLogger(__name__)


class ScoutAgent:
    """Collects raw competitor intelligence from public websites, pricing tables, and feeds."""

    def __init__(self, scraper_service: ScraperService = None):
        self.scraper = scraper_service or ScraperService()

    def run(self, state: MarketIntelligenceState) -> Dict[str, Any]:
        competitor_urls = state.get("competitor_urls", [])
        demo_mode = state.get("demo_mode", True)
        all_chunks: List[Dict[str, Any]] = []

        logger.info(f"Scout Agent initiating collection for {len(competitor_urls)} competitors...")

        for url in competitor_urls:
            url_clean = url.strip()
            if not url_clean:
                continue

            comp_name = self.scraper._derive_competitor_name(url_clean)

            if demo_mode:
                # Use verified rich fixture chunks for consistent evaluation
                chunks = self.scraper.fetch_demo_chunks(comp_name)
                if not chunks:
                    chunks = self.scraper.fetch_page(url_clean, competitor_name=comp_name)
            else:
                chunks = self.scraper.fetch_page(url_clean, competitor_name=comp_name)

            for chunk in chunks:
                all_chunks.append(chunk.model_dump())

        return {
            "raw_sources": all_chunks,
            "current_stage": "scouted",
        }
