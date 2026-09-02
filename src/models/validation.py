from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ClaimStatus(str, Enum):
    VALIDATED = "VALIDATED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    CONTRADICTED = "CONTRADICTED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"


class ClaimItem(BaseModel):
    """An individual factual claim extracted by the Analyst Agent."""
    claim_id: str = Field(description="Unique identifier for the claim")
    competitor_name: str = Field(description="Name of the competitor this claim refers to")
    category: str = Field(description="Category: positioning | pricing | key_services | recent_change | swot")
    statement: str = Field(description="The factual proposition asserted by the Analyst")
    claimed_source_ids: List[str] = Field(default_factory=list, description="IDs of source chunks claimed to back this")


class ClaimVerification(BaseModel):
    """An audited claim with citation evidence, confidence score, and evaluation rationale."""
    claim_id: str
    competitor_name: str
    category: str
    statement: str
    status: ClaimStatus
    confidence_score: float = Field(ge=0.0, le=1.0, description="Verification confidence between 0.0 and 1.0")
    source_citation: Optional[str] = Field(default=None, description="Direct quote or snippet from source chunk")
    matched_source_id: Optional[str] = Field(default=None, description="ID of the matching source chunk")
    matched_url: Optional[str] = Field(default=None, description="Source URL where evidence was verified")
    audit_notes: str = Field(default="", description="Evaluator reasoning explaining why it passed or needs review")


class EvidenceQualityReport(BaseModel):
    """Overall evidence quality metrics produced by the Validator Agent."""
    total_claims: int = Field(default=0)
    claims_validated: int = Field(default=0)
    claims_requiring_review: int = Field(default=0)
    overall_confidence: float = Field(default=0.0, description="Percentage confidence (e.g., 91.0)")
    verifications: List[ClaimVerification] = Field(default_factory=list)
    summary_assessment: str = Field(default="", description="Executive summary of data reliability and source coverage")
