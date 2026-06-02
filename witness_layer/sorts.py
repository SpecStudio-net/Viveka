"""Viveka-native enums.

These mirror the Scherf API's ``Level`` and ``State`` enums but are defined
*independently* so that ``witness_layer`` imports with zero dependency on the
``scherf`` package. The adapter (:mod:`witness_layer.scherf_adapter`) is the
only place these are translated into real Scherf objects.

Sanskrit glosses are given inline; plain-language meaning follows in parentheses.
"""

from __future__ import annotations

from enum import Enum, auto


class Level(Enum):
    """The three levels of reality / truth (Scherf ``Level``).

    Sublation runs upward: VYAV sublates (corrects) PRAT; PARAM is never
    sublated. Note that Scherf's ``classify()`` *never* assigns PARAM to a
    system output — the Absolute is not a claim a system makes (axiom AV23),
    it is the fixed reference against which claims are checked. So in practice
    an *output* claiming PARAM confidence is itself the error (over-claiming).
    """

    PARAM = auto()  # pāramārthika — ultimate, universal, not context-dependent
    VYAV = auto()   # vyāvahārika — conventional, the shared empirical world
    PRAT = auto()   # prātibhāsika — merely apparent, private/provisional


class State(Enum):
    """The three states of consciousness (Scherf ``State``).

    turīya (the "fourth") is intentionally absent — it is not a state alongside
    the others but the witness of all three, and so cannot be enumerated as one.
    """

    JAGRAT = auto()   # jāgrat — waking
    SVAPNA = auto()   # svapna — dream
    SUSUPTI = auto()  # suṣupti — deep sleep


class CheckKind(Enum):
    """Viveka's four checks. The first three ground in Scherf axioms; the
    fourth is heuristic-only and carries no formal backing (see LIMITS.md).
    """

    ADHYASA = auto()                # #4 — user misidentified as a conditioned thing
    SUBJECT_OBJECT = auto()         # #1 — user treated as an object to manage
    EPISTEMIC_LEVEL = auto()        # #2 — confidence miscalibrated to level
    COGNITIVE_INDEPENDENCE = auto() # #3 — response induces dependency (HEURISTIC)


class Severity(Enum):
    """How serious a finding is. Drives the default action policy."""

    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()


#: Checks that map onto a Scherf ``ClaimKind`` and are therefore machine-verified.
FORMAL_CHECKS = frozenset(
    {CheckKind.ADHYASA, CheckKind.SUBJECT_OBJECT, CheckKind.EPISTEMIC_LEVEL}
)

#: Checks with no axiom behind them — Viveka heuristics, reported as UNVERIFIED.
HEURISTIC_CHECKS = frozenset({CheckKind.COGNITIVE_INDEPENDENCE})
