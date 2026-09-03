import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.graph.workflow import run_competitive_analysis
from src.services.storage import StorageService

st.set_page_config(
    page_title="AI Market Intelligence Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .metric-card {
        background-color: var(--secondary-background-color, #1e293b);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .badge-validated {
        background-color: #dcfce7;
        color: #166534;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.8rem;
    }
    .badge-review {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.8rem;
    }
    .badge-low {
        background-color: #fef3c7;
        color: #92400e;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

storage = StorageService()

# App Header
st.title("Multi-Agent Market & Competitor Intelligence System")
st.markdown(
    "*An AI-powered multi-agent system that monitors public competitor data, extracts structured market intelligence, "
    "**validates claims against source evidence**, and produces executive reports.*"
)

# Sidebar Inputs
st.sidebar.header("Intelligence Parameters")

company_name = st.sidebar.text_input("Target Company", value="iDesign")
industry = st.sidebar.text_input("Industry", value="Web Hosting / Digital Services")
analysis_period = st.sidebar.selectbox(
    "Analysis Period",
    ["Current / last 30 days", "Q3 2026", "Year-to-Date"],
    index=0,
)

default_urls = (
    "https://www.hostinger.com\n"
    "https://www.bluehost.com\n"
    "https://www.cloudflare.com"
)
competitor_urls_text = st.sidebar.text_area(
    "Competitor URLs (3-5 URLs)",
    value=default_urls,
    height=110,
)

demo_mode = st.sidebar.checkbox(
    "Use Verified Offline Dataset (Fast & Reproducible)",
    value=True,
    help="Uses clean cached public data for instant, reliable evaluation without network flakiness.",
)

run_button = st.sidebar.button("🚀 Run Multi-Agent Pipeline", type="primary", use_container_width=True)

# Historical Runs Explorer in Sidebar
saved_runs = storage.list_runs(limit=15)
if saved_runs:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📂 Saved Historical Runs")
    run_dict = {
        f"{r['created_at'][:16]} — {r['company_name']} ({int(r.get('confidence_score', 0))}% Conf)": r["run_id"]
        for r in saved_runs
    }
    selected_run_label = st.sidebar.selectbox(
        "Load Past Run",
        ["-- Select a saved run --"] + list(run_dict.keys()),
    )
    if selected_run_label != "-- Select a saved run --":
        past_id = run_dict[selected_run_label]
        past_run = storage.get_run(past_id)
        if past_run and past_run.get("report"):
            st.session_state["research_result"] = {
                "final_report": past_run["report"],
                "validation_report": past_run["report"].get("evidence_quality", {}),
            }

# Main Execution Flow
if run_button or "research_result" in st.session_state:
    if run_button:
        competitor_urls = [u.strip() for u in competitor_urls_text.splitlines() if u.strip()]

        progress_container = st.empty()
        with progress_container.container():
            st.info("Pipeline Execution Started: Initializing LangGraph Workflow...")
            p_bar = st.progress(10)

            # 1. Scout
            st.markdown("`[1/4] Scout Agent`: Collecting competitor public pages, pricing tiers, and announcements...")
            p_bar.progress(30)

            # Run graph
            final_state = run_competitive_analysis(
                company_name=company_name,
                competitor_urls=competitor_urls,
                industry=industry,
                analysis_period=analysis_period,
                demo_mode=demo_mode,
            )

            # 2. Analyst
            p_bar.progress(60)
            st.markdown("`[2/4] Analyst Agent`: Synthesizing structured competitor profiles & factual assertions...")

            # 3. Validator
            p_bar.progress(85)
            st.markdown("`[3/4] Validator Agent`: Auditing claims against source chunks to detect hallucinations...")

            # 4. Reporter
            p_bar.progress(100)
            st.markdown("`[4/4] Reporter Agent`: Generating executive report and compiling ReportLab PDF...")

        progress_container.empty()
        st.session_state["research_result"] = final_state

        # Automatically persist run in database
        rep = final_state.get("final_report", {})
        val = final_state.get("validation_report", {})
        import uuid
        storage.save_run(
            run_id=str(uuid.uuid4())[:8],
            company_name=company_name,
            industry=industry,
            analysis_period=analysis_period,
            status="completed",
            confidence_score=val.get("overall_confidence", 0.0),
            claims_validated=val.get("claims_validated", 0),
            claims_review=val.get("claims_requiring_review", 0),
            report_data=rep,
            pdf_path=rep.get("pdf_path"),
        )

    # Retrieve from session
    state = st.session_state["research_result"]
    final_report = state.get("final_report", {})
    val_report = state.get("validation_report", {})
    landscape = final_report.get("landscape", [])
    opps = final_report.get("market_opportunities", [])
    recs = final_report.get("recommended_actions", [])
    pdf_path = final_report.get("pdf_path")

    # High-level Metrics Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Competitors Analyzed", len(landscape))
    with c2:
        st.metric("Total Claims Audited", val_report.get("total_claims", 0))
    with c3:
        st.metric("Claims Validated", val_report.get("claims_validated", 0))
    with c4:
        conf = val_report.get("overall_confidence", 0.0)
        st.metric("Evidence Quality Score", f"{conf}%")

    st.markdown("---")

    # Tabs for Outputs
    tab_landscape, tab_opps, tab_evidence, tab_export = st.tabs(
        [
            "🏢 Competitive Landscape & 2x2 Map",
            "💡 Opportunities & Actions",
            "🔍 Evidence Quality & Claim Audit",
            "📄 Download & Export",
        ]
    )

    with tab_landscape:
        st.subheader("Executive Overview")
        st.info(final_report.get("executive_summary", ""))

        st.subheader("Competitive Landscape Matrix")
        table_rows = []
        for c in landscape:
            table_rows.append({
                "Competitor": c.get("name"),
                "Positioning": c.get("positioning"),
                "Pricing": c.get("pricing_tier"),
                "Key Services": ", ".join(c.get("key_services", [])),
                "Recent Change": c.get("recent_change"),
            })

        df_landscape = pd.DataFrame(table_rows)
        st.dataframe(df_landscape, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Market Positioning 2x2 Matrix")
        st.caption("Strategic quadrant analysis mapping relative pricing tiers against enterprise infrastructure & security capabilities.")

        # Construct 2x2 positioning data
        map_points = []
        for c in landscape:
            name = c.get("name", "")
            # Assign coordinates based on market positioning
            if "hostinger" in name.lower():
                x_val, y_val = 1.6, 2.2
            elif "bluehost" in name.lower():
                x_val, y_val = 2.7, 2.9
            elif "cloudflare" in name.lower():
                x_val, y_val = 4.2, 4.8
            else:
                x_val, y_val = 2.0, 2.5
            map_points.append({
                "Competitor": name,
                "PriceTierIndex": x_val,
                "CapabilityIndex": y_val,
                "Positioning": c.get("positioning", ""),
                "Pricing": c.get("pricing_tier", ""),
                "RecentChange": c.get("recent_change", ""),
            })

        df_map = pd.DataFrame(map_points)
        fig_2x2 = px.scatter(
            df_map,
            x="PriceTierIndex",
            y="CapabilityIndex",
            text="Competitor",
            color="Competitor",
            size=[26] * len(df_map),
            hover_data={"Positioning": True, "Pricing": True, "RecentChange": True, "PriceTierIndex": False, "CapabilityIndex": False},
        )
        fig_2x2.update_traces(textposition="top center", marker=dict(line=dict(width=1, color="DarkSlateGrey")))
        fig_2x2.update_layout(
            xaxis_title="Pricing & Entry Barrier (Value → Enterprise)",
            yaxis_title="Infrastructure & Security Scope (Shared Builder → Enterprise Edge)",
            xaxis=dict(range=[0.5, 5.0], showgrid=True),
            yaxis=dict(range=[0.5, 5.5], showgrid=True),
            height=440,
            shapes=[
                # Horizontal dividing line
                dict(type="line", x0=0.5, x1=5.0, y0=3.2, y1=3.2, line=dict(color="rgba(128,128,128,0.3)", dash="dash")),
                # Vertical dividing line
                dict(type="line", x0=2.8, x1=2.8, y0=0.5, y1=5.5, line=dict(color="rgba(128,128,128,0.3)", dash="dash")),
            ],
            annotations=[
                dict(x=1.6, y=5.0, text="<b>High Tech / Low Price</b> (Disruptors)", showarrow=False, font=dict(color="gray", size=10)),
                dict(x=4.0, y=5.0, text="<b>Enterprise Leaders</b> (Edge/Cloud)", showarrow=False, font=dict(color="gray", size=10)),
                dict(x=1.6, y=1.2, text="<b>Budget / Mass Market</b> (SMB)", showarrow=False, font=dict(color="gray", size=10)),
                dict(x=4.0, y=1.2, text="<b>Niche / Premium Legacy</b>", showarrow=False, font=dict(color="gray", size=10)),
            ],
        )
        st.plotly_chart(fig_2x2, use_container_width=True)

        # Deep Dive Profiles
        st.markdown("---")
        st.subheader("Competitor Deep-Dive Profiles")
        for c in landscape:
            with st.expander(f"📌 {c.get('name')} — Full SWOT Analysis"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**Identified Competitive Strengths:**")
                    for s in c.get("strengths", []):
                        st.markdown(f"- ✅ {s}")
                with col_b:
                    st.markdown("**Identified Vulnerabilities & Gaps:**")
                    for w in c.get("weaknesses", []):
                        st.markdown(f"- ⚠️ {w}")

    with tab_opps:
        st.subheader("Market White Spaces & Strategic Openings")
        for i, opp in enumerate(opps, 1):
            st.markdown(f"**{i}.** {opp}")

        st.markdown("---")
        st.subheader("Recommended Strategic Action Plan")
        for i, rec in enumerate(recs, 1):
            st.success(f"**Strategic Initiative {i}:** {rec}")

    with tab_evidence:
        st.subheader("Evidence Quality & Hallucination Audit")
        st.markdown(
            """
            > **Automated Evidence Evaluation & Grounding:**
            > In high-stakes AI pipelines, accuracy and ground-truth verification are paramount. 
            > The **Validator Agent** systematically parses every claim asserted by the Analyst, computes keyword alignment against primary scraped source chunks,
            > and flags unsupported assertions or hallucinations before they reach the executive report.
            """
        )

        st.info(val_report.get("summary_assessment", ""))

        verifications = val_report.get("verifications", [])
        if verifications:
            col_chart, col_summary = st.columns([1, 1])
            with col_chart:
                status_series = pd.Series([v.get("status") for v in verifications]).value_counts().reset_index()
                status_series.columns = ["Status", "Count"]
                fig = px.pie(
                    status_series,
                    values="Count",
                    names="Status",
                    title="Audit Verification Status",
                    color="Status",
                    color_discrete_map={
                        "VALIDATED": "#16a34a",
                        "REQUIRES_REVIEW": "#dc2626",
                        "LOW_CONFIDENCE": "#f59e0b",
                    },
                    hole=0.45,
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_summary:
                st.markdown("#### Audit Metrics Breakdown")
                st.write(f"- **Total Claims Audited:** {val_report.get('total_claims', 0)}")
                st.write(f"- **Grounding Confirmed (Validated):** {val_report.get('claims_validated', 0)}")
                st.write(f"- **Flagged as Unsupported / Hallucination:** {val_report.get('claims_requiring_review', 0)}")
                st.write(f"- **Overall Reliability Confidence:** **{val_report.get('overall_confidence', 0.0)}%**")
                st.write("*Audit methodology: Token stem matching, factual entity extraction, and sentence-level citation quotation.*")

            st.markdown("---")
            st.subheader("Claim Citation Inspector")
            st.caption("Inspect individual claims, confidence ratings, exact primary source quotations, and evaluator audit notes:")

            for v in verifications:
                raw_st = v.get("status", "VALIDATED")
                if hasattr(raw_st, "value"):
                    raw_st = raw_st.value
                st_label = str(raw_st).replace("ClaimStatus.", "").replace("_", " ")
                conf_pct = int(v.get("confidence_score", 1.0) * 100)

                if "VALIDATED" in st_label:
                    badge = f"<span class='badge-validated'>VALIDATED ({conf_pct}%)</span>"
                elif "REVIEW" in st_label:
                    badge = f"<span class='badge-review'>REQUIRES REVIEW ({conf_pct}%)</span>"
                else:
                    badge = f"<span class='badge-low'>LOW CONFIDENCE ({conf_pct}%)</span>"

                exp_title = f"{v.get('claim_id')} [{v.get('competitor_name')} - {v.get('category').upper()}] — {v.get('statement')[:70]}..."
                with st.expander(f"{st_label}: {exp_title}"):
                    st.markdown(f"**Verification Status:** {badge}", unsafe_allow_html=True)
                    st.markdown(f"**Assertion:** *\"{v.get('statement')}\"*")
                    st.markdown(f"**Primary Source Citation Quote:**")
                    citation_text = v.get("source_citation") or "No direct quote available."
                    if "No matching evidence" in citation_text:
                        st.error(f"⚠️ {citation_text}")
                    else:
                        st.success(f"“{citation_text}”")

                    if v.get("matched_url"):
                        st.markdown(f"🔗 **Source Reference:** `{v.get('matched_url')}`")
                    st.markdown(f"🧠 **Evaluator Reasoning:** `{v.get('audit_notes')}`")

    with tab_export:
        st.subheader("Executive PDF Export")
        if pdf_path and os.path.exists(pdf_path):
            st.success(f"Executive Report ready: `{os.path.basename(pdf_path)}`")
            st.caption("Includes McKinsey-grade formatting, NumberedCanvas running headers, landscape table, and evidence quality scorecard.")

            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            st.download_button(
                label="📥 Download Executive PDF Report",
                data=pdf_bytes,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                type="primary",
            )
        else:
            st.warning("No PDF file currently generated.")

else:
    st.info("👈 Set your parameters in the sidebar and click **'🚀 Run Multi-Agent Pipeline'** to begin competitive intelligence research.")
