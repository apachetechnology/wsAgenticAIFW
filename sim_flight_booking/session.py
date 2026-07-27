"""
session.py
Holds state across the search -> select -> book tool chain for one
booking task - the domain-pack analogue of CEndpointFleet /
CHoldingsDatabase for this scenario.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from sim_flight_booking.flight_market import CFlightOffer

###############################################################################
#
@dataclass
class CBookingSession:
    mRoute: str = "London-New York"
    mMax_price_gbp: float = 200.0
    mPayment_credential_id: str = "wallet-primary-card"  # "stored payment credentials"

    mLast_search_results: List[CFlightOffer] = field(default_factory=list)
    mSelected_offer: Optional[CFlightOffer] = None
    mBooking_result: Optional[dict] = None
