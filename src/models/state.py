from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class SourceChunk(BaseModel):
    """Represents a piece of raw content collected by the Scout Agent."""
    chunk_id: str = Field(description="Unique hash or ID for this content chunk")
    competitor_name: str = Field(description="Name of the competitor")
    url: str = Field(description="Source URL")
    title: str = Field(default="", description="Page or section title")
    content: str = Field(description="Cleaned extracted text content")
    scraped_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    content_type: str = Field(default="webpage", description="pricing | product | news | homepage")


class MarketIntelligenceState(TypedDict, total=False):
    """LangGraph state passed through Scout -> Analyst -> Validator -> Reporter."""
    company_name: str
    competitor_urls: List[str]
    industry: str
    analysis_period: str
    demo_mode: bool
    raw_sources: List[Dict[str, Any]]
    extracted_intelligence: Optional[Dict[str, Any]]
    validation_report: Optional[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]
    errors: List[str]
    current_stage: str
