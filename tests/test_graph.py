import os
import pytest
from src.graph.workflow import create_market_intelligence_graph, run_competitive_analysis


def test_graph_compilation():
    graph = create_market_intelligence_graph()
    assert graph is not None
    # Verify node names in graph
    assert "scout" in graph.nodes
    assert "analyst" in graph.nodes
    assert "validator" in graph.nodes
    assert "reporter" in graph.nodes


def test_full_pipeline_execution():
    result = run_competitive_analysis(
        company_name="iDesign",
        competitor_urls=[
            "https://www.hostinger.com",
            "https://www.bluehost.com",
            "https://www.cloudflare.com",
        ],
        industry="Web Hosting / Digital Services",
        analysis_period="Current / last 30 days",
        demo_mode=True,
    )

    assert result["current_stage"] == "completed"
    assert len(result["raw_sources"]) > 0

    # Verify extraction
    intel = result["extracted_intelligence"]
    assert len(intel["competitors"]) == 3
    assert len(intel["claims"]) > 0

    # Verify validator
    val_report = result["validation_report"]
    assert val_report["total_claims"] > 0
    assert val_report["claims_validated"] >= 1
    assert val_report["overall_confidence"] > 0.0

    # Verify reporter & PDF
    final_report = result["final_report"]
    assert final_report["company_name"] == "iDesign"
    assert len(final_report["landscape"]) == 3
    assert len(final_report["market_opportunities"]) > 0
    assert len(final_report["recommended_actions"]) > 0
    assert os.path.exists(final_report["pdf_path"])
