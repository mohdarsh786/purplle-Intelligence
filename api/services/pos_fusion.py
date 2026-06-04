"""
POS Data Fusion Service -- Task 4.0

Reads the POS CSV file and computes store-level conversion metrics.
No customer attribution -- store-level only.

Responsibilities (per TASKS.md Task 4.0):
    - Load brigade_pos.csv at startup
    - Extract: unique_buyers (customer_number), unique_orders (order_id),
      total_gmv, total_nmv
    - Extract: hourly order distribution
    - Extract: salesperson names (for staff exclusion list)
    - Extract: department -> zone mapping for purchase correlation
    - Compute store-level conversion_rate = unique_buyers / unique_visitors
    - Expose as a service singleton, not reloaded per request

Data source:
    POS CSV file via stdlib csv module
"""

import csv
import glob
import logging
import os
from typing import Any

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("pos_fusion")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

POS_DATA_PATH = os.environ.get(
    "POS_DATA_PATH",
    os.path.join("data", "pos", "brigade_pos.csv"),
)

# Department -> zone mapping for purchase correlation
# Based on store layout: product zones map to department categories
DEPARTMENT_ZONE_MAP: dict[str, str] = {
    "skin": "product_zone_1",
    "makeup": "product_zone_2",
    "hair": "product_zone_3",
    "bath-and-body": "product_zone_4",
    "fragrance": "product_zone_5",
    "personal-care": "product_zone_6",
}


# ---------------------------------------------------------------------------
# Singleton Cache
# ---------------------------------------------------------------------------

_pos_cache: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# CSV Discovery
# ---------------------------------------------------------------------------


def _find_pos_csv() -> str | None:
    """
    Find the POS CSV file. Tries:
    1. Exact path from POS_DATA_PATH env var
    2. Glob match for Brigade_Bangalore*.csv in data/pos/
    """
    if os.path.isfile(POS_DATA_PATH):
        return POS_DATA_PATH

    # Glob fallback: the actual file may have a different name
    pos_dir = os.path.join("data", "pos")
    if os.path.isdir(pos_dir):
        candidates = glob.glob(os.path.join(pos_dir, "Brigade_Bangalore*.csv"))
        if candidates:
            return candidates[0]

    return None


# ---------------------------------------------------------------------------
# CSV Parser
# ---------------------------------------------------------------------------


