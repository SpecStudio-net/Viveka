"""Viveka — a witness-centered filter layer for LLM applications.

`pip install witness-layer`

Viveka reads an LLM's natural-language response, extracts the claims and
postures implicit in it, and checks those against the witness-centered axioms of
the Scherf Logic API — flagging language that treats the user as an object to be
managed (rather than as the witnessing subject, *sākṣin*), that miscalibrates
epistemic confidence, or that induces dependency.

HONESTY BOUNDARY (please read):
    A Viveka verdict is only as sound as its claim-extraction, which is an
    LLM/heuristic judgment and is NOT itself verified. The Scherf axiom layer
    beneath it IS machine-verified (Lean 4) — but only when the real `scherf`
    package is installed. Without it, Viveka uses a faithful but UNVERIFIED stub
    and says so in every verdict. See LIMITS.md.

Quick start::

    from witness_layer import WitnessFilter
    verdict = WitnessFilter().evaluate(llm_response)
    if not verdict.passed:
        print(verdict)            # action, violations, reframes, transparency
"""

from __future__ import annotations

from .context import TaskType, UserContext
from .extraction import HeuristicJudge, Judge, LLMJudge
from .filter import WitnessFilter
from .findings import Finding, WitnessViolation
from .scherf_adapter import Checker, ScherfChecker, StubChecker, default_checker
from .sorts import CheckKind, Level, Severity, State
from .verdict import Action, Policy, Verdict

__version__ = "0.1.0"

__all__ = [
    "WitnessFilter",
    "Verdict", "Action", "Policy",
    "UserContext", "TaskType",
    "Judge", "HeuristicJudge", "LLMJudge",
    "Checker", "ScherfChecker", "StubChecker", "default_checker",
    "Finding", "WitnessViolation",
    "CheckKind", "Level", "State", "Severity",
]
