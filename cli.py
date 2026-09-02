import argparse
import sys

# Ensure UTF-8 output on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.graph.workflow import run_competitive_analysis


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent Market & Competitor Intelligence System — CLI Runner"
    )
    parser.add_argument("--company", default="iDesign", help="Target company name (default: iDesign)")
    parser.add_argument(
        "--industry",
        default="Web Hosting / Digital Services",
        help="Industry vertical (default: Web Hosting / Digital Services)",
    )
    parser.add_argument(
        "--period",
        default="Current / last 30 days",
        help="Analysis time window",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        default=True,
        help="Run in reproducible offline demo mode using verified fixtures",
    )
    parser.add_argument(
        "--competitors",
        nargs="+",
        default=[
            "https://www.hostinger.com",
            "https://www.bluehost.com",
            "https://www.cloudflare.com",
        ],
        help="List of competitor URLs",
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print(" AI MARKET INTELLIGENCE AGENT -- MULTI-AGENT PIPELINE")
    print("=" * 70)
    print(f" Target Company : {args.company}")
    print(f" Industry       : {args.industry}")
    print(f" Period         : {args.period}")
    print(f" Competitors    : {len(args.competitors)} URLs")
    print("=" * 70)
    print("\n[1/4] Scout Agent    : Ingesting & chunking competitor sources...")
    print("[2/4] Analyst Agent  : Extracting positioning, pricing, and claims...")
    print("[3/4] Validator Agent: Cross-referencing claims against citations...")
    print("[4/4] Reporter Agent : Synthesizing executive report & PDF...")

    result = run_competitive_analysis(
        company_name=args.company,
        competitor_urls=args.competitors,
        industry=args.industry,
        analysis_period=args.period,
        demo_mode=args.demo,
    )

    rep = result.get("final_report", {})
    val = result.get("validation_report", {})

    print("\n" + "-" * 70)
    print(" [*] COMPETITIVE LANDSCAPE MATRIX")
    print("-" * 70)
    header = f"{'COMPETITOR':<14} | {'POSITIONING':<24} | {'PRICING':<16} | {'RECENT PIVOT'}"
    print(header)
    print("-" * 70)
    for c in rep.get("landscape", []):
        row = f"{c.get('name', ''):<14} | {c.get('positioning', ''):<24} | {c.get('pricing_tier', ''):<16} | {c.get('recent_change', '')[:28]}..."
        print(row)

    print("\n" + "-" * 70)
    print(" [?] EVIDENCE QUALITY & AI EVALUATION (LABELBOX AUDIT)")
    print("-" * 70)
    print(f" Total Claims Audited     : {val.get('total_claims')}")
    print(f" Validated Ground-Truth   : {val.get('claims_validated')}")
    print(f" Flagged for Review       : {val.get('claims_requiring_review')}")
    print(f" Overall Confidence Score : {val.get('overall_confidence')}%")
    print(f"\n Assessment: {val.get('summary_assessment')}")

    print("\n" + "-" * 70)
    print(" [+] EXECUTIVE REPORT GENERATED")
    print("-" * 70)
    print(f" PDF Report Location: {rep.get('pdf_path')}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
