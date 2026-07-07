"""
execution.py
CExecutionEnvironment — Paper Fig. 1 "Execution Environment": sandboxed
runtime, permission system, state management, and error handling for
the Action layer. Tool-chain steps produced by the Task Setup Agent are
run here, never invoked directly.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from agentic_framework.agent_tools import CToolRegistry

#########################################################################
# 
@dataclass
class CExecutionRecord:
    tool: str
    args: Dict
    status: str            # "ok" | "denied" | "error"
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


############################################################################
#
class CExecutionEnvironment:
    """
    Sandbox: every step declares a tool name + args; execution only
    proceeds if the tool's required permissions are all present in
    `allowed_permissions` for this run. State (the running log) is kept
    so the reasoning layer's reflection step has something concrete to
    look back on, and so a failed run can be inspected after the fact.
    """

    def __init__(self, registry: CToolRegistry, allowed_permissions: Set[str]):
        self.mRegistry = registry
        self.mAllowedPermissions = set(allowed_permissions)
        self.mLog: List[CExecutionRecord] = []

    def run_step(self, tool_name: str, args: Dict) -> CExecutionRecord:
        tool = self.mRegistry.get(tool_name)

        if tool is None:
            record = CExecutionRecord(tool_name, args, "error",
                                       error=f"Unknown tool: {tool_name}")
            self.mLog.append(record)
            return record

        missing = tool.permissions - self.mAllowedPermissions
        if missing:
            record = CExecutionRecord(
                tool_name, args, "denied",
                error=f"Missing permission(s) for this run: {sorted(missing)}",
            )
            self.mLog.append(record)
            return record

        try:
            result = tool.func(**args)
            record = CExecutionRecord(tool_name, args, "ok", result=result)
        except Exception as e:  # noqa: BLE001 — sandbox must not propagate
            record = CExecutionRecord(tool_name, args, "error", error=str(e))

        self.mLog.append(record)
        return record

    def get_log(self) -> List[CExecutionRecord]:
        return self.mLog

    def reset_state(self) -> None:
        self.mLog = []
