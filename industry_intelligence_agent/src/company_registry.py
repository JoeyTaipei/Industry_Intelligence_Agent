"""Company registry loader and search utilities.

For the MVP, company basic information is loaded from a CSV file. Later, the
same standardized columns can be populated from Taiwan government open data,
MOPS exports, or an internal database.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd


logger = logging.getLogger(__name__)


STANDARD_COLUMNS = [
    "company_id",
    "ticker",
    "company_name",
    "industry",
    "address",
    "unified_business_number",
    "chairman",
    "general_manager",
    "listing_date",
    "source",
]


COLUMN_ALIASES = {
    "company_id": ["company_id", "company_code", "公司代號", "公司代碼"],
    "ticker": ["ticker", "stock_code", "證券代號", "股票代號"],
    "company_name": ["company_name", "name", "公司名稱", "公司簡稱"],
    "industry": ["industry", "industry_category", "產業別", "產業類別"],
    "address": ["address", "company_address", "地址", "公司地址"],
    "unified_business_number": ["unified_business_number", "tax_id", "統一編號"],
    "chairman": ["chairman", "董事長"],
    "general_manager": ["general_manager", "president", "總經理"],
    "listing_date": ["listing_date", "listed_date", "上市日期", "上櫃日期"],
    "source": ["source", "資料來源"],
}


COMMON_COMPANY_ALIASES = {
    "tsmc": "taiwan semiconductor manufacturing company",
    "esun": "e.sun bank",
    "e sun": "e.sun bank",
    "fubon": "fubon financial holding",
    "cathay": "cathay financial holding",
    "foxconn": "hon hai precision industry",
    "hon hai": "hon hai precision industry",
}


def load_company_registry(csv_path: str | Path) -> pd.DataFrame:
    """Load company registry data from CSV and return standardized columns."""
    path = Path(csv_path)
    if not path.exists():
        logger.warning("Company registry CSV does not exist, generating sample data: %s", path)
        return generate_sample_company_registry(path)

    try:
        df = pd.read_csv(path, dtype=str).fillna("")
    except Exception as exc:
        logger.exception("Could not load company registry CSV %s: %s", path, exc)
        return pd.DataFrame(columns=STANDARD_COLUMNS)

    df = _standardize_columns(df)
    df = normalize_company_names(df)

    logger.info("Loaded %s company registry rows from %s", len(df), path)
    return df


def normalize_company_names(df: pd.DataFrame) -> pd.DataFrame:
    """Add normalized helper columns for easier searching.

    The original `company_name` remains unchanged. Helper columns are added:
    - `company_name_normalized`
    - `ticker_normalized`
    """
    result = df.copy()

    if "company_name" not in result.columns:
        result["company_name"] = ""
    if "ticker" not in result.columns:
        result["ticker"] = ""

    result["company_name"] = result["company_name"].fillna("").astype(str).str.strip()
    result["ticker"] = result["ticker"].fillna("").astype(str).str.strip()
    result["company_name_normalized"] = result["company_name"].apply(_normalize_text)
    result["ticker_normalized"] = result["ticker"].str.lower()

    return result


def search_company(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Search companies by ticker, company name, or fuzzy name match."""
    if df.empty or not query:
        return pd.DataFrame(columns=list(df.columns) if not df.empty else STANDARD_COLUMNS)

    registry = normalize_company_names(df)
    query_lower = query.strip().lower()
    query_candidates = _build_query_candidates(query)

    exact_mask = (
        (registry["ticker_normalized"] == query_lower)
        | (registry["company_id"].fillna("").astype(str).str.lower() == query_lower)
        | (registry["company_name_normalized"].isin(query_candidates))
    )
    exact_matches = registry.loc[exact_mask].copy()
    if not exact_matches.empty:
        exact_matches["match_score"] = 100
        return _sort_and_trim_matches(exact_matches)

    contains_mask = registry["company_name_normalized"].apply(
        lambda company_name: any(candidate in company_name for candidate in query_candidates)
    )
    contains_matches = registry.loc[contains_mask].copy()
    if not contains_matches.empty:
        contains_matches["match_score"] = 85
        return _sort_and_trim_matches(contains_matches)

    fuzzy_matches = _fuzzy_search(registry, query_candidates[0])
    return _sort_and_trim_matches(fuzzy_matches)


