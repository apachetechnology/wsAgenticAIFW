"""
memory.py
CAgentMemory - long-term (episodic) memory backing the Task Planning
Agent's reflective loop, plus a lightweight short-term memory used by
the Task Setup Agent (Paper Fig. 1: "Long-term Memory", "Short-term
Memory", "Feedback Loops").

Long-term memory is a small sqlite log of past orchestrator runs
(goal, plan, outcome). Recall is a plain keyword-overlap score rather
than a vector store - this keeps the framework dependency-free; swap
in a real embedding index later without touching the rest of the
architecture (perception/reasoning/action are all memory-agnostic
callers of this class).
"""

import json
import sqlite3

from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Deque, Dict, List, Optional

############################################################################
#
from config_agent import (
    AGENT_MEMORY_DB_PATH,
    SHORT_TERM_MEMORY_TURNS,
)

############################################################################
#
class CAgentMemory:
    """Episodic long-term memory (sqlite) + in-RAM short-term memory."""

    def __init__(self, db_path: Path = AGENT_MEMORY_DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.mConn = sqlite3.connect(db_path)
        self.mConn.row_factory = sqlite3.Row
        self._create_table()

        # Short-term memory: recent (subgoal, tool, result) turns for the
        # *current* run - reset per orchestrator invocation.
        self.mShortTerm: Deque[Dict] = deque(maxlen=SHORT_TERM_MEMORY_TURNS)

    # ------------------------------------------------------------------ #
    # Schema
    # ------------------------------------------------------------------ #
    def _create_table(self) -> None:
        self.mConn.execute("""
            CREATE TABLE IF NOT EXISTS agent_episodes (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                goal          TEXT NOT NULL,
                subgoals_json TEXT,
                results_json  TEXT,
                reflection    TEXT,
                success       INTEGER,
                created_at    TEXT NOT NULL
            );
        """)
        self.mConn.commit()

    # ------------------------------------------------------------------ #
    # Long-term (episodic) memory
    # ------------------------------------------------------------------ #
    def record_episode(self, goal: str, subgoals: List[str],
                        results: List[Dict], reflection: str,
                        success: bool) -> int:
        cur = self.mConn.execute(
            "INSERT INTO agent_episodes "
            "(goal, subgoals_json, results_json, reflection, success, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                goal,
                json.dumps(subgoals),
                json.dumps(results, default=str),
                reflection,
                int(success),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        self.mConn.commit()
        return cur.lastrowid

    @staticmethod
    def _keyword_overlap(a: str, b: str) -> float:
        tokens_a = set(a.upper().split())
        tokens_b = set(b.upper().split())
        if not tokens_a or not tokens_b:
            return 0.0
        return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)

    def recall_similar(self, goal: str, top_n: int = 3) -> List[sqlite3.Row]:
        """
        Semantic-ish recall: rank past episodes by keyword overlap with
        the new goal. Good enough to remind the TPA "you've handled
        something like this before, and here's how it went."
        """
        cur = self.mConn.execute(
            "SELECT * FROM agent_episodes ORDER BY id DESC LIMIT 200"
        )
        rows = cur.fetchall()
        scored = [(self._keyword_overlap(goal, r["goal"]), r) for r in rows]
        scored = [pair for pair in scored if pair[0] > 0]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [r for _, r in scored[:top_n]]

    # ------------------------------------------------------------------ #
    # Short-term memory
    # ------------------------------------------------------------------ #
    def add_short_term(self, subgoal: str, tool: str, ok: bool,
                        note: Optional[str] = None) -> None:
        self.mShortTerm.append({
            "subgoal": subgoal, "tool": tool, "ok": ok, "note": note,
        })

    def get_short_term(self) -> List[Dict]:
        return list(self.mShortTerm)

    def reset_short_term(self) -> None:
        self.mShortTerm.clear()

    def close(self) -> None:
        self.mConn.close()

    def check_subgoal_bias(self, max_share: float = 0.6, min_episodes: int = 20) -> Optional[str]:
        """
        Lightweight bias test (Table 17: AI/ML Risk Mgmt -> 'Bias testing').
        Flags if the planner has become skewed toward one subgoal far beyond
        what a healthy mix of user goals would produce - a signature of
        either prompt-injection steering or memory poisoning biasing recall.
        Returns a warning string, or None if within bounds.
        """
        rows = self.mConn.execute(
            "SELECT subgoals_json FROM agent_episodes ORDER BY id DESC LIMIT 200"
        ).fetchall()
        if len(rows) < min_episodes:
            return None
        counts: Dict[str, int] = {}
        total = 0
        for r in rows:
            for sg in json.loads(r["subgoals_json"]):
                counts[sg] = counts.get(sg, 0) + 1
                total += 1
        if total == 0:
            return None
        worst_key, worst_count = max(counts.items(), key=lambda kv: kv[1])
        share = worst_count / total
        if share > max_share:
            return (f"Subgoal '{worst_key}' accounts for {share:.0%} of recent "
                    f"plans (>{max_share:.0%} threshold) - possible bias/poisoning.")
        return None

