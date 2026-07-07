"""
orchestrator.py
CAgenticOrchestrator - Paper Fig. 1 "Orchestration Layer": manages
workflow execution by assigning tasks, optimizing resource allocation,
and facilitating inter-agent communication (TPA <-> TSA <-> Action).
Serves as the strategic control-and-coordination hub for the whole run.

Flow for a single call to run():
    1. Perception  : snapshot the portfolio + describe it compactly
    2. Reasoning/TPA: plan()      -> ordered subgoals
    3. Reasoning/TSA: setup()     -> tool + args per subgoal
    4. Action       : run_step()  -> sandboxed execution, one per subgoal
    5. Reasoning/TPA: reflect()   -> plain-language summary + success flag
    6. Memory       : record_episode() for future recall
"""

from typing import Dict, List, Optional, Set

from api_Finance.database import CHoldingsDatabase
from api_Finance.nav_fetcher import CFetchNAV
from api_Finance.performance_analyzer import CPerformanceAnalyzer
from api_Finance.db_interface import CDBInterface
from api_server.Ollama_server import COllamaServer

from config_agent import DEFAULT_ALLOWED_PERMISSIONS
from agentic_framework.agent_memory import CAgentMemory
from agentic_framework.layer_perception import CPerceptionLayer
from agentic_framework.agent_tools import CToolRegistry
from agentic_framework.layer_execution import CExecutionEnvironment
from agentic_framework.layer_reasoning import CTaskPlanningAgent, CTaskSetupAgent


############################################################################
#
class CAgenticOrchestrator:
    def __init__(self, aOllamaServer: COllamaServer, aDB: CHoldingsDatabase,
                 aFetcher: CFetchNAV, aAnalyzer: CPerformanceAnalyzer,
                 aDBInterface: CDBInterface,
                 allowed_permissions: Set[str] = DEFAULT_ALLOWED_PERMISSIONS):
        self.mMemory = CAgentMemory()
        self.mPerception = CPerceptionLayer(aDB, aFetcher)
        self.mRegistry = CToolRegistry(aDB, aFetcher, aAnalyzer, aDBInterface)
        self.mExecution = CExecutionEnvironment(self.mRegistry, allowed_permissions)
        self.mTPA = CTaskPlanningAgent(aOllamaServer, self.mMemory)
        self.mTSA = CTaskSetupAgent(aOllamaServer, self.mMemory)

    # ------------------------------------------------------------------ #
    # Resource allocation - a simple per-run tally of tool calls by
    # permission bucket, printed as part of the coordination log. Keeps
    # the "optimizing resource allocation" duty of the orchestration
    # layer visible rather than implicit.
    # ------------------------------------------------------------------ #
    def _summarize_resource_use(self, log) -> str:
        by_status: Dict[str, int] = {}
        for record in log:
            by_status[record.status] = by_status.get(record.status, 0) + 1
        return ", ".join(f"{k}={v}" for k, v in sorted(by_status.items())) or "no steps run"

    # ------------------------------------------------------------------ #
    # Main entry point
    # ------------------------------------------------------------------ #
    def run(self, goal: str, owner_name: Optional[str] = None,
            extra_args: Optional[Dict[str, Dict]] = None) -> Dict:
        """
        extra_args: optional {subgoal: {arg_name: value}} overrides/additions
        for subgoals the TSA can't reliably fill from free text alone
        (e.g. add_fund's holding_units/nav_base).
        """
        extra_args = extra_args or {}
        self.mExecution.reset_state()
        self.mMemory.reset_short_term()

        # 1. Perception - task assignment starts once context is gathered.
        snapshot = self.mPerception.gather_portfolio_snapshot(owner_name)
        context_summary = self.mPerception.describe_context(snapshot)
        print(f"[Orchestrator] Context gathered: {len(snapshot)} holding row(s).")

        # 2. Reasoning/TPA - plan the subgoals.
        subgoals = self.mTPA.plan(goal, context_summary)
        print(f"[Orchestrator] Task assignment - subgoals: {subgoals or '(none identified)'}")

        # 3-4. Reasoning/TSA + Action - set up and execute each subgoal.
        for subgoal in subgoals:
            step = self.mTSA.setup(subgoal, goal, default_owner=owner_name)
            if step is None:
                self.mMemory.add_short_term(subgoal, tool="?", ok=False, note="no tool mapping")
                continue

            step["args"].update(extra_args.get(subgoal, {}))
            record = self.mExecution.run_step(step["tool"], step["args"])
            self.mMemory.add_short_term(subgoal, step["tool"], record.status == "ok",
                                         note=record.error)

            status_note = f"{step['tool']} -> {record.status}"
            if record.error:
                status_note += f" ({record.error})"
            print(f"[Orchestrator] {status_note}")

        # 5. Reasoning/TPA - reflect over the full execution log.
        reflection = self.mTPA.reflect(goal, self.mExecution.get_log())
        print(f"[Orchestrator] Resource allocation - {self._summarize_resource_use(self.mExecution.get_log())}")
        print(f"[Orchestrator] Reflection: {reflection['summary']}")

        # 6. Memory - record the episode for future recall.
        self.mMemory.record_episode(goal, subgoals,
                                     [vars(r) for r in self.mExecution.get_log()],
                                     reflection["summary"], reflection["success"])

        return {
            "goal": goal,
            "subgoals": subgoals,
            "execution_log": self.mExecution.get_log(),
            "reflection": reflection,
        }
