import os
import uuid
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, Field

from ..graph.workflow import run_competitive_analysis
from ..services.storage import StorageService

app = FastAPI(
    title="Multi-Agent Market & Competitor Intelligence System",
    description="Automated competitive research pipeline powered by LangGraph with Scout, Analyst, Validator, and Reporter agents.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage = StorageService()


class ResearchRequest(BaseModel):
    company_name: str = Field(default="iDesign", examples=["iDesign"])
    competitor_urls: List[str] = Field(
        default=["https://www.hostinger.com", "https://www.bluehost.com", "https://www.cloudflare.com"],
        examples=[["https://www.hostinger.com", "https://www.bluehost.com", "https://www.cloudflare.com"]],
    )
    industry: str = Field(default="Web Hosting / Digital Services", examples=["Web Hosting / Digital Services"])
    analysis_period: str = Field(default="Current / last 30 days", examples=["Current / last 30 days"])
    demo_mode: bool = Field(default=True, description="True uses offline verified fixtures; False performs live web scraping")


class ResearchResponse(BaseModel):
    run_id: str
    status: str
    company_name: str
    industry: str
    analysis_period: str
    confidence_score: float
    claims_validated: int
    claims_requiring_review: int
    pdf_download_url: Optional[str] = None
    report: Optional[Dict[str, Any]] = None


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Market Intelligence Multi-Agent System",
        "version": "1.0.0",
    }


@app.post("/api/research/run", response_model=ResearchResponse)
def execute_research(request: ResearchRequest):
    run_id = str(uuid.uuid4())[:8]

    try:
        final_state = run_competitive_analysis(
            company_name=request.company_name,
            competitor_urls=request.competitor_urls,
            industry=request.industry,
            analysis_period=request.analysis_period,
            demo_mode=request.demo_mode,
        )

        final_report = final_state.get("final_report", {})
        val_report = final_state.get("validation_report", {})

        confidence = val_report.get("overall_confidence", 0.0)
        validated_count = val_report.get("claims_validated", 0)
        review_count = val_report.get("claims_requiring_review", 0)
        pdf_path = final_report.get("pdf_path")

        storage.save_run(
            run_id=run_id,
            company_name=request.company_name,
            industry=request.industry,
            analysis_period=request.analysis_period,
            status="completed",
            confidence_score=confidence,
            claims_validated=validated_count,
            claims_review=review_count,
            report_data=final_report,
            pdf_path=pdf_path,
        )

        return ResearchResponse(
            run_id=run_id,
            status="completed",
            company_name=request.company_name,
            industry=request.industry,
            analysis_period=request.analysis_period,
            confidence_score=confidence,
            claims_validated=validated_count,
            claims_requiring_review=review_count,
            pdf_download_url=f"/api/research/{run_id}/pdf" if pdf_path else None,
            report=final_report,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution error: {str(e)}")


@app.get("/api/research/{run_id}", response_model=Dict[str, Any])
def get_research_run(run_id: str):
    run = storage.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Research run '{run_id}' not found.")
    return run


@app.get("/api/research/{run_id}/pdf")
def download_pdf(run_id: str):
    run = storage.get_run(run_id)
    if not run or not run.get("pdf_path"):
        raise HTTPException(status_code=404, detail="PDF report not found for this run.")

    pdf_path = run["pdf_path"]
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Report file not found on disk.")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(pdf_path),
    )


@app.get("/api/runs", response_model=List[Dict[str, Any]])
def list_runs():
    return storage.list_runs()
