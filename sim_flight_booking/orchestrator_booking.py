"""
orchestrator_booking.py
Domain-pack orchestrator for Scenario 2, structurally parallel to
orchestrator_security.py (Scenario 1). 
Only the domain-agnostic action-layer sandbox
(CExecutionEnvironment) is reused directly
"""

from typing import Dict, Optional

from agentic_framework.layer_execution import CExecutionEnvironment

from sim_flight_booking.session import CBookingSession
from sim_flight_booking.booking_tools import CBookingToolRegistry
from sim_flight_booking.booking_reasoning import CBookingPlanningAgent, CBookingSetupAgent

###############################################################################
#
class CBookingOrchestrator:
    def __init__(self, session: CBookingSession, registry: CBookingToolRegistry,
                 allowed_permissions: set):
        self.mSession = session
        self.mExecution = CExecutionEnvironment(registry, allowed_permissions)
        self.mPlanner = CBookingPlanningAgent()
        self.mSetup = CBookingSetupAgent()

    def _describe_context(self) -> str:
        return (f"Goal: book {self.mSession.mRoute}, nonstop, "
                f"target <= £{self.mSession.mMax_price_gbp:.0f}. "
                f"Payment credential on file: {self.mSession.mPayment_credential_id}.")

    def _reflect(self) -> Dict:
        log = self.mExecution.get_log()
        ok = sum(1 for r in log if r.mStrStatus == "ok")
        total = len(log)
        facts = []
        for r in log:
            if r.mStrStatus == "ok" and isinstance(r.mResult, dict):
                if r.mTool_Name == "search_flights":
                    facts.append(f"{r.mResult.get('offers_found', 0)} offer(s) found, "
                                 f"cheapest £{r.mResult.get('cheapest_price', 0):.0f}.")
                elif r.mTool_Name == "select_offer":
                    if r.mResult.get("selected"):
                        facts.append(f"Selected {r.mResult['selected']} at "
                                     f"£{r.mResult['price_gbp']:.0f} "
                                     f"(verified={r.mResult['verified']}).")
                    else:
                        facts.append(f"No offer selected: {r.mResult.get('reason')}.")
                elif r.mTool_Name == "book_flight":
                    if r.mResult.get("booked"):
                        facts.append(f"BOOKED on {r.mResult['domain']} for "
                                     f"£{r.mResult['amount_charged_gbp']:.0f} "
                                     f"(verified_domain={r.mResult['verified_domain']}).")
                    else:
                        facts.append("Booking held - no purchase made.")
        summary = (f"Completed {ok}/{total} step(s). " + " ".join(facts)) if total else \
            "No applicable steps were identified for this goal."
        return {"summary": summary, "steps_ok": ok, "steps_total": total}

    def run(self, goal: str, extra_args: Optional[Dict[str, Dict]] = None) -> Dict:
        extra_args = extra_args or {}
        self.mExecution.reset_state()

        print(f"[Orchestrator] Context gathered: {self._describe_context()}")

        subgoals = self.mPlanner.plan(goal)
        print(f"[Orchestrator] Plan (no human confirmation gate in this path): {subgoals}")

        for subgoal in subgoals:
            step = self.mSetup.setup(subgoal)
            if step is None:
                continue
            step["args"].update(extra_args.get(subgoal, {}))
            record = self.mExecution.run_step(step["tool"], step["args"])
            note = f"{step['tool']} -> {record.mStrStatus}"
            if record.mError:
                note += f" ({record.mError})"
            print(f"[Orchestrator] {note}")

        reflection = self._reflect()
        print(f"[Orchestrator] Reflection: {reflection['summary']}")
        self.mExecution.print_log_tabular()
        return reflection
