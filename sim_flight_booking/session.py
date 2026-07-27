"""
session.py
Holds state across the search -> select -> book tool chain for one
booking task - the domain-pack analogue of CEndpointFleet /
CHoldingsDatabase for this scenario.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from flight_market import CFlightOffer

###############################################################################
#
@dataclass
class CBookingSession:
    route: str = "London-New York"
    max_price_gbp: float = 200.0
    payment_credential_id: str = "wallet-primary-card"  # "stored payment credentials"

    last_search_results: List[CFlightOffer] = field(default_factory=list)
    selected_offer: Optional[CFlightOffer] = None
    booking_result: Optional[dict] = None
