from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from .validation import ClaimItem, EvidenceQualityReport


class CompetitorProfile(BaseModel):
    """Structured extraction of an individual competitor's market position."""
    name: str = Field(description="Competitor name")
    url: str = Field(description="Main website URL")
    positioning: str = Field(description="Market positioning (e.g., Value, Premium, Enterprise, Developer-first)")
    pricing_tier: str = Field(description="Pricing level representation (e.g., ₹₹, ₹₹₹, or monthly rate)")
    key_services: List[str] = Field(default_factory=list, description="Core offerings or products")
    recent_change: str = Field(description="Notable recent product launch, price shift, or strategic pivot")
    strengths: List[str] = Field(default_factory=list, description="Identified competitive strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Identified competitive weaknesses or gaps")


class RawIntelligence(BaseModel):
    """Intermediate intelligence package produced by the Analyst Agent."""
    competitors: List[CompetitorProfile] = Field(default_factory=list)
    claims: List[ClaimItem] = Field(default_factory=list, description="Factual assertions awaiting validation")
    market_opportunities: List[str] = Field(default_factory=list, description="Identified market white spaces or gaps")
    recommended_actions: List[str] = Field(default_factory=list, description="Actionable strategic recommendations")


class MarketLandscape(BaseModel):
    """Competitive landscape overview across analyzed competitors."""
    industry: str
    target_company: str
    competitors: List[CompetitorProfile]


class ExecutiveReport(BaseModel):
    """Final, validated executive competitive intelligence report."""
    company_name: str
    industry: str
    analysis_period: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    executive_summary: str
    landscape: List[CompetitorProfile]
    market_opportunities: List[str]
    recommended_actions: List[str]
    evidence_quality: EvidenceQualityReport
