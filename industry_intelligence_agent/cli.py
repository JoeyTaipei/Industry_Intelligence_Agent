"""Command-line interface for the Industry Intelligence Agent."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from industry_intelligence_agent.analysis.brief import generate_brief
from industry_intelligence_agent.collectors.financials import collect_price_indicators
from industry_intelligence_agent.collectors.news import collect_news
from industry_intelligence_agent.collectors.registry import lookup_company
from industry_intelligence_agent.collectors.reports import collect_configured_reports
from industry_intelligence_agent.config import load_config, load_env
from industry_intelligence_agent.exporters.csv_json import export_brief, export_documents
from industry_intelligence_agent.logging_config import setup_logging
from industry_intelligence_agent.storage.database import init_db, save_brief, save_documents

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="industry-intelligence-agent",
        description="Collect and summarize company or industry research sources.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    research = subparsers.add_parser("research", help="Run the MVP research workflow.")
    research.add_argument("--company", default="", help="Company name to research.")
    research.add_argument("--ticker", default="", help="Ticker symbol, for example AAPL.")
    research.add_argument("--industry", default="", help="Industry name to research.")
    research.add_argument("--config", default="", help="Path to JSON config file.")
    research.add_argument("--out", default="outputs", help="Output directory.")
    research.add_argument("--verbose", action="store_true", help="Show debug logs.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    load_env()
    setup_logging(verbose=getattr(args, "verbose", False))

    if args.command == "research":
        run_research(args)


def run_research(args: argparse.Namespace) -> None:
    if not args.company and not args.ticker and not args.industry:
        raise SystemExit("Please provide --company, --ticker, or --industry.")

    config = load_config(args.config or None)
    out_dir = Path(args.out)
    db_path = out_dir / "intelligence.db"
    timeout = int(config.get("request_timeout_seconds", 15))

    logger.info("Starting research workflow")

    profile = lookup_company(
        company_name=args.company,
        ticker=args.ticker,
        registry_csv_path=config.get("registry_csv_path", "data/company_registry_sample.csv"),
    )

    company = args.company or (profile.company_name if profile else "")
    ticker = args.ticker or (profile.ticker if profile else "")
    industry = args.industry or (profile.industry if profile else "")
    news_query = company or industry or ticker

    documents = []
    documents.extend(
        collect_news(
            query=news_query,
            feeds=config.get("news_feeds", []),
            max_items=int(config.get("max_news_items", 8)),
        )
    )
    documents.extend(
        collect_configured_reports(
            company=company,
            industry=industry,
            config=config,
            timeout=timeout,
        )
    )

    indicators = collect_price_indicators(ticker=ticker, timeout=timeout)
    brief = generate_brief(
        company=company,
        ticker=ticker,
        industry=industry,
        profile=profile,
        documents=documents,
        indicators=indicators,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    init_db(db_path)
    save_documents(db_path, documents)
    save_brief(db_path, brief)
    export_documents(documents, out_dir)
    export_brief(brief, out_dir)

    logger.info("Research workflow finished")
    print(f"Collected {len(documents)} source documents.")
    print(f"Generated brief: {out_dir / 'industry_brief.md'}")
    print(f"Exported database: {db_path}")


if __name__ == "__main__":
    main()

