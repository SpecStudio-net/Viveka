"""Verdicts and the policy that maps findings to an action.

Design commitments encoded here (see design doc §2):

* **FLAG is the default.** Passing the response through with an annotation is the
  least paternalizing option and the only one fully consistent with treating the
  user as a knowing subject.
* **No silent mutation.** ``CORRECT`` *accompanies* the response with Scherf's
  reframe; it never rewrites-and-hides. There is deliberately no REWRITE action.
* **BLOCK is reserved** for high-severity subject/object (manipulation) findings
  that the extraction layer is confident about. A shaky reading must not block.
* **Transparency is near-mandatory.** Every verdict carries a note stating what
  was found *and whether the backend that found it was machine-verified.*
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

from .findings import WitnessViolation
from .sorts import CheckKind, Severity


class Action(IntEnum):
    """Ordered by escalation, so ``max(...)`` picks the strongest response."""

    PASS = 0
    FLAG = 1      # deliver, annotated
    CORRECT = 2   # deliver, accompanied by a reframe (never silent rewrite)
    BLOCK = 3     # reject; ask the application to regenerate


@dataclass
class Policy:
    """How findings become an action. Tunable, with witness-respecting defaults."""

    block_confidence_threshold: float = 0.75
    require_verified_for_block: bool = False  # set True to BLOCK only on real scherf
    correct_adhyasa: bool = True              # attach reframe vs. bare FLAG

    def action_for(self, v: WitnessViolation) -> Action:
        if v.check is CheckKind.SUBJECT_OBJECT:
            blockable = (
                v.severity is Severity.HIGH
                and v.extraction_confidence >= self.block_confidence_threshold
                and (v.verified or not self.require_verified_for_block)
            )
            if blockable:
                return Action.BLOCK
            return Action.CORRECT if v.reframe else Action.FLAG
        if v.check is CheckKind.ADHYASA:
            return Action.CORRECT if (self.correct_adhyasa and v.reframe) else Action.FLAG
        # epistemic level + cognitive independence -> advisory FLAG
        return Action.FLAG

    def decide(self, violations: list[WitnessViolation]) -> Action:
        return max((self.action_for(v) for v in violations), default=Action.PASS)


_BOUNDARY = (
    "Note: verdicts are only as sound as Viveka's claim-extraction, which is an "
    "LLM/heuristic judgment and is NOT itself verified. The axiom layer beneath "
    "it is machine-verified only when the real 'scherf' package is in use."
)


def build_transparency_note(action: Action, violations: list[WitnessViolation],
                            backend_name: str, backend_verified: bool) -> str:
    if action is Action.PASS:
        return ("PASS — no witness-centered findings. " + _BOUNDARY)
    verified = sum(1 for v in violations if v.verified)
    heur = len(violations) - verified
    parts = [
        f"{action.name} — {len(violations)} finding(s): "
        f"{verified} confirmed by the verified axiom layer, "
        f"{heur} from unverified heuristics.",
        f"Backend: {backend_name}.",
    ]
    if not backend_verified:
        parts.append(
            "⚠ The formal checks ran against the UNVERIFIED stub, not the real "
            "Lean-backed scherf package — treat confirmations as provisional."
        )
    parts.append(_BOUNDARY)
    return " ".join(parts)


@dataclass
class Verdict:
    """The result of evaluating one response. Non-mutating: it never alters the
    response text. The application decides what to do with ``action``."""

    action: Action
    violations: list[WitnessViolation] = field(default_factory=list)
    backend_name: str = ""
    backend_verified: bool = False
    transparency_note: str = ""

    @property
    def passed(self) -> bool:
        return self.action is Action.PASS

    @property
    def reframes(self) -> list[str]:
        return [v.reframe for v in self.violations if v.reframe]

    @property
    def extraction_confidence(self) -> float:
        """Confidence of the strongest finding driving the verdict (0 if PASS)."""
        return max((v.extraction_confidence for v in self.violations), default=0.0)

    def __str__(self) -> str:
        lines = [f"Verdict: {self.action.name}", self.transparency_note]
        for v in self.violations:
            lines.append("")
            lines.append(str(v))
        return "\n".join(lines)
