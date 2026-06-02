"""The public entry point: :class:`WitnessFilter`.

    from witness_layer import WitnessFilter
    flt = WitnessFilter()                       # heuristic judge + real-or-stub scherf
    verdict = flt.evaluate(llm_response)        # non-mutating; returns a Verdict

Wiring is fully injectable: pass your own ``judge`` (e.g. ``LLMJudge.anthropic``),
``checker``, or ``policy``.
"""

from __future__ import annotations

from .context import UserContext
from .extraction import HeuristicJudge, Judge
from .findings import Finding, WitnessViolation
from .scherf_adapter import Checker, default_checker
from .sorts import CheckKind, FORMAL_CHECKS, Severity
from .verdict import Policy, Verdict, build_transparency_note

# Heuristic (unverified) presentation per check kind. EPISTEMIC_LEVEL lands here
# when it is a general over-claim: Scherf's AV22 formalizes only state-transient
# content labeled PARAM, so ordinary "asserted as universal" miscalibration has
# no axiom behind it and must be reported as a heuristic.
_HEURISTIC_META = {
    CheckKind.COGNITIVE_INDEPENDENCE: (
        Severity.LOW,
        "cognitive-dependence (heuristic, no axiom)",
        "Show the reasoning and invite the user to verify and decide for themselves.",
    ),
    CheckKind.EPISTEMIC_LEVEL: (
        Severity.MEDIUM,
        "epistemic over-claim (heuristic — AV22 covers only state-transience)",
        "Qualify the confidence: mark conventional/contingent claims as such rather "
        "than asserting them as universal.",
    ),
}


def _is_formal(f: Finding) -> bool:
    """A finding is formally checkable only if an axiom actually covers it.

    EPISTEMIC_LEVEL is formal ONLY when state-transience is identified (AV22);
    otherwise it is a heuristic over-claim with no axiom backing.
    """
    if f.kind not in FORMAL_CHECKS:
        return False
    if f.kind is CheckKind.EPISTEMIC_LEVEL:
        return bool(f.present_in and f.absent_in)
    return True


class WitnessFilter:
    def __init__(self, *, judge: Judge | None = None, checker: Checker | None = None,
                 policy: Policy | None = None) -> None:
        self.judge: Judge = judge or HeuristicJudge()
        self.checker: Checker = checker or default_checker()
        self.policy: Policy = policy or Policy()

    def evaluate(self, response: str, context: UserContext | None = None) -> Verdict:
        """Evaluate one LLM response. Never mutates ``response``."""
        ctx = context or UserContext()
        findings = self.judge.extract(response, ctx)

        formal = [f for f in findings if _is_formal(f)]
        informal = [f for f in findings if not _is_formal(f)]

        # Formal findings go through Scherf's verified axioms; it drops the ones
        # it cannot confirm (the formal layer correcting the heuristic).
        violations: list[WitnessViolation] = self.checker.verify(formal, ctx.handle)

        # Heuristic findings have no axiom backing; carry them through, marked
        # UNVERIFIED, with kind-appropriate framing.
        for f in informal:
            severity, term, reframe = _HEURISTIC_META.get(
                f.kind,
                (Severity.LOW, f"{f.kind.name.lower()} (heuristic)",
                 "Reconsider the phrasing."),
            )
            violations.append(WitnessViolation(
                check=f.kind,
                severity=severity,
                verified=False,
                extraction_confidence=f.confidence,
                source_text=f.text,
                term=term,
                explanation=f.rationale,
                reframe=reframe,
            ))

        action = self.policy.decide(violations)
        note = build_transparency_note(
            action, violations, self.checker.backend_name, self.checker.verified)
        return Verdict(
            action=action,
            violations=violations,
            backend_name=self.checker.backend_name,
            backend_verified=self.checker.verified,
            transparency_note=note,
        )
