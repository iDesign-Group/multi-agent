import pytest
from src.agents.validator import ValidatorAgent
from src.models.validation import ClaimStatus


@pytest.fixture
def sample_source_chunks():
    return [
        {
            "chunk_id": "chk_hostinger_01",
            "competitor_name": "Hostinger",
            "url": "https://www.hostinger.com/pricing",
            "content": "Hostinger provides aggressive value-tier web hosting starting at ₹149/month with free domain, free website builder, and unlimited SSL certificates. Absence of phone customer support, relying strictly on 24/7 live chat.",
        },
        {
            "chunk_id": "chk_bluehost_01",
            "competitor_name": "Bluehost",
            "url": "https://www.bluehost.com/hosting",
            "content": "Bluehost is an officially WordPress-recommended hosting provider starting at ₹279/month. Includes customized WordPress onboarding wizards and 24/7 phone support.",
        },
    ]


def test_validator_detects_grounded_claim(sample_source_chunks):
    validator = ValidatorAgent()
    claim = {
        "claim_id": "CLM-001",
        "competitor_name": "Hostinger",
        "category": "pricing",
        "statement": "Hostinger web hosting plans start at ₹149/month with free domain and SSL.",
        "claimed_source_ids": ["chk_hostinger_01"],
    }

    result = validator.evaluate_claim(claim, sample_source_chunks)

    assert result.status == ClaimStatus.VALIDATED
    assert result.confidence_score >= 0.75
    assert "₹149/month" in result.source_citation
    assert "Grounding verified" in result.audit_notes


def test_validator_flags_unsupported_hallucination(sample_source_chunks):
    validator = ValidatorAgent()
    # Hallucinated statement with zero support in source text
    claim = {
        "claim_id": "CLM-002",
        "competitor_name": "Bluehost",
        "category": "features",
        "statement": "Bluehost offers free unlimited GPU compute instances for AI inference to all shared hosting subscribers.",
        "claimed_source_ids": ["chk_bluehost_01"],
    }

    result = validator.evaluate_claim(claim, sample_source_chunks)

    assert result.status == ClaimStatus.REQUIRES_REVIEW
    assert result.confidence_score <= 0.35
    assert "potential hallucination" in result.audit_notes.lower()


def test_validator_run_computes_evidence_quality_metrics(sample_source_chunks):
    validator = ValidatorAgent()

    state = {
        "raw_sources": sample_source_chunks,
        "extracted_intelligence": {
            "claims": [
                {
                    "claim_id": "CLM-001",
                    "competitor_name": "Hostinger",
                    "category": "pricing",
                    "statement": "Hostinger web hosting plans start at ₹149/month with free domain.",
                },
                {
                    "claim_id": "CLM-002",
                    "competitor_name": "Hostinger",
                    "category": "support",
                    "statement": "Hostinger relies strictly on 24/7 live chat with no phone support.",
                },
                {
                    "claim_id": "CLM-003",
                    "competitor_name": "Hostinger",
                    "category": "features",
                    "statement": "Hostinger provides quantum computing access to all basic tier users.",
                },
            ]
        },
    }

    update = validator.run(state)
    val_report = update["validation_report"]

    assert val_report["total_claims"] == 3
    assert val_report["claims_validated"] == 2
    assert val_report["claims_requiring_review"] == 1
    assert val_report["overall_confidence"] == pytest.approx(66.7, rel=1e-1)
    assert update["current_stage"] == "validated"
