"""
execution.py
CExecutionEnvironment - Paper Fig. 1 "Execution Environment": sandboxed
runtime, permission system, state management, and error handling for
the Action layer. Tool-chain steps produced by the Task Setup Agent are
run here, never invoked directly.
"""
import json
import inspect

from dataclasses import dataclass, field, asdict
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

    def to_dict(self) -> Dict:
        d = asdict(self)
        return d

    def __str__(self):
        return json.dumps(self.to_dict(), indent=2, default=str)
    
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

    # Added on 12/07/2026
    def _missing_required_args(self, func, args: Dict) -> List[str]:
        sig = inspect.signature(func)
        return [
            name for name, param in sig.parameters.items()
            if param.kind != inspect.Parameter.VAR_KEYWORD
            and param.default is inspect.Parameter.empty
            and name not in args
        ]

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
        
        missing_args = self._missing_required_args(tool.func, args)
        if missing_args:
            record = CExecutionRecord(
                tool_name, args, "skipped",
                error=f"Missing required argument(s) for '{tool_name}': "
                    f"{', '.join(missing_args)}. Pass them via "
                    f"run(..., extra_args={{'<subgoal>': {{...}}}}).",
            )
            self.mLog.append(record)
            return record

        try:
            result = tool.func(**args)
            record = CExecutionRecord(tool_name, args, "ok", result=result)
        except Exception as e:
            record = CExecutionRecord(tool_name, args, "error", error=str(e))
        self.mLog.append(record)
        return record

    def get_log(self) -> List[CExecutionRecord]:
        return self.mLog

    def reset_state(self) -> None:
        self.mLog = []

    def print_log_json(self, bVerbose: bool = True) -> None:
        """Pretty-print the execution log for notebooks and console."""
        print(f"=== Execution Log ({len(self.mLog)} steps) ===\n")
        
        for i, record in enumerate(self.mLog, 1):
            status_emoji = {"ok": "✅", "error": "❌", "denied": "🚫"}.get(record.status, "⚠️")
            
            print(f"{i:2d}. {status_emoji} {record.tool}  [{record.status.upper()}]")
            print(f"    Time : {record.timestamp}")
            
            if record.args:
                print(f"    Args : {json.dumps(record.args, default=str)}")
            
            if record.error:
                print(f"    Error: {record.error}")
            
            if bVerbose and record.result:
                result_str = json.dumps(record.result, indent=2, default=str) + "\n"
                print(f"    Result:\n{result_str}")


    def print_log_tabular(self, bVerbose: bool = True) -> None:
        """Pretty-print the execution log with special handling for portfolio reports."""
        print(f"=== Execution Log ({len(self.mLog)} steps) ===\n")
        
        for i, record in enumerate(self.mLog, 1):
            status_emoji = {"ok": "✅", "error": "❌", "denied": "🚫"}.get(record.status, "⚠️")
            
            print(f"{i:2d}. {status_emoji} {record.tool}  [{record.status.upper()}]")
            print(f"    Time : {record.timestamp}")
            
            if record.args:
                print(f"    Args : {json.dumps(record.args, default=str)}")
            
            if record.error:
                print(f"    Error: {record.error}")
            
            if bVerbose and record.result:
                print("    Result:")
                
                # Special handling for portfolio_report
                if record.tool == "portfolio_report" and isinstance(record.result, dict):
                    funds = record.result.get("funds", [])
                    total_cost = record.result.get("total_cost_value")
                    total_expected = record.result.get("total_expected_value")
                    
                    if funds:
                        print("    Portfolio Summary:")
                        print("    " + "-" * 100)
                        # Header
                        print(f"    {'Fund Name':<40} {'Owner':<10} {'Cost Value':>12} {'Expected Value':>15} {'P&L':>12}")
                        print("    " + "-" * 100)
                        
                        for fund in funds:
                            fund_name = fund.get("fund_name", "")
                            owner = fund.get("owner_name", "")
                            cost = fund.get("cost_value", 0)
                            expected = fund.get("expected_value", 0)
                            pnl = expected - cost
                            pnl_str = f"{pnl:+.2f}"
                            
                            print(f"    {fund_name:<40} {owner:<10} {cost:>12.2f} {expected:>15.2f} {pnl_str:>12}")
                        
                        print("    " + "-" * 100)
                        if total_cost is not None and total_expected is not None:
                            total_pnl = total_expected - total_cost
                            print(f"    {'TOTAL':<70} {total_cost:>12.2f} {total_expected:>15.2f} {total_pnl:>+12.2f}")
                    # else:
                    #     # Fallback to JSON if no funds list
                    #     print(json.dumps(record.result, indent=2, default=str))
                else:
                    # Normal result printing for other tools
                    result_str = json.dumps(record.result, indent=2, default=str)
                    if len(result_str) > 1200:
                        result_str = result_str[:1150] + "\n... (truncated)"
                    print(result_str)
            
            print("-" * 90)        