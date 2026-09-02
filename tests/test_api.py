import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Multi-Agent" in data["service"]


def test_execute_research_and_fetch_run(client):
    payload = {
        "company_name": "iDesign",
        "competitor_urls": [
            "https://www.hostinger.com",
            "https://www.bluehost.com",
        ],
        "industry": "Web Hosting / Digital Services",
        "analysis_period": "Current / last 30 days",
        "demo_mode": True,
    }

    # 1. Trigger research
    response = client.post("/api/research/run", json=payload)
    assert response.status_code == 200
    res_data = response.json()

    run_id = res_data["run_id"]
    assert res_data["status"] == "completed"
    assert res_data["company_name"] == "iDesign"
    assert res_data["confidence_score"] > 0
    assert res_data["claims_validated"] > 0
    assert "pdf_download_url" in res_data

    # 2. Fetch specific run by ID
    get_res = client.get(f"/api/research/{run_id}")
    assert get_res.status_code == 200
    run_detail = get_res.json()
    assert run_detail["run_id"] == run_id
    assert run_detail["status"] == "completed"

    # 3. Download generated PDF
    pdf_res = client.get(f"/api/research/{run_id}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000

    # 4. List runs
    runs_res = client.get("/api/runs")
    assert runs_res.status_code == 200
    runs_list = runs_res.json()
    assert any(r["run_id"] == run_id for r in runs_list)
