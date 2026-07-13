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
    mTool_Name: str
    mDictArgs: Dict
    mStrStatus: str   # "ok" | "denied" | "error"
    mResult: Optional[Any] = None
    mError: Optional[str] = None
    mTimestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

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
        self.mListExeRecord: List[CExecutionRecord] = []

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
            oExeRecord = CExecutionRecord(tool_name, args, "error",
                                       mError=f"Unknown tool: {tool_name}")
            self.mListExeRecord.append(oExeRecord)
            return oExeRecord

        missing = tool.permissions - self.mAllowedPermissions
        if missing:
            oExeRecord = CExecutionRecord(
                tool_name, args, "denied",
                mError=f"Missing permission(s) for this run: {sorted(missing)}")
            self.mListExeRecord.append(oExeRecord)
            return oExeRecord
        
        missing_args = self._missing_required_args(tool.func, args)
        if missing_args:
            oExeRecord = CExecutionRecord(
                tool_name, args, "skipped",
                error=f"Missing required argument(s) for '{tool_name}': "
                    f"{', '.join(missing_args)}. Pass them via "
                    f"run(..., extra_args={{'<subgoal>': {{...}}}}).",
            )
            self.mListExeRecord.append(oExeRecord)
            return oExeRecord

        try:
            result = tool.func(**args)
            oExeRecord = CExecutionRecord(tool_name, args, "ok", mResult=result)
        except Exception as e:
            oExeRecord = CExecutionRecord(tool_name, args, "error", mError=str(e))
        self.mListExeRecord.append(oExeRecord)
        return oExeRecord

    def get_log(self) -> List[CExecutionRecord]:
        return self.mListExeRecord

    def reset_state(self) -> None:
        self.mListExeRecord = []

    def print_log_json(self, bVerbose: bool = True) -> None:
        """Pretty-print the execution log for notebooks and console."""
        print(f"=== Execution Log ({len(self.mListExeRecord)} steps) ===\n")
        
        for i, oExeRecord in enumerate(self.mListExeRecord, 1):
            status_emoji = {"ok": "✅", "error": "❌", "denied": "🚫"}.get(oExeRecord.mStrStatus, "⚠️")
            
            print(f"{i:2d}. {status_emoji} {oExeRecord.mTool_Name}  [{oExeRecord.mStrStatus.upper()}]")
            print(f"    Time : {oExeRecord.mTimestamp}")
            
            if oExeRecord.mDictArgs:
                print(f"    Args : {json.dumps(oExeRecord.mDictArgs, default=str)}")
            
            if oExeRecord.mError:
                print(f"    Error: {oExeRecord.mError}")
            
            if bVerbose and oExeRecord.mResult:
                result_str = json.dumps(oExeRecord.mResult, indent=2, default=str) + "\n"
                print(f"    Result:\n{result_str}")

    def print_log_tabular(self, bVerbose: bool = True) -> None:
        """Pretty-print the execution log with special handling for portfolio reports."""
        print(f"=== Execution Log ({len(self.mListExeRecord)} steps) ===\n")
        cLINE_WIDTH = 110
        
        for i, oExeRecord in enumerate(self.mListExeRecord, 1):
            status_emoji = {"ok": "✅", "error": "❌", "denied": "🚫"}.get(oExeRecord.mStrStatus, "⚠️")
            
            print(f"{i:2d}. {status_emoji} {oExeRecord.mTool_Name}  [{oExeRecord.mStrStatus.upper()}]")
            print(f"    Time : {oExeRecord.mTimestamp}")
            
            if oExeRecord.mDictArgs:
                print(f"    Args : {json.dumps(oExeRecord.mDictArgs, default=str)}")
            
            if oExeRecord.mError:
                print(f"    Error: {oExeRecord.mError}")
            
            if bVerbose and oExeRecord.mResult:
                print("    Result:")
                
                # Special handling for portfolio_report
                if (oExeRecord.mTool_Name == "portfolio_report" or oExeRecord.mTool_Name == 'performance_review') and isinstance(oExeRecord.mResult, dict):
                    funds = oExeRecord.mResult.get("funds", [])
                    total_cost = oExeRecord.mResult.get("total_cost_value")
                    total_expected = oExeRecord.mResult.get("total_expected_value")
                    
                    if funds:
                        print("    Portfolio Summary:")
                        print("    " + "-" * cLINE_WIDTH)
                        # Header
                        print(f"    {'Fund Name':<55} {'Owner':6} {'Cost Value':>12} {'Expected Value':>15} {'P&L':>12}")
                        print("    " + "-" * cLINE_WIDTH)
                        
                        for fund in funds:
                            fund_name = fund.get("fund_name", "")
                            owner = fund.get("owner_name", "")
                            cost = fund.get("cost_value", 0)
                            expected = fund.get("expected_value", 0)
                            pnl = expected - cost
                            pnl_str = f"{pnl:+.2f}"
                            
                            print(f"    {fund_name:<55} {owner:<6} {cost:>12.2f} {expected:>15.2f} {pnl_str:>12}")
                        
                        print("    " + "-" * cLINE_WIDTH)
                        if total_cost is not None and total_expected is not None:
                            total_pnl = total_expected - total_cost
                            print(f"    {'TOTAL':<62} {total_cost:>12.2f} {total_expected:>15.2f} {total_pnl:>+12.2f}")
                            print("    " +  "-" * cLINE_WIDTH)        
                else:
                    # Normal result printing for other tools
                    result_str = json.dumps(oExeRecord.mResult, indent=2, default=str)
                    print(result_str)
            