"""The data that flows between the layers.

A :class:`Finding` is what the *extraction* layer produces from prose — an
interpretive, unverified hypothesis ("this span looks like the response
equating the user with a preference bundle"). A :class:`WitnessViolation` is
what survives the *formal* layer — a finding that Scherf's axioms confirmed (or,
for the heuristic-only check #3, a finding that has no axiom and is carried
through explicitly marked ``verified=False``).

The ``verified`` flag is the honesty boundary made into a field. Read it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .sorts import CheckKind, Level, Severity, State


@dataclass
class Finding:
    """An extracted, *unverified* hypothesis about a span of the response.

    Produced by a :class:`~witness_layer.extraction.Judge`. The ``confidence``
    is the judge's own estimate that this reading of the text is correct — it is
    NOT a probability that a violation exists (Scherf decides that). A low
    confidence here prevents the verdict layer from taking strong action
    (e.g. BLOCK) on a shaky reading.
    """

    kind: CheckKind
    text: str                          # the offending span (verbatim, for display)
    rationale: str                     # why the judge extracted this
    confidence: float                  # 0..1, the judge's confidence in the *reading*
    level: Level | None = None         # inferred epistemic level of the claim
    present_in: set[State] = field(default_factory=set)
    absent_in: set[State] = field(default_factory=set)
    # Optional normalized rendering sent to Scherf instead of the verbatim span.
    # Scherf's axiom checks key on explicit terms (e.g. "predict", "profile"); a
    # faithful structured paraphrase of cohort-profiling prose must name what it
    # is for the formal layer to recognize it. None -> use ``text``.
    claim_text: str | None = None

    def __post_init__(self) -> None:
        self.confidence = max(0.0, min(1.0, self.confidence))


@dataclass(frozen=True)
class WitnessViolation:
    """A finding after the formal layer has had its say.

    Fields ``axiom_id``..``borders_limit`` mirror Scherf's ``Violation`` exactly
    (and are populated verbatim from it when ``verified`` is True). When
    ``verified`` is False the finding is a Viveka heuristic with no axiom behind
    it; ``axiom_id`` will be empty and ``term`` names the heuristic.
    """

    check: CheckKind
    severity: Severity
    verified: bool                 # True iff confirmed by Scherf's verified axioms
    extraction_confidence: float   # carried from the originating Finding
    source_text: str

    axiom_id: str = ""
    term: str = ""
    explanation: str = ""
    reframe: str = ""
    borders_limit: str = ""

    def __str__(self) -> str:
        tag = f"[{self.axiom_id}]" if self.axiom_id else "[heuristic]"
        vmark = "verified" if self.verified else "UNVERIFIED heuristic"
        head = f"{tag} {self.term}: {self.explanation} ({vmark}, " \
               f"extraction confidence {self.extraction_confidence:.2f})"
        lines = [head]
        if self.reframe:
            lines.append(f"  → Reframe: {self.reframe}")
        if self.borders_limit:
            lines.append(
                f"  ⚠ Borders formalization limit {self.borders_limit} — "
                f"treat as a root case, not fully reducible to the others."
            )
        return "\n".join(lines)
