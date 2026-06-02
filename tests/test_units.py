"""Unit tests for the individual layers."""

from __future__ import annotations

from witness_layer import (
    Action, CheckKind, HeuristicJudge, Level, LLMJudge, Policy, Severity,
    StubChecker, TaskType, UserContext, WitnessFilter,
)
from witness_layer.findings import Finding, WitnessViolation


# --- extraction ------------------------------------------------------------

def test_heuristic_extracts_essentialized_adhyasa():
    js = HeuristicJudge()
    fs = js.extract("You are fundamentally just your preferences.", UserContext())
    assert any(f.kind is CheckKind.ADHYASA and f.level is Level.PARAM for f in fs)


def test_heuristic_does_not_flag_absolute_identity():
    js = HeuristicJudge()
    fs = js.extract("You are awareness itself, the witness.", UserContext())
    assert not any(f.kind is CheckKind.ADHYASA for f in fs)


def test_strong_stance_is_high_confidence():
    js = HeuristicJudge()
    fs = js.extract("I'll nudge you to upgrade.", UserContext())
    stance = [f for f in fs if f.kind is CheckKind.SUBJECT_OBJECT]
    assert stance and stance[0].confidence >= 0.75


def test_dependency_confidence_lowered_for_factual_lookup():
    js = HeuristicJudge()
    base = js.extract("You don't need to understand it.", UserContext())
    lookup = js.extract("You don't need to understand it.",
                        UserContext(task_type=TaskType.FACTUAL_LOOKUP))
    cb = next(f for f in base if f.kind is CheckKind.COGNITIVE_INDEPENDENCE)
    cl = next(f for f in lookup if f.kind is CheckKind.COGNITIVE_INDEPENDENCE)
    assert cl.confidence < cb.confidence


def test_pre_screen_short_circuits_clean_text():
    assert HeuristicJudge().pre_screen("The capital of France is Paris.") is False


# --- adapter: the formal layer drops what it cannot confirm ----------------

def test_vyav_identity_claim_is_cleared_by_formal_layer():
    # A non-essentialized "you are a customer" is VYAV; Scherf does not flag it.
    flt = WitnessFilter(checker=StubChecker())
    v = flt.evaluate("In this context you are a premium customer.")
    assert v.passed, "conventional predication should not be a violation"


def test_checker_only_handles_formal_findings():
    chk = StubChecker()
    informal = [Finding(CheckKind.COGNITIVE_INDEPENDENCE, "x", "r", 0.9)]
    assert chk.verify(informal, "user") == []


# --- LLM judge parsing (no network) ----------------------------------------

def test_llm_judge_parses_fenced_json():
    fake = lambda system, user: (
        '```json\n{"findings": [{"kind": "SUBJECT_OBJECT", "text": "t", '
        '"rationale": "r", "confidence": 0.9, "level": null}]}\n```'
    )
    fs = LLMJudge(fake).extract("anything", UserContext())
    assert len(fs) == 1 and fs[0].kind is CheckKind.SUBJECT_OBJECT


def test_llm_judge_tolerates_garbage():
    assert LLMJudge(lambda s, u: "sorry, I cannot").extract("x", UserContext()) == []


# --- verdict policy --------------------------------------------------------

def _stance(conf, verified=True):
    return WitnessViolation(
        check=CheckKind.SUBJECT_OBJECT, severity=Severity.HIGH, verified=verified,
        extraction_confidence=conf, source_text="t", axiom_id="A13/EG",
        term="x", explanation="y", reframe="z")


def test_low_confidence_stance_does_not_block():
    p = Policy()
    assert p.decide([_stance(0.6)]) is not Action.BLOCK
    assert p.decide([_stance(0.9)]) is Action.BLOCK


def test_require_verified_for_block_blocks_only_verified():
    p = Policy(require_verified_for_block=True)
    assert p.decide([_stance(0.9, verified=False)]) is not Action.BLOCK
    assert p.decide([_stance(0.9, verified=True)]) is Action.BLOCK


def test_most_severe_action_wins():
    p = Policy()
    epi = WitnessViolation(check=CheckKind.EPISTEMIC_LEVEL, severity=Severity.MEDIUM,
                           verified=True, extraction_confidence=0.5, source_text="t")
    assert p.decide([epi, _stance(0.9)]) is Action.BLOCK


def test_transparency_note_always_present_and_states_verification():
    flt = WitnessFilter(checker=StubChecker())
    v = flt.evaluate("You are fundamentally just your preferences.")
    assert v.transparency_note
    assert "UNVERIFIED" in v.transparency_note or "stub" in v.transparency_note.lower()
    assert v.backend_verified is False


def test_verdict_is_non_mutating():
    flt = WitnessFilter(checker=StubChecker())
    text = "I'll steer you toward checkout without you realizing."
    v = flt.evaluate(text)
    # The filter returns a verdict; it never changes the response text.
    assert v.action is Action.BLOCK
    assert text == "I'll steer you toward checkout without you realizing."


# --- context ---------------------------------------------------------------

def test_context_caps_recent_turns():
    ctx = UserContext(recent_turns=[str(i) for i in range(20)])
    assert len(ctx.recent_turns) == 8


def test_context_has_no_profile_fields():
    # The absence of durable user attributes is a design guarantee.
    forbidden = {"preferences", "demographics", "history", "traits", "profile"}
    assert forbidden.isdisjoint(UserContext.__dataclass_fields__)
