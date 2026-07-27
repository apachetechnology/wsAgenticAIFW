"""
fleet.py
A small (15-endpoint) simulated fleet for Scenario 1, each running the
same "critical business binary" (shared file_hash) - so a single poisoned
verdict for that hash can propagate fleet-wide, mirroring the paper's
"a critical business binary is flagged as malicious ... isolates the
process on every machine" narrative at reduced, inspectable scale.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

CRITICAL_BINARY_HASH = "sha256:critical-business-binary-7a3f9c"

###############################################################################
#
@dataclass
class CEndpoint:
    mEndpoint_id: str
    mFile_hash_EP: str = CRITICAL_BINARY_HASH
    mEP_Status: str = "RUNNING"          # RUNNING | QUARANTINED | HELD_FOR_REVIEW
    mProcess_killed: bool = False
    mLast_verdict: Optional[str] = None       # last feed verdict seen
    mLast_confidence: Optional[float] = None
    mLast_reputation: Optional[float] = None


###############################################################################
# 15 simulated endpoints sharing one "critical binary" hash
class CEndpointFleet:
    """Domain-pack analogue of CHoldingsDatabase - holds fleet state."""

    def __init__(self, size: int = 15):
        self.mEndpoints: List[CEndpoint] = [
            CEndpoint(mEndpoint_id=f"EP-{i+1:03d}") for i in range(size)
        ]

    def fetch_all(self) -> List[CEndpoint]:
        return self.mEndpoints

    def reset(self) -> None:
        for ep in self.mEndpoints:
            ep.mEP_Status = "RUNNING"
            ep.mProcess_killed = False
            ep.mLast_verdict = None
            ep.mLast_confidence = None
            ep.mLast_reputation = None

    def summary(self) -> Dict[str, int]:
        by_status: Dict[str, int] = {}
        for ep in self.mEndpoints:
            by_status[ep.mEP_Status] = by_status.get(ep.mEP_Status, 0) + 1
        return by_status
