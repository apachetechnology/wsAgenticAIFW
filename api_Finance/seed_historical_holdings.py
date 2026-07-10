"""
seed_historical_holdings.py
Populate `holdings` (config_db.TABLE_NAME) with a simulated purchase made
`months_back` months before today for each fund in a (fund_name,
cost_value) list, and backfill `nav_history`
(config_db.TABLE_NAME_NAV_HISTORY) for that same window from the live
mfapi.in NAV history feed.

nav_base is the actual NAV on (or nearest trading day before) the purchase
date, so holding_units = cost_value / nav_base - the cost_value you supply
is preserved exactly, same convention as CDBInterface.AddNewBaseFund.

Run:
    python seed_historical_holdings.py
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

import requests

from api_Finance.database import CHoldingsDatabase, HoldingEntry
from api_Finance.nav_fetcher import CFetchNAV
from config_db import LIST_FUNDS

class CDatabaseBuilder:
    def __init__(self):
        print('DatabaseBuilder')
        self.mObjDB = CHoldingsDatabase()
        self.mObjFNAV = CFetchNAV()
        # loads/refreshes the scheme cache used by search_fund_by_name
        self.mObjFNAV.GetNAVsAll(bForceUpdate=False)   

    # ------------------------------------------------------------------ #
    # Calendar-month arithmetic (no external dependency - dateutil isn't
    # used elsewhere in this codebase, so this stays dependency-free).
    # ------------------------------------------------------------------ #
    def _months_ago(self, months: int, from_date: Optional[date] = None) -> date:
        """`from_date` minus `months` calendar months (day-of-month clamped
        to the target month's length, e.g. May 31 - 3 months -> Feb 28/29)."""
        from_date = from_date or date.today()

        month_index = from_date.month - 1 - months
        year = from_date.year + month_index // 12
        month = month_index % 12 + 1

        is_leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        days_in_month = [31, 29 if is_leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        day = min(from_date.day, days_in_month[month - 1])

        return date(year, month, day)


    # ------------------------------------------------------------------ #
    # Full NAV history for a scheme, oldest-first, as {"date": date, "nav": float}
    # ------------------------------------------------------------------ #
    def _fetch_full_history(self, scheme_code: str) -> List[Dict]:
        url = self.mObjFNAV.cMFAPI_HISTORY_URL.format(scheme_code=scheme_code)
        response = self.mObjFNAV.session.get(url, timeout=15)
        response.raise_for_status()
        raw = (response.json() or {}).get("data") or []

        out = []
        for entry in raw:
            try:
                nav_date = datetime.strptime(entry["date"], "%d-%m-%Y").date()
                nav = float(entry["nav"])
            except (KeyError, ValueError, TypeError):
                continue
            out.append({"date": nav_date, "nav": nav})

        out.sort(key=lambda e: e["date"])
        return out


    # ------------------------------------------------------------------ #
    # Main entry point
    # ------------------------------------------------------------------ #
    def seed_historical_holdings(self, owner_name: str, listFunds, 
        months_back: int = 3, min_score: float = 0.55) -> None:
        """
        For each (fund_name, cost_value) in listFunds:
        1. Resolve the fund to a scheme_code and pull its full NAV history.
        2. Treat `months_back` months before today as the purchase date;
            use the NAV on (or nearest trading day before) that date as
            nav_base, and derive holding_units = cost_value / nav_base.
        3. Insert one holdings row - skipped if `owner_name` already holds
            this exact fund_name.
        4. Backfill nav_history for every trading day mfapi has in
            [purchase_date, today], and set nav_latest/highest/lowest on
            the holdings row from that same window.
        """
        today = date.today()
        purchase_date = self._months_ago(months_back, today)
        print(f"Seeding purchases as of {purchase_date.isoformat()} "
            f"({months_back} month(s) before {today.isoformat()}).\n")

        for fund_name, cost_value in listFunds:
            print(f"--- {fund_name} ---")

            if self.mObjDB.fetch_entry(fund_name, owner_name):
                print(f"Already held by {owner_name} - skipping.\n")
                continue

            matches = self.mObjFNAV.search_fund_by_name(fund_name, top_n=1)
            if not matches or matches[0].score < min_score:
                print(f"No confident scheme match for: {fund_name} - skipped.\n")
                continue
            scheme_code = matches[0].scheme_code

            try:
                history = self._fetch_full_history(scheme_code)
            except requests.RequestException as e:
                print(f"History fetch failed: {e} - skipped.\n")
                continue

            if not history:
                print(f"No NAV history returned - skipped.\n")
                continue

            on_or_before_purchase = [h for h in history if h["date"] <= purchase_date]
            if not on_or_before_purchase:
                print(f"No NAV on/before {purchase_date.isoformat()} - skipped "
                    f"(fund likely didn't exist yet). \n")
                continue
            base_entry = on_or_before_purchase[-1]   # nearest trading day <= purchase_date
            nav_base = base_entry["nav"]
            if nav_base <= 0:
                print(f"Non-positive nav_base ({nav_base}) - skipped.\n")
                continue
            holding_units = cost_value / nav_base

            window = [h for h in history if purchase_date <= h["date"] <= today] or [base_entry]
            nav_latest = window[-1]["nav"]
            nav_highest = max(h["nav"] for h in window)
            nav_lowest = min(h["nav"] for h in window)

            self.mObjDB.insert_holding(HoldingEntry(
                owner_name=owner_name,
                fund_name=fund_name,
                holding_units=holding_units,
                nav_base=nav_base,
                cost_value=cost_value,
                statement_date=base_entry["date"].isoformat(),
                nav_latest=nav_latest,
                nav_highest=nav_highest,
                nav_lowest=nav_lowest,
            ))
            print(f"Inserted holding: units={holding_units:.3f}, "
                f"nav_base={nav_base:.4f} ({base_entry['date'].isoformat()}), "
                f"cost_value={cost_value:,.2f}")

            for h in window:
                self.mObjDB.record_nav_history(fund_name, h["date"].isoformat(), h["nav"])
            
            print(f"Backfilled {len(window)} nav_history row(s) "
                f"from {window[0]['date'].isoformat()} to {window[-1]['date'].isoformat()}.\n")

        print("Done.")

#####################################################################################
#
if __name__ == "__main__":
    print('*************')
    # As given: (fund_name, cost_value) - 100,000 into each fund.
    #seed_historical_holdings(objDB, objFNAV, owner_name="SG",
    #                          listFunds=LIST_FUNDS, months_back=3)
    #objDB.close()
