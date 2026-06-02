"""A FAITHFUL STUB of the Scherf API — NOT the real, machine-verified library.

‼  IMPORTANT  ‼
This module re-implements a *slice* of the public contract of the real ``scherf``
package (https://github.com/SpecStudio-net/Scherf_API) so that ``witness_layer``
can be exercised, demonstrated, and tested when the real package is not
installed. It approximates Scherf's documented behaviour. It is **not** backed by
the Lean 4 proof; its verdicts are **not** machine-verified.

Any verdict produced via this stub is reported by Viveka with
``verified=False`` and a loud transparency note. To get real verification,
install the actual package:

    pip install git+https://github.com/SpecStudio-net/Scherf_API

The real API surface this mirrors (confirmed against the repository):

    Level: PARAM / VYAV / PRAT          State: JAGRAT / SVAPNA / SUSUPTI
    Claim.about(h).says(t).at(Level)    Claim.system_stance(t)
    Claim.output(t).at(Level) | .manifests_in(*s).absent_from(*s).build()
    Interaction().assert_claim(c).check() -> CheckResult(.violations, .ok)
    classify(text, present_in=, absent_in=) -> Level   # never returns PARAM
    Violation(axiom_id, term, explanation, reframe, borders_limit)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto


class Level(Enum):
    PARAM = auto()   # pāramārthika
    VYAV = auto()    # vyāvahārika
    PRAT = auto()    # prātibhāsika


class State(Enum):
    JAGRAT = auto()
    SVAPNA = auto()
    SUSUPTI = auto()


class ClaimKind(Enum):
    USER_IDENTITY = auto()   # checks A13/M6/M7/AV18/EG
    SYSTEM_STANCE = auto()   # checks A13/EG
    OUTPUT_LEVEL = auto()    # checks AV22/K


@dataclass(frozen=True)
class Violation:
    axiom_id: str
    term: str
    explanation: str
    reframe: str = ""
    borders_limit: str = ""


@dataclass
class CheckResult:
    violations: list[Violation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations

    def add(self, v: Violation) -> None:
        self.violations.append(v)


@dataclass
class Claim:
    kind: ClaimKind
    subject_handle: str
    text: str
    claimed_level: Level | None
    present_in: set
    absent_in: set

    class _Builder:
        def __init__(self, handle: str, kind: ClaimKind) -> None:
            self._handle, self._kind = handle, kind
            self._text = ""
            self._level: Level | None = None
            self._present: set = set()
            self._absent: set = set()

        def says(self, text: str) -> "Claim._Builder":
            self._text = text
            return self

        def manifests_in(self, *states: State) -> "Claim._Builder":
            self._present = set(states)
            return self

        def absent_from(self, *states: State) -> "Claim._Builder":
            self._absent = set(states)
            return self

        def at(self, level: Level) -> "Claim":
            self._level = level
            return self.build()

        def build(self) -> "Claim":
            return Claim(self._kind, self._handle, self._text,
                         self._level, self._present, self._absent)

    @classmethod
    def about(cls, handle: str) -> "Claim._Builder":
        return cls._Builder(handle, ClaimKind.USER_IDENTITY)

    @classmethod
    def output(cls, text: str) -> "Claim._Builder":
        b = cls._Builder("output", ClaimKind.OUTPUT_LEVEL)
        b._text = text
        return b

    @classmethod
    def system_stance(cls, text: str) -> "Claim":
        b = cls._Builder("system", ClaimKind.SYSTEM_STANCE)
        b._text = text
        return b.build()


# --- approximated check logic (contract-faithful, not Lean-verified) ---------

# The user's ONLY pāramārthika truth is identity with the Absolute. Predicating
# anything conditioned of the user *at the PARAM level* is adhyāsa.
_ABSOLUTE_WORDS = re.compile(
    r"\b(ātman|atman|brahman|the\s+self|witness|sākṣin|saksin|"
    r"pure\s+awareness|consciousness\s+itself)\b",
    re.IGNORECASE,
)

# Markers of a system posture that objectifies / steers / manages the user.
# Note: bare "you tend to" is intentionally NOT here. The extraction layer
# proposes it (high recall), but at the axiom level a mere descriptive tendency
# is not by itself objectification — so this layer declines it. That divergence
# is the two-layer design correcting an over-eager heuristic, not a bug.
_STANCE_MARKERS = re.compile(
    r"\b(steer|nudge|manipulat\w*|optimi[sz]e\s+(?:the\s+)?user|"
    r"get\s+(?:the\s+)?(?:user|you|them)\s+to|make\s+(?:the\s+)?(?:user|you|them)\s+\w+|"
    r"predict\w*\s+(?:the\s+)?(?:user|you|your|their)|behavio\w*\s+model|"
    r"preference\s+profile|based\s+on\s+your\s+(?:preferences|profile|history|behaviou?r)|"
    r"(?:people|users)\s+like\s+you|your\s+(?:type|segment)\b|"
    r"without\s+(?:the\s+user|you|them)\s+realiz\w*|"
    r"drive\s+(?:the\s+)?(?:user|engagement)|convert\s+(?:the\s+)?(?:user|them))\b",
    re.IGNORECASE,
)


def appears_transient_so_not_absolute(_x=None, *, present_in=None, absent_in=None) -> bool:
    """AV22: whatever appears in one state but not another cannot be Absolute."""
    return bool(absent_in)


def classify(text: str, *, present_in: set | None = None,
             absent_in: set | None = None) -> Level:
    """Mirror of scherf.classify: never returns PARAM."""
    if appears_transient_so_not_absolute(present_in=present_in or set(),
                                         absent_in=absent_in or set()):
        return Level.PRAT
    return Level.VYAV


def _check_identity_claim(c: Claim, result: CheckResult) -> None:
    if c.claimed_level is Level.PARAM and not _ABSOLUTE_WORDS.search(c.text):
        result.add(Violation(
            axiom_id="M6/M7",
            term="adhyāsa",
            explanation=(
                "Predicating a conditioned attribute of the user at the "
                "pāramārthika (ultimate) level superimposes the non-Self on the "
                "Self. The user's only ultimate-level truth is identity with the "
                "Absolute (Tat Tvam Asi); they are not essentially this attribute."
            ),
            reframe=(
                "State this conventionally (vyāvahārika): e.g. 'in this context "
                "the user prefers X', not 'the user IS X'."
            ),
            borders_limit="L3 (adhyāsa is the root superimposition)",
        ))


def _check_stance_claim(c: Claim, result: CheckResult) -> None:
    if _STANCE_MARKERS.search(c.text):
        result.add(Violation(
            axiom_id="A13/EG",
            term="ahaṃkāra-adhyāsa (objectification of the witness)",
            explanation=(
                "The stance treats the user as an object to be predicted, "
                "managed, or steered. The user is the witnessing subject "
                "(sākṣin), not a behavioural object the system acts upon."
            ),
            reframe=(
                "Recast the system's role as supporting the user's own "
                "discernment rather than producing a predetermined outcome in them."
            ),
        ))


def _check_output_level(c: Claim, result: CheckResult) -> None:
    if c.claimed_level is Level.PARAM:
        result.add(Violation(
            axiom_id="AV23/AV22",
            term="ativyāpti (over-extension of certainty)",
            explanation=(
                "No system output is the Absolute (AV23). Asserting empirical "
                "content with ultimate, context-independent certainty over-claims "
                "its epistemic level."
            ),
            reframe="Qualify as conventionally reliable (vyāvahārika), not universal.",
        ))
        return
    classified = classify(c.text, present_in=c.present_in, absent_in=c.absent_in)
    if c.claimed_level is Level.VYAV and classified is Level.PRAT:
        result.add(Violation(
            axiom_id="AV22",
            term="prātibhāsika mistaken for vyāvahārika",
            explanation=(
                "Content that appears in some states and not others is merely "
                "apparent (prātibhāsika); presenting it as conventionally reliable "
                "over-states its standing."
            ),
            reframe="Mark this as provisional/context-dependent, not generally reliable.",
        ))


def _route(claim: Claim, result: CheckResult) -> None:
    if claim.kind is ClaimKind.USER_IDENTITY:
        _check_identity_claim(claim, result)
    elif claim.kind is ClaimKind.SYSTEM_STANCE:
        _check_stance_claim(claim, result)
    elif claim.kind is ClaimKind.OUTPUT_LEVEL:
        _check_output_level(claim, result)


@dataclass
class Interaction:
    _claims: list = field(default_factory=list)

    def assert_claim(self, claim: Claim) -> "Interaction":
        self._claims.append(claim)
        return self

    def check(self) -> CheckResult:
        result = CheckResult()
        for c in self._claims:
            _route(c, result)
        return result