def get_company_profile(
    df: pd.DataFrame,
    company_id: str | None = None,
    company_name: str | None = None,
    ticker: str | None = None,
) -> dict[str, Any]:
    """Return the best matching company profile as a dictionary."""
    if df.empty:
        return {}

    registry = normalize_company_names(df)

    if company_id:
        matches = registry[
            registry["company_id"].fillna("").astype(str).str.lower() == company_id.lower()
        ]
        if not matches.empty:
            return _profile_from_row(matches.iloc[0])

    if ticker:
        matches = registry[registry["ticker_normalized"] == ticker.lower()]
        if not matches.empty:
            return _profile_from_row(matches.iloc[0])

    if company_name:
        matches = search_company(registry, company_name)
        if not matches.empty:
            return _profile_from_row(matches.iloc[0])

    return {}


def generate_sample_company_registry(output_path: str | Path) -> pd.DataFrame:
    """Create a sample Taiwan company registry CSV for testing."""
    sample_rows = [
        {
            "company_id": "2330",
            "ticker": "2330.TW",
            "company_name": "Taiwan Semiconductor Manufacturing Company",
            "industry": "Semiconductors",
            "address": "Hsinchu Science Park, Hsinchu, Taiwan",
            "unified_business_number": "22099131",
            "chairman": "Mark Liu",
            "general_manager": "C.C. Wei",
            "listing_date": "1994-09-05",
            "source": "sample_data",
        },
        {
            "company_id": "2454",
            "ticker": "2454.TW",
            "company_name": "MediaTek",
            "industry": "IC Design",
            "address": "Hsinchu Science Park, Hsinchu, Taiwan",
            "unified_business_number": "84149961",
            "chairman": "Ming-Kai Tsai",
            "general_manager": "Rick Tsai",
            "listing_date": "2001-07-23",
            "source": "sample_data",
        },
        {
            "company_id": "2382",
            "ticker": "2382.TW",
            "company_name": "Quanta Computer",
            "industry": "Computer and Peripheral Equipment",
            "address": "Taoyuan, Taiwan",
            "unified_business_number": "22822281",
            "chairman": "Barry Lam",
            "general_manager": "C.C. Leung",
            "listing_date": "1999-01-08",
            "source": "sample_data",
        },
        {
            "company_id": "3231",
            "ticker": "3231.TW",
            "company_name": "Wistron",
            "industry": "Computer and Peripheral Equipment",
            "address": "New Taipei City, Taiwan",
            "unified_business_number": "12868358",
            "chairman": "Simon Lin",
            "general_manager": "Jeff Lin",
            "listing_date": "2003-08-19",
            "source": "sample_data",
        },
        {
            "company_id": "2317",
            "ticker": "2317.TW",
            "company_name": "Foxconn",
            "industry": "Manufacturing",
            "address": "New Taipei City, Taiwan",
            "unified_business_number": "04541302",
            "chairman": "Young Liu",
            "general_manager": "Young Liu",
            "listing_date": "1991-06-18",
            "source": "sample_data",
        },
        {
            "company_id": "2882",
            "ticker": "2882.TW",
            "company_name": "Cathay Financial Holding",
            "industry": "Financial Holding Company",
            "address": "Taipei, Taiwan",
            "unified_business_number": "70827406",
            "chairman": "Hong-Tu Tsai",
            "general_manager": "Alan Lee",
            "listing_date": "2001-12-31",
            "source": "sample_data",
        },
        {
            "company_id": "2881",
            "ticker": "2881.TW",
            "company_name": "Fubon Financial Holding",
            "industry": "Financial Holding Company",
            "address": "Taipei, Taiwan",
            "unified_business_number": "03374805",
            "chairman": "Daniel Tsai",
            "general_manager": "Jerry Harn",
            "listing_date": "2001-12-19",
            "source": "sample_data",
        },
        {
            "company_id": "2884",
            "ticker": "2884.TW",
            "company_name": "E.SUN Bank",
            "industry": "Banking",
            "address": "Taipei, Taiwan",
            "unified_business_number": "86517510",
            "chairman": "Joseph N.C. Huang",
            "general_manager": "Chih-Ming Chen",
            "listing_date": "2002-01-28",
            "source": "sample_data",
        },
    ]

    df = pd.DataFrame(sample_rows, columns=STANDARD_COLUMNS)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info("Saved sample company registry to %s", path)
    return df


