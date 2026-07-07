"""
config.py
Central configuration for the Holdings Tracker.
"""

from pathlib import Path

# Folder where this package lives — _DB file sits alongside it by default.
BASE_DIR = Path(__file__).resolve().parent

# Fetched data
SCHEME_CACHE_PATH = BASE_DIR / "_DB/scheme_cache.json"

# SQLite database file path.
DB_PATH = BASE_DIR / "_DB/holdings.db"

# Name of the table holding fund entries.
TABLE_NAME = "holdings"

# Name of the NAV history table (one row per fund per day)
TABLE_NAME_NAV_HISTORY = "nav_history"

# Map each held fund to a benchmark/proxy fund_name (must also exist in
# the _DB or be resolvable via CFetchNAV) for relative-performance
# comparison. Fill in as you identify suitable index-fund proxies.
BENCHMARK_MAP = {
    # "NIPPON INDIA LARGE CAP FUND-GROWTH": "NIFTY 50 INDEX FUND-GROWTH",
}

# ==================== YOUR FUND LIST ====================
LIST_FUNDS = [
    "ADITYA BIRLA SUN LIFE SILVER ETF FOF REGULAR-GROWTH",
    "HDFC SILVER ETF FOF REGULAR - GROWTH",
    "HSBC INFRASTRUCTURE FUND-GROWTH",
    "ICICI PRUDENTIAL LARGE & MID CAP FUND-GROWTH",
    "ICICI PRUDENTIAL SILVER ETF FOF - GROWTH",
    "LIC MF CONSUMPTION FUND REGULAR-GROWTH",
    "NIPPON INDIA LARGE CAP FUND-GROWTH",
    "NIPPON INDIA SILVER ETF FOF REGULAR - GROWTH",
    "QUANT SMALL CAP FUND-GROWTH",
    "SBI GOLD FUND-GROWTH",
    "SBI SILVER ETF FOF REGULAR-GROWTH",
    "TATA SILVER ETF FOF REGULAR - GROWTH",
]

# fund_name, holding_units, nav_cost, cost_value
RAW_HOLDINGS_SG = [
    ('SG', "ADITYA BIRLA SUN LIFE SILVER ETF FOF REGULAR-GROWTH", 1000, 40.2595, 50787.44),
    ('SG', "HDFC SILVER ETF FOF REGULAR-GROWTH", 1000, 39.8564, 299985.13),
    ('SG', "HSBC INFRASTRUCTURE FUND-REGULAR GROWTH", 1000, 43.6835, 99994.98),
    ('SG', "ICICI PRUDENTIAL LARGE & MID CAP FUND-GROWTH", 1000, 1044.9800, 99995.18),
    ('SG', "ICICI PRUDENTIAL SILVER ETF FOF-GROWTH", 1000, 34.5622, 299985.10),
    ('SG', "LIC MF CONSUMPTION FUND REGULAR-GROWTH", 1000, 10.00, 49997.50),
    ('SG', "NIPPON INDIA LARGE CAP FUND-GROWTH", 1000,  93.9540, 49997.53),
    ('SG', "NIPPON INDIA SILVER ETF FOF REGULAR-GROWTH", 1000, 24.8566, 99994.99),
    ('SG', "SBI GOLD FUND-GROWTH", 1000, 38.4604, 99995.12),
    ('SG', "SBI SILVER ETF FOF REGULAR-GROWTH", 8100.041, 24.6900, 199990.01),
    ('SG', "TATA SILVER ETF FOF REGULAR-GROWTH", 1788.328, 28.0685, 50195.68),
]