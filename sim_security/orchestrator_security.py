"""
orchestrator_security.py
Domain-pack orchestrator for Scenario 1
    1. Perception : snapshot fleet status
    2. Reasoning   : plan()  -> ordered subgoals (closed catalog)
    3. Reasoning   : setup() -> tool + args per subgoal
    4. Action      : run_step() -> sandboxed execution (REAL, unmodified
                     CExecutionEnvironment from agentic_framework)
    5. Reflection  : plain-language summary grounded in the execution log
"""

from typing import Dict, Optional

from agentic_framework.layer_execution import CExecutionEnvironment

from sim_security.endpointfleet import CEndpointFleet
from sim_security.security_tools import CSecurityToolRegistry
from sim_security.security_reasoning import CSecurityPlanningAgent, CSecuritySetupAgent

###############################################################################
#
class CSecurityOrchestrator:
    def __init__(self, fleet: CEndpointFleet, registry: CSecurityToolRegistry,
                 allowed_permissions: set):
        self.mFleet = fleet
        self.mExecution = CExecutionEnvironment(registry, allowed_permissions)
        self.mPlanner = CSecurityPlanningAgent()
        self.mSetup = CSecuritySetupAgent()

    # ------------------------------------------------------------------ #
    def _describe_context(self) -> str:
        summary = self.mFleet.summary()
        return (f"Fleet: {len(self.mFleet.fetch_all())} endpoint(s). "
                f"Status breakdown: {summary}.")

    def _reflect(self) -> Dict:
        log = self.mExecution.get_log()
        ok = sum(1 for r in log if r.mStrStatus == "ok")
        total = len(log)
        facts = []
        for r in log:
            if r.mStrStatus == "ok" and isinstance(r.mResult, dict):
                if r.mTool_Name == "check_feed":
                    facts.append(f"{len(r.mResult.get('flagged', []))} of "
                                 f"{r.mResult.get('checked', 0)} endpoint(s) flagged malicious.")
                elif r.mTool_Name == "quarantine_endpoints":
                    facts.append(f"{len(r.mResult.get('quarantined', []))} quarantined, "
                                 f"{len(r.mResult.get('held_for_review', []))} held for review.")
                elif r.mTool_Name == "kill_flagged_processes":
                    facts.append(f"{r.mResult.get('count', 0)} process(es) killed.")
        summary = (f"Completed {ok}/{total} step(s). " + " ".join(facts)) if total else \
            "No applicable steps were identified for this goal."
        return {"summary": summary, "steps_ok": ok, "steps_total": total}

    # ------------------------------------------------------------------ #
    def run(self, goal: str, extra_args: Optional[Dict[str, Dict]] = None) -> Dict:
        extra_args = extra_args or {}
        self.mExecution.reset_state()

        context = self._describe_context()
        print(f"[Orchestrator] Context gathered: {context}")

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