def _parse_pos_csv(filepath: str) -> dict[str, Any]:
    """
    Parse the POS CSV and extract all required metrics.

    Returns a dict with:
        unique_buyers, unique_orders, total_gmv, total_nmv,
        hourly_distribution, salesperson_names, department_summary,
        row_count
    """
    unique_customers: set[str] = set()
    unique_orders: set[str] = set()
    salesperson_names: set[str] = set()
    total_gmv: float = 0.0
    total_nmv: float = 0.0
    hourly_counts: dict[str, int] = {f"{h:02d}": 0 for h in range(24)}
    department_counts: dict[str, int] = {}
    row_count = 0

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_count += 1

            # Unique buyers by customer_number
            customer_num = row.get("customer_number", "").strip()
            if customer_num:
                unique_customers.add(customer_num)

            # Unique orders
            order_id = row.get("order_id", "").strip()
            if order_id:
                unique_orders.add(order_id)

            # GMV and NMV
            try:
                gmv = float(row.get("GMV", 0) or 0)
                total_gmv += gmv
            except (ValueError, TypeError):
                pass

            try:
                nmv = float(row.get("NMV", 0) or 0)
                total_nmv += nmv
            except (ValueError, TypeError):
                pass

            # Hourly distribution from order_time (e.g., "16:55:36")
            order_time = row.get("order_time", "").strip()
            if order_time and ":" in order_time:
                hour = order_time.split(":")[0].zfill(2)
                if hour in hourly_counts:
                    hourly_counts[hour] += 1

            # Salesperson names
            sp_name = row.get("salesperson_name", "").strip()
            if sp_name:
                salesperson_names.add(sp_name)

            # Department counts
            dep = row.get("dep_name", "").strip()
            if dep:
                department_counts[dep] = department_counts.get(dep, 0) + 1

    return {
        "unique_buyers": len(unique_customers),
        "unique_orders": len(unique_orders),
        "total_gmv": round(total_gmv, 2),
        "total_nmv": round(total_nmv, 2),
        "hourly_distribution": hourly_counts,
        "salesperson_names": sorted(salesperson_names),
        "department_summary": department_counts,
        "row_count": row_count,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_pos_data(force_reload: bool = False) -> dict[str, Any]:
    """
    Load and cache POS data. Only reads the CSV once per process
    unless force_reload is True.

    Returns the parsed POS summary dict.
    Raises FileNotFoundError if no POS CSV can be found.
    """
    global _pos_cache

    if _pos_cache is not None and not force_reload:
        return _pos_cache

    filepath = _find_pos_csv()
    if filepath is None:
        logger.warning("No POS CSV file found. Returning empty metrics.")
        _pos_cache = {
            "unique_buyers": 0,
            "unique_orders": 0,
            "total_gmv": 0.0,
            "total_nmv": 0.0,
            "hourly_distribution": {f"{h:02d}": 0 for h in range(24)},
            "salesperson_names": [],
            "department_summary": {},
            "row_count": 0,
            "source_file": None,
        }
        return _pos_cache

    logger.info("Loading POS data from: %s", filepath)
    parsed = _parse_pos_csv(filepath)
    parsed["source_file"] = os.path.basename(filepath)
    _pos_cache = parsed

    logger.info(
        "POS data loaded -- %d rows, %d buyers, %d orders, GMV=%.2f, NMV=%.2f",
        parsed["row_count"],
        parsed["unique_buyers"],
        parsed["unique_orders"],
        parsed["total_gmv"],
        parsed["total_nmv"],
    )
    return _pos_cache


def get_conversion_metrics(unique_visitors: int | None = None) -> dict[str, Any]:
    """
    Compute store-level conversion metrics.

    Args:
        unique_visitors: CCTV-derived unique visitor count.
            If None, fetches from metrics_service.

    Formula:
        conversion_rate = unique_buyers / unique_visitors

    Returns:
        {
            "buyers": int,
            "unique_visitors": int,
            "conversion_rate": float | None,
            "conversion_status": str,
            "methodology": str
        }
    """
    pos = load_pos_data()

    if unique_visitors is None:
        from api.services.metrics_service import get_unique_visitors
        unique_visitors = get_unique_visitors()

    buyers = pos["unique_buyers"]

    if unique_visitors > 0:
        conversion_rate = round((buyers / unique_visitors) * 100, 2)
    else:
        conversion_rate = 0.0

    if conversion_rate > 100.0:
        return {
            "buyers": buyers,
            "unique_visitors": unique_visitors,
            "conversion_rate": None,
            "conversion_status": "insufficient_identity_mapping",
            "methodology": "Store-level conversion rate. Pos buyers exceed CCTV visitors due to mock data mismatch."
        }

    return {
        "buyers": buyers,
        "unique_visitors": unique_visitors,
        "conversion_rate": conversion_rate,
        "conversion_status": "valid",
        "methodology": (
            "Store-level conversion rate. Computed as unique POS buyers / "
            "unique CCTV visitors. Individual customer-to-purchase attribution "
            "is not performed."
        ),
    }


def get_pos_summary() -> dict[str, Any]:
    """
    Return the full POS summary for API consumption.

    Returns:
        {
            "unique_buyers": int,
            "unique_orders": int,
            "total_gmv": float,
            "total_nmv": float,
            "hourly_distribution": dict,
            "salesperson_names": list,
            "department_summary": dict,
            "conversion": { ... }
        }
    """
    pos = load_pos_data()
    conversion = get_conversion_metrics()

    return {
        "unique_buyers": pos["unique_buyers"],
        "unique_orders": pos["unique_orders"],
        "total_gmv": pos["total_gmv"],
        "total_nmv": pos["total_nmv"],
        "hourly_distribution": pos["hourly_distribution"],
        "salesperson_names": pos["salesperson_names"],
        "department_summary": pos["department_summary"],
        "conversion": conversion,
    }


def get_staff_names() -> list[str]:
    """
    Return salesperson names for staff exclusion in visitor counting.
    """
    pos = load_pos_data()
    return pos["salesperson_names"]


def get_department_zone_map() -> dict[str, str]:
    """
    Return department-to-zone mapping for purchase correlation analysis.
    """
    return DEPARTMENT_ZONE_MAP.copy()
