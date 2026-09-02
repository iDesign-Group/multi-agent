import os
import pytest
from src.agents.scout import ScoutAgent
from src.agents.analyst import AnalystAgent
from src.agents.reporter import ReporterAgent
from src.services.scraper import ScraperService


def test_scout_agent_collection():
    agent = ScoutAgent()
    state = {
        "competitor_urls": ["https://www.hostinger.com"],
        "demo_mode": True,
    }
    update = agent.run(state)
    assert "raw_sources" in update
    assert len(update["raw_sources"]) > 0
    chunk = update["raw_sources"][0]
    assert "chunk_id" in chunk
    assert "competitor_name" in chunk
    assert "Hostinger" in chunk["competitor_name"]
    assert update["current_stage"] == "scouted"


def test_analyst_agent_synthesis():
    agent = AnalystAgent()
    state = {
        "company_name": "iDesign",
        "industry": "Web Hosting",
        "raw_sources": [
            {
                "chunk_id": "test_chk_1",
                "competitor_name": "Hostinger",
                "url": "https://www.hostinger.com/pricing",
                "content": "Hostinger plans start at ₹149/month with AI builder.",
            }
        ],
    }
    update = agent.run(state)
    assert "extracted_intelligence" in update
    intel = update["extracted_intelligence"]
    assert len(intel["competitors"]) > 0
    assert len(intel["claims"]) > 0
    assert update["current_stage"] == "analyzed"


import tempfile

def test_reporter_agent_generates_pdf():
    with tempfile.TemporaryDirectory() as tmp_dir:
        from src.services.pdf_generator import PDFReportGenerator
        pdf_gen = PDFReportGenerator(output_dir=tmp_dir)
        agent = ReporterAgent(pdf_generator=pdf_gen)

        state = {
            "company_name": "iDesign",
            "industry": "Web Hosting / Digital Services",
            "analysis_period": "Last 30 Days",
            "extracted_intelligence": {
                "competitors": [
                    {
                        "name": "Hostinger",
                        "url": "https://www.hostinger.com",
                        "positioning": "Value",
                        "pricing_tier": "₹149/mo",
                        "key_services": ["Shared", "VPS"],
                        "recent_change": "Refreshed KVM VPS",
                        "strengths": ["Low cost"],
                        "weaknesses": ["No phone support"],
                    }
                ],
                "market_opportunities": ["Price transparency"],
                "recommended_actions": ["Launch fixed renewal pricing"],
            },
            "validation_report": {
                "total_claims": 5,
                "claims_validated": 4,
                "claims_requiring_review": 1,
                "overall_confidence": 80.0,
                "verifications": [],
                "summary_assessment": "4 of 5 claims verified.",
            },
        }

        update = agent.run(state)
        assert "final_report" in update
        report = update["final_report"]
        assert "pdf_path" in report
        assert os.path.exists(report["pdf_path"])
        assert update["current_stage"] == "completed"
