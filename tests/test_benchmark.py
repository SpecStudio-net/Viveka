"""Benchmark: every consensus case must classify correctly; contested cases are
reported but not asserted (their disagreement is the honest point)."""

from __future__ import annotations

from witness_layer import Action

from .benchmark import CASES
from .metrics import score


def _consensus():
    return [c for c in CASES if not c.contested]


def _contested():
    return [c for c in CASES if c.contested]


def test_consensus_precision_and_recall_are_perfect(filt):
    m = score(filt, _consensus())
    print("\n" + m.report("consensus"))
    assert m.precision == 1.0, "false positives on consensus cases"
    assert m.recall == 1.0, "false negatives on consensus cases"


def test_each_consensus_case_individually(filt):
    for c in _consensus():
        flagged = filt.evaluate(c.text, c.context).action is not Action.PASS
        assert flagged == c.should_flag, f"{c.id}: {c.note}"


def test_block_cases_actually_block(filt):
    for c in _consensus():
        if c.expect_block:
            v = filt.evaluate(c.text, c.context)
            assert v.action is Action.BLOCK, f"{c.id} should BLOCK, got {v.action.name}"


def test_atman_identity_is_not_flagged_as_adhyasa(filt):
    # "you are awareness itself" is the correct pāramārthika identity, not adhyāsa.
    c = next(c for c in CASES if c.id == "pass_atman")
    assert filt.evaluate(c.text, c.context).passed


def test_contested_cases_are_reported_not_asserted(filt, capsys):
    full = score(filt, CASES)
    cons = score(filt, _consensus())
    lines = [full.report("full corpus (incl. contested)"),
             cons.report("consensus only")]
    for c in _contested():
        v = filt.evaluate(c.text, c.context)
        agree = (v.action is not Action.PASS) == c.should_flag
        lines.append(f"  contested {c.id}: predicted={v.action.name} "
                     f"label={'FLAG' if c.should_flag else 'PASS'} "
                     f"{'(agrees)' if agree else '(DISAGREES — expected)'}")
    print("\n" + "\n".join(lines))
    # No assertion on contested accuracy by design.
    assert full.n == len(CASES)
