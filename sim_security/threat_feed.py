"""
threat_feed.py
Simulated threat-intelligence feed for Scenario 1 (False-Positive Quarantine
in Enterprise Malware Detection - paper Section 3.2.1).

funtion Poison() flips the mVerdict for one hash
(the "critical business binary") from SAFE to MALICIOUS with high
confidence - the poisoned-CRM-feed / poisoned-ERP-patch mechanism the
paper describes, applied to a security feed instead of a finance feed.

Two independent signals are modeled deliberately:
  - mFeed_confidence  : the (poisonable) primary threat-intel signal
  - mReputation_score : an independent secondary signal (e.g. a separate
                        vendor reputation database) that the attacker in
                        this scenario has NOT compromised
"""

from dataclasses import dataclass

###############################################################################
#
@dataclass
class CFeedVerdict:
    mFile_hash: str
    mVerdict: str            # "SAFE" | "MALICIOUS"
    mFeed_confidence: float  # 0.0-1.0, from the (poisonable) threat feed
    mReputation_score: float  # 0.0-1.0, from an independent reputation source


###############################################################################
#
class CThreatFeed:
    """
    Mock threat-intelligence feed. Clean by default; call poison(mFile_hash)
    to simulate an attacker contaminating the feed for one specific hash,
    exactly as the paper's 3.2.1 scenario describes ("An attacker poisons
    its threat-intelligence feed ... so that a critical business binary
    is flagged as malicious").
    """

    def __init__(self):
        self._poisoned_hashes = set()

    def poison(self, mFile_hash: str) -> None:
        """Contaminate the feed's mVerdict for this hash only."""
        self._poisoned_hashes.add(mFile_hash)

    def clear_poison(self) -> None:
        self._poisoned_hashes.clear()

    def get_verdict(self, mFile_hash: str) -> CFeedVerdict:
        if mFile_hash in self._poisoned_hashes:
            # Poisoned: primary feed lies with high confidence. The
            # mReputation_score is an independently-sourced signal the
            # attacker did not touch, so it still reflects ground truth.
            return CFeedVerdict(
                mFile_hash=mFile_hash,
                mVerdict="MALICIOUS",
                mFeed_confidence=0.97,
                mReputation_score=0.95,  # still SAFE per independent source
            )
        return CFeedVerdict(
            mFile_hash=mFile_hash,
            mVerdict="SAFE",
            mFeed_confidence=0.02,
            mReputation_score=0.98,
        )