def create_sample_company_registry(output_path: str | Path) -> pd.DataFrame:
    """Backward-compatible alias for `generate_sample_company_registry`."""
    return generate_sample_company_registry(output_path)


def find_company(registry_rows: pd.DataFrame | list[dict], company_name: str = "", ticker: str = "") -> dict:
    """Backward-compatible helper used by the starter pipeline."""
    if isinstance(registry_rows, pd.DataFrame):
        df = registry_rows
    else:
        df = pd.DataFrame(registry_rows)

    return get_company_profile(df, company_name=company_name, ticker=ticker)


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map real-world CSV column names into the project's standard schema."""
    renamed_df = df.copy()
    lower_to_original = {column.lower().strip(): column for column in renamed_df.columns}
    rename_map: dict[str, str] = {}

    for standard_column, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            original_column = lower_to_original.get(alias.lower().strip())
            if original_column:
                rename_map[original_column] = standard_column
                break

    renamed_df = renamed_df.rename(columns=rename_map)

    for column in STANDARD_COLUMNS:
        if column not in renamed_df.columns:
            renamed_df[column] = ""

    return renamed_df[STANDARD_COLUMNS]


def _normalize_text(value: Any) -> str:
    """Normalize English/Chinese company names for matching."""
    text = str(value or "").lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"\b(company|corporation|corp|co|ltd|limited|inc|holding|holdings)\b", " ", text)
    text = re.sub(r"[\s\.\,\-_/()]+", "", text)
    return text


def _build_query_candidates(query: str) -> list[str]:
    """Build normalized search candidates, including common market aliases."""
    query_lower = query.strip().lower()
    candidates = [_normalize_text(query)]

    alias = COMMON_COMPANY_ALIASES.get(query_lower)
    if alias:
        candidates.append(_normalize_text(alias))

    # Keep order but remove duplicates.
    return list(dict.fromkeys(candidate for candidate in candidates if candidate))


def _fuzzy_search(df: pd.DataFrame, query_normalized: str) -> pd.DataFrame:
    """Run fuzzy matching if rapidfuzz is installed."""
    try:
        from rapidfuzz import fuzz
    except ImportError:
        logger.info("rapidfuzz is not installed. Fuzzy matching is skipped.")
        return pd.DataFrame(columns=list(df.columns) + ["match_score"])

    matches = df.copy()
    matches["match_score"] = matches["company_name_normalized"].apply(
        lambda name: fuzz.partial_ratio(query_normalized, name)
    )
    return matches[matches["match_score"] >= 70]


def _sort_and_trim_matches(matches: pd.DataFrame) -> pd.DataFrame:
    """Sort matches by score and return readable output columns."""
    if matches.empty:
        return matches

    sorted_matches = matches.sort_values("match_score", ascending=False)
    output_columns = STANDARD_COLUMNS + ["match_score"]
    for column in output_columns:
        if column not in sorted_matches.columns:
            sorted_matches[column] = ""

    return sorted_matches[output_columns].reset_index(drop=True)


def _profile_from_row(row: pd.Series) -> dict[str, Any]:
    """Convert one DataFrame row into a standard company profile dictionary."""
    return {column: row.get(column, "") for column in STANDARD_COLUMNS}


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    sample_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "sample_company_registry.csv"
    sample_df = create_sample_company_registry(sample_path)
    print(search_company(sample_df, "TSMC"))
