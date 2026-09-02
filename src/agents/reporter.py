import re
import logging
from typing import Dict, Any
from ..models.state import MarketIntelligenceState
from ..models.intelligence import ExecutiveReport
from ..services.pdf_generator import PDFReportGenerator

logger = logging.getLogger(__name__)


class ReporterAgent:
    """Compiles validated competitive findings into an executive report and generates corporate PDF."""

    def __init__(self, pdf_generator: PDFReportGenerator = None):
        self.pdf_generator = pdf_generator or PDFReportGenerator()

    def run(self, state: MarketIntelligenceState) -> Dict[str, Any]:
        company_name = state.get("company_name", "Our Organization")
        industry = state.get("industry", "Digital Services")
        period = state.get("analysis_period", "Current")
        intelligence = state.get("extracted_intelligence", {})
        val_report = state.get("validation_report", {})

        logger.info(f"Reporter Agent generating executive report for {company_name}...")

        competitors = intelligence.get("competitors", [])
        opportunities = intelligence.get("market_opportunities", [])
        actions = intelligence.get("recommended_actions", [])
        confidence = val_report.get("overall_confidence", 0.0)

        # Craft structured executive summary
        summary = (
            f"Competitive market evaluation for {company_name} across {len(competitors)} primary competitors in "
            f"the {industry} sector. Market research reveals significant bifurcation between low-cost automated providers "
            f"and high-ticket enterprise edge services. Key opportunity identified in addressing steep contract renewal price hikes "
            f"and offering managed support tiers for growing organizations. All findings have been audited with an overall evidence "
            f"confidence rating of {confidence}%."
        )

        executive_report = {
            "company_name": company_name,
            "industry": industry,
            "analysis_period": period,
            "executive_summary": summary,
            "landscape": competitors,
            "market_opportunities": opportunities,
            "recommended_actions": actions,
            "evidence_quality": val_report,
        }

        # Validate with Pydantic
        report_model = ExecutiveReport.model_validate(executive_report)
        report_dict = report_model.model_dump()

        # Generate downloadable PDF with sanitized safe filename
        safe_company = re.sub(r"[^a-zA-Z0-9_-]", "_", company_name.lower())
        safe_period = re.sub(r"[^a-zA-Z0-9_-]", "_", period.lower())
        run_id = f"{safe_company}_{safe_period}"
        pdf_path = self.pdf_generator.generate(run_id, report_dict)
        report_dict["pdf_path"] = pdf_path

        return {
            "final_report": report_dict,
            "current_stage": "completed",
        }
