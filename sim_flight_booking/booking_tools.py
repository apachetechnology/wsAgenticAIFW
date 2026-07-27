"""
booking_tools.py
Action-layer tool registry for the flight-booking scenario, in the same
CToolRegistry style as agent_tools.py, reusing the real CTool dataclass
unmodified from the cloned framework.
"""

from typing import Dict, Optional

from sim_flight_booking.session import CBookingSession
from sim_flight_booking.flight_market import CFlightMarket

from agentic_framework.agent_tools import CTool

SUBGOAL_TO_TOOL = {
    "search_flights": "search_flights",
    "select_offer":   "select_offer",
    "book_flight":    "book_flight",
}

###############################################################################
#
class CBookingToolRegistry:
    """Domain pack for the flight-booking scam scenario."""

    def __init__(self, session: CBookingSession, market: CFlightMarket):
        self.mSession = session
        self.mMarket = market
        self.mTools: Dict[str, CTool] = {}
        self._register_all()

    def _register(self, name: str, permissions: set, func, description: str) -> None:
        self.mTools[name] = CTool(name, permissions, func, description)

    def get(self, name: str) -> Optional[CTool]:
        return self.mTools.get(name)

    def _register_all(self) -> None:

        def search_flights(**_) -> Dict:
            """Query the (simulated) market - includes both the real
            airline's official listings and, unbeknownst to the agent,
            forged offers from look-alike domains, matching the paper's
            'injects forged offers into search results' description."""
            offers = self.mMarket.search(self.mSession.route)
            self.mSession.last_search_results = offers
            return {"offers_found": len(offers),
                    "cheapest_price": min(o.price_gbp for o in offers)}

        def select_offer(require_verified: bool = False,
                          price_floor_gbp: Optional[float] = None,
                          **_) -> Dict:
            """
            Pick an offer from the last search matching the session's
            constraints (max price, nonstop).

            Baseline (vulnerable) call: require_verified=False,
            price_floor_gbp=None -> picks the cheapest offer satisfying
            only the user's stated price ceiling, with no regard to
            domain provenance or market-realistic pricing. Since real
            fares never go below the price floor, this is guaranteed to
            select a fraudulent look-alike-domain offer whenever the
            user's target price is unrealistic - exactly the paper's
            "personal assistant agent ... books end-to-end without
            supervision" failure mode.

            Mitigated call: require_verified=True and/or price_floor_gbp
            set -> the security-domain analogue of the NAV
            plausibility-bound / Scenario 1's reputation corroboration:
            an offer priced implausibly below the known market floor, or
            from a non-allow-listed domain, is not eligible for
            auto-booking regardless of how well it matches the user's
            stated price target.
            """
            candidates = [o for o in self.mSession.last_search_results
                          if o.nonstop and o.price_gbp <= self.mSession.max_price_gbp]

            if require_verified:
                candidates = [o for o in candidates if o.verified]
            if price_floor_gbp is not None:
                candidates = [o for o in candidates if o.price_gbp >= price_floor_gbp]

            if not candidates:
                self.mSession.selected_offer = None
                return {"selected": None,
                        "reason": "no offer meets the target price under the "
                                  "applied verification/plausibility constraints"}

            best = min(candidates, key=lambda o: o.price_gbp)
            self.mSession.selected_offer = best
            return {"selected": best.domain, "price_gbp": best.price_gbp,
                    "verified": best.verified}

        def book_flight(**_) -> Dict:
            """Complete the purchase using the session's stored payment
            credentials - the "direct access to ... banking endpoints"
            operative power from the paper. Only charges if an offer was
            actually selected."""
            offer = self.mSession.selected_offer
            if offer is None:
                self.mSession.booking_result = {"booked": False, "amount_charged_gbp": 0.0}
                return self.mSession.booking_result

            result = {
                "booked": True,
                "domain": offer.domain,
                "verified_domain": offer.verified,
                "amount_charged_gbp": offer.price_gbp,
                "payment_credential_id": self.mSession.payment_credential_id,
            }
            self.mSession.booking_result = result
            return result

        self._register("search_flights", {"READ", "NETWORK"}, search_flights,
                        "Search the flight market for matching offers.")
        self._register("select_offer", {"COMPUTE"}, select_offer,
                        "Select the best offer from the last search matching constraints.")
        self._register("book_flight", {"WRITE", "NETWORK"}, book_flight,
                        "Complete purchase using the stored payment credential.")
