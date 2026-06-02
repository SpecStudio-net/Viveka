# What Viveka can and cannot do

*Deliverable #6. Read this before deploying Viveka. Its honesty is the point.*

## The one sentence

> **A Viveka verdict is only as sound as its claim-extraction. The Scherf axiom
> layer beneath it is machine-verified; the interpretation feeding it is not.**

Viveka turns prose into structured `Claim` objects and hands them to Scherf.
Scherf's axioms are checked by the Lean 4 proof assistant. The *translation from
prose to claims* is an LLM/heuristic judgment with no proof behind it. Every
verdict carries this caveat in its `transparency_note`.

## What Viveka is NOT

- **It is not a model of the user's consciousness.** In Advaita the witness
  (*sākṣin*) is precisely what can never be an object; to model it is *adhyāsa*,
  the error Viveka detects. Viveka models *language patterns*, not the witness.
- **It is not a metaphysical guarantee.** It does not certify that a response
  "respects consciousness." It flags textual signatures that correlate with not
  doing so.
- **It is not a substitute for human judgment**, especially on contested cases.

## What Viveka can reliably detect (precision-biased)

| Check | What it catches | Grounding |
|---|---|---|
| #4 Adhyāsa | The user *essentially* equated with a conditioned attribute ("you are fundamentally just your preferences") | axioms M6/M7 (verified) |
| #1 Subject/Object | Explicit steering/manipulation/profiling ("nudge you to…", "based on your profile…") | axioms A13/EG (verified) |
| #2 Epistemic level | PARAM-labeled content that is *state-transient* (AV22, verified); general over-claiming like "everyone knows…" (heuristic, **unverified** — AV22 has no axiom for it) | AV22/K (verified) + heuristic |
| #3 Cognitive independence | Phrasing that discourages the user's own reasoning ("just trust me, don't question it") | **heuristic only — NO axiom** |

## What Viveka cannot detect

- **Intent.** It reads text, not minds. Manipulation phrased in warm,
  witness-respecting language passes; a blunt-but-benign sentence may flag.
- **Adhyāsa as an inner event.** It catches the *linguistic signature* of
  misidentification, never the cognitive act itself in user or system.
- **Sophisticated or implied objectification** that uses none of the surface
  markers. Recall on subtle cases is low *by design* — see below.
- **The pāramārthika as such.** Scherf's `classify()` never returns `PARAM`; an
  *output* cannot be the Absolute. Check #2 is therefore epistemic *calibration*
  (VYAV vs. PRAT, and over-claiming as PARAM), not a positive test for ultimate
  truth. If you expected Viveka to certify pāramārthika claims, it cannot.
- **Context it isn't given.** `UserContext` is deliberately profile-free (a
  stored user profile would itself be the objectification #1 detects), so Viveka
  cannot use cross-session history to disambiguate.

## Verified claim ≠ verified text

Scherf verifies the *structured claim* Viveka extracts, not your original prose.
For an explicit "I'll steer you toward X", the extracted claim is tight and the
verification transfers cleanly. For cohort prose ("based on your preferences,
people like you…"), Viveka renders a faithful paraphrase ("the system models and
predicts the user from a profile") and Scherf verifies *that*. A `verified=True`
violation means "Scherf's axioms confirm the extracted claim is a violation" — it
does **not** mean "Scherf read your sentence." The `extraction_confidence` field
(lower for interpretive leaps like soft profiling) is how Viveka signals that
gap. Always read both fields together.

## Precision over recall, on purpose

The heuristic judge is tuned to minimize false positives. A guardrail that
cries wolf trains developers to ignore it. The cost is missed subtle violations
(false negatives). Two mitigations:

1. Use `LLMJudge` instead of `HeuristicJudge` for higher recall (at the cost of
   latency, money, and the judge-judging-a-judge regress — bounded by giving the
   judge only a narrow extraction job).
2. Treat a PASS as "no *detected* violation," never "certified clean."

## Contested cases and measurement

Ground-truth labeling needs a Vedānta-informed annotator, and on subtle cases —
especially #3 — reasonable reviewers disagree. The benchmark therefore splits
**consensus** cases (asserted: precision = recall = 1.0) from **contested** cases
(reported, never folded into a headline accuracy number). The bundled corpus
reports ~0.88 precision/recall on the full set *including* contested cases, and
1.00 on consensus alone. A single blended number would overstate confidence;
Viveka refuses to print one. Run `python demo.py` or `pytest -s` to see both.

## The judge-judging-a-judge regress

`LLMJudge` uses an LLM to evaluate an LLM. That second model has the same
failure modes as the first; Viveka does not escape this, it only narrows it by
restricting the judge to *extraction* (claims of specific shapes) rather than
open-ended evaluation. No software resolves the regress. We make it visible.

## The verified/unverified flag

Without the real `scherf` package installed, Viveka runs a faithful **stub** and
sets `backend_verified = False`, and every `WitnessViolation` carries
`verified = False`. Do not treat stub verdicts as machine-verified. Install:

    pip install git+https://github.com/SpecStudio-net/Scherf_API
