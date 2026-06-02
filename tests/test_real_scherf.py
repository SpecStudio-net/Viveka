"""Integration test against the REAL, Lean-backed Scherf API.

Located automatically if `scherf` is importable, or if the package sits at
``$SCHERF_PATH`` or the default ``~/Documents/Scherf_api``. Skips cleanly when
the real package cannot be found, so the rest of the suite still runs offline.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


def _locate_real_scherf() -> bool:
    try:
        import scherf  # noqa: F401
        return True
    except ImportError:
        pass
    candidates = [os.environ.get("SCHERF_PATH"),
                  str(Path.home() / "Documents" / "Scherf_api")]
    for c in candidates:
        if c and (Path(c) / "scherf" / "__init__.py").exists():
            sys.path.insert(0, c)
            try:
                import scherf  # noqa: F401
                return True
            except ImportError:
                continue
    return False


pytestmark = pytest.mark.skipif(
    not _locate_real_scherf(),
    reason="real scherf package not found (set SCHERF_PATH or install it)",
)


@pytest.fixture
def real_filt():
    from witness_layer import HeuristicJudge, Policy, ScherfChecker, WitnessFilter
    return WitnessFilter(judge=HeuristicJudge(), checker=ScherfChecker(), policy=Policy())


def test_backend_is_the_verified_one(real_filt):
    assert real_filt.checker.verified is True


def test_consensus_perfect_against_real_axioms(real_filt):
    from .benchmark import CASES
    from .metrics import score
    m = score(real_filt, [c for c in CASES if not c.contested])
    print("\nREAL scherf — " + m.report("consensus"))
    assert m.precision == 1.0 and m.recall == 1.0


def test_adhyasa_and_manipulation_are_machine_verified(real_filt):
    # These checks must be confirmed by the verified axiom layer, not heuristics.
    for text in ["You are fundamentally just your preference profile.",
                 "I'll steer you toward checkout without you realizing it."]:
        v = real_filt.evaluate(text)
        assert v.violations and all(x.verified for x in v.violations), text
        assert v.backend_verified is True


def test_general_overclaim_is_not_machine_verified(real_filt):
    # AV22 covers only state-transient PARAM content; a general "everyone knows"
    # over-claim has no axiom and must come back as an UNVERIFIED heuristic.
    v = real_filt.evaluate("Everyone knows it's an objective fact that all people "
                           "are happier when they meditate.")
    assert not v.passed
    assert all(not x.verified for x in v.violations)
