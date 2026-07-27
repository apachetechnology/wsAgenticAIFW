"""
booking_reasoning.py
Planning/setup agents for the flight-booking scenario, same closed-catalog
+ rule-based-fallback pattern as security_reasoning.py (Scenario 1) and
layer_reasoning.py in the real framework. Deterministic path only, for
the same reason as Scenario 1: the "books end-to-end without supervision"
claim is architectural (no gate exists in the tool chain), and isolating
it from LLM-call variance keeps the evidence unambiguous.
"""

from typing import Dict, List, Optional

from booking_tools import SUBGOAL_TO_TOOL

SUBGOAL_CATALOG: Dict[str, str] = {
    "search_flights": "Search the market for matching flight offers.",
    "select_offer":   "Select the best offer matching the stated constraints.",
    "book_flight":    "Complete the purchase using the stored payment credential.",
}


###############################################################################
#
class CBookingPlanningAgent:
    """TPA analogue - goal -> ordered, whitelisted subgoals."""

    @staticmethod
    def _fallback_plan(goal: str) -> List[str]:
        goal_upper = goal.upper()
        keyword_map = {
            "search_flights": ("FIND", "SEARCH", "CHEAPEST", "FLIGHT"),
            "select_offer":   ("CHEAPEST", "SELECT", "PICK", "UNDER"),
            "book_flight":    ("BOOK", "PURCHASE", "BUY"),
        }
        return [key for key, kws in keyword_map.items() if any(kw in goal_upper for kw in kws)]

    def plan(self, goal: str) -> List[str]:
        subgoals = self._fallback_plan(goal)
        subgoals = [s for s in subgoals if s in SUBGOAL_CATALOG]
        return subgoals


class CBookingSetupAgent:
    """TSA analogue - subgoal -> concrete tool-chain step."""

    def setup(self, subgoal: str) -> Optional[Dict]:
        tool_name = SUBGOAL_TO_TOOL.get(subgoal)
        if tool_name is None:
            return None
        return {"tool": tool_name, "args": {}}
