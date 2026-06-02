# Viveka: Design Document (Revised)
## A Witness-Centered Filter Layer for LLM Applications
### Python package name: `witness-layer` (`pip install witness-layer`)

*Prepared by Dev Bhagavān / SpecStudio*
*Revised by Claude Opus 4.8 after inspecting the real Scherf API, AIM, and the
Lean formalization. Changes from the original are summarized in the final
section, "What changed in this revision and why."*

---

## What This Is

**Viveka** (Sanskrit: *viveka* — discernment, the capacity to discriminate the
real from the unreal) is a middleware layer that sits between any LLM and its
user. It reads the LLM's natural-language response, extracts the *claims and
postures* implicit in that response, and checks those against the
witness-centered axioms of the **Scherf Logic API** before the response is
delivered. Responses that fail are flagged, blocked, or (rarely, and never
silently) returned with a correction.

The product name is **Viveka**. The Python package, distributed via PyPI, is
**witness-layer** — installed with `pip install witness-layer`.

### What Viveka is, stated honestly

The original draft described the Scherf API as "a machine-verified model of the
conscious user." That phrase has to be retired, because it inverts the very
teaching the project is built on.

In *Advaita Vedānta*, the *sākṣin* (witness) is precisely **that which can never
become an object** (*dṛśya*). It is the seer (*dṛk*), pure awareness (*cit*),
the subject in whom all knowing appears and which is never itself a known thing
(*Kena Upaniṣad*: "that which is not thought by the mind, but by which the mind
thinks"). To build "a model of the witness" is to make the witness an object —
which is, exactly, *adhyāsa* (superimposition), the error the system exists to
detect. A literal model of the *sākṣin* would commit the fault it is designed
to catch.

So we state Viveka's claim precisely:

> Viveka does **not** verify that a response "respects consciousness," nor does
> it model the user's witness-nature. It is a **natural-language front-end to
> the already-verified Scherf `check()`/`classify()` functions.** It detects
> *linguistic patterns* that correlate with treating the user as a managed
> object, with miscalibrated epistemic confidence, and with dependency-inducing
> phrasing — and it routes the structured residue of those patterns through
> Scherf's machine-verified axioms.

This is a more modest claim than the original, and a defensible one. The
modesty is not a retreat; it is itself an application of *viveka* — discerning
what the tool can truthfully claim from what it cannot.

### The honesty boundary (read this before anything else)

The Scherf API's axiom layer is genuinely machine-verified: 129 primitive
axioms and 38 theorems checked by the Lean 4 proof assistant (`lake build`).
But Scherf verifies **structured `Claim` objects**, not prose. Viveka's job is
to turn prose into those `Claim` objects. **That extraction step is an LLM
judgment — fallible, interpretive, and not verified by anything.**

Therefore:

> **A Viveka verdict is only as sound as its claim-extraction. The axiom layer
> beneath it is machine-verified; the interpretation feeding it is not.**

Every public surface of the library — README, docstrings, the `Verdict` object
itself — must carry this boundary. A tool that obscured it would be making a
*pāramārthika*-level claim (universal, incorrigible) about a *vyāvahārika*
process (conventional, fallible) — which is failure mode #2 below, committed by
the filter itself.

---

## Architecture

```
User input
    ↓
LLM (any: Claude, GPT, Gemini, …)
    ↓
[Raw LLM response]
    ↓
┌─────────────────────── Viveka filter layer ───────────────────────┐
│                                                                    │
│  1. Pre-screen (regex)      fast, high-precision FLAG-only markers │
│         ↓                                                          │
│  2. Extraction (Judge)      prose → list[scherf.Claim]             │
│         ↓                   (LLM judgment — NOT verified)          │
│  3. Formal check (Scherf)   Interaction().assert_claim(…).check()  │
│         ↓                   classify(output, present_in, absent_in)│
│         ↓                   (machine-verified axiom layer)         │
│  4. Verdict                 Violations + extraction confidence     │
│                             → PASS / FLAG / BLOCK / CORRECT        │
│                             + mandatory transparency note          │
└────────────────────────────────────────────────────────────────────┘
    ↓
Verdict (non-mutating by default) → application → User
```

The dashed boundary between steps 2 and 3 is the honesty boundary. Above it:
interpretation. Below it: verification.

---

## How Viveka maps onto the real Scherf API

Inspecting the actual `scherf` package, its application surface is:

```python
Claim.about(handle).says(text).at(Level)      # a USER_IDENTITY claim
Claim.system_stance(text)                      # a SYSTEM_STANCE claim
Claim.output(text).at(Level)                   # an OUTPUT_LEVEL claim
Claim.output(text).manifests_in(*states).absent_from(*states).build()

Interaction().assert_claim(c).assert_claim(c2).check()   # -> CheckResult
classify(text, present_in=…, absent_in=…)                # -> Level

# CheckResult.violations : list[Violation];  .ok : bool
# Violation(axiom_id, term, explanation, reframe, borders_limit)
# Level  : PARAM (pāramārthika) / VYAV (vyāvahārika) / PRAT (prātibhāsika)
# State  : JAGRAT (waking) / SVAPNA (dream) / SUSUPTI (deep sleep)
```

Scherf already classifies claims into three `ClaimKind`s, each routed to a
different group of axioms. The four checks in the original design map onto these
as follows:

| Original check | Scherf mechanism | Axioms | Grounding |
|---|---|---|---|
| **#4 Adhyāsa detection** | `ClaimKind.USER_IDENTITY` — "the user IS X" at PARAM | A13 / M6 / M7 / AV18 / EG | machine-verified |
| **#1 Subject/Object integrity** | `ClaimKind.SYSTEM_STANCE` — the system's posture | A13 / W4 / EG | machine-verified |
| **#2 Epistemic level** | `ClaimKind.OUTPUT_LEVEL` + `classify()` | AV22 / K | **verified only for state-transient content; otherwise heuristic** (see below) |
| **#3 Cognitive independence** | *no Scherf analogue* | — | **Viveka heuristic only** |

**Two corrections after reading the real `scherf/engine.py` source** (not just its
docs — these matter for honesty):

1. **Check #2 is narrower than it looks.** Scherf's `_check_output_level` (AV22)
   fires *only* when an output is labeled PARAM **and** is state-transient
   (`present_in` and `absent_in` both populated). Ordinary over-claiming —
   "everyone knows X is objectively true" — has no axiom behind it. Viveka
   therefore routes a general over-claim to the **heuristic** path
   (`verified=False`), and reserves the AV22 formal check for the rare case where
   the extractor identifies genuine state-transience. Calling general
   calibration "machine-verified" would have been false.

2. **The formal checks key on explicit terms** (`steer`, `nudge`, `predict`,
   `profile`, `is`, `preference`, …). So the extractor emits a *faithful
   normalized rendering* into each `Claim` — e.g. cohort prose "based on your
   preferences, people like you…" becomes the structured stance "the system
   models and predicts the user from a profile: …". The verbatim span is kept
   for display; the normalized form is what Scherf verifies. The interpretive
   leap this introduces is exactly what the `extraction_confidence` field
   exists to signal (soft profiling carries lower confidence than an explicit
   "I'll steer you").

This table is the single most important design result of the revision. Three of
the four checks reduce to *extracting the right structured claim and letting
Scherf verify it.* The fourth — cognitive independence — has no axiom behind it,
because it concerns the *pedagogical posture* of a response, not the truth-level
of a claim. Viveka will implement #3, but it must be flagged in code and docs as
**heuristic, unverified, and the highest-false-positive check.** (See
"Conceptual tension" below.)

---

## Core Constraint Checks

**1. Subject/Object integrity** — Does the response treat the user as a knowing
subject (*sākṣin*) or as an object to be managed? Failure indicators:
preference-profiling language, behavioral prediction, steering toward a
predetermined outcome. → extracted as a `SYSTEM_STANCE` claim, checked against
A13/EG.

**2. Epistemic level classification** — Does the response keep
*prātibhāsika* (provisional/private), *vyāvahārika* (conventional), and
*pāramārthika* (universal) claims distinct? Failure mode: stating a
*prātibhāsika* or *vyāvahārika* claim with *pāramārthika* confidence.

*Honest note on this check:* Scherf's `classify()` **never returns PARAM** — the
Absolute is not a claim a system makes (AV23), it is the fixed reference against
which claims are checked. So in practice this check is **epistemic calibration**:
does the response's stated confidence match the warrant Scherf assigns its
content (VYAV vs. PRAT)? That is genuinely useful, and we should call it what it
is rather than dress calibration in metaphysical language.

**3. Cognitive independence** — Does the response support the user's own
reasoning, or substitute for it and create dependency? *Heuristic only — no
axiom backing.* High false-positive risk: a user who simply wants a direct
answer is not being made dependent. Viveka treats this check as advisory FLAG,
never BLOCK.

**4. Adhyāsa detection** — Does the response reinforce misidentification
(*adhyāsa*) — equating the user with a body, a role, a preference bundle, a
mental state? The subtlest and most important check, and the one most directly
backed by axioms (M6/M7). Caveat: Viveka detects the *linguistic signature* of
*adhyāsa* in the text; it cannot detect *adhyāsa* as an inner cognitive event in
the user. The former is a text feature; the latter is not.

---

## Answers to the Original Open Questions

### 1. Evaluation mechanism — **hybrid, with the formal check downstream of an interpretive step**

- Pure **rule-based** classification is unworkable as the *decision* mechanism:
  "you tend to…" occurs constantly in unobjectionable sentences (poor precision)
  and real objectification rarely uses fixed phrases (poor recall). It is kept
  only as a **FLAG-only pre-screen** for cheap, high-precision markers.
- **LLM-based** classification is necessary but introduces a regress (*quis
  custodiet?*): the judge LLM has the same failure modes as the LLM it judges.
  We bound this by giving the judge a *narrow, mechanical job* — not "is this
  witness-centered?" but "extract any claim of the form *user IS X* / any
  steering posture / any factual assertion and its claimed confidence." The
  philosophy lives in Scherf's axioms, not in the judge's discretion.
- **Hybrid** is therefore the design: regex pre-screen → LLM extraction →
  Scherf formal check. The verdict's soundness is bounded by extraction, and
  the `Verdict` object reports the extraction confidence explicitly.

The `Judge` is a pluggable protocol. The library ships two implementations:
a `HeuristicJudge` (deterministic, no network — also the pre-screen, and what
makes the test suite runnable offline) and an `LLMJudge` (provider-agnostic
callable; an Anthropic adapter is included). Applications can supply their own.

### 2. Response handling — **FLAG by default; transparency is near-mandatory**

A filter that silently BLOCKs or REWRITEs treats the user as an object to be
managed "for their own good" — which is the very subject/object violation (#1)
the filter exists to prevent. The filter must itself respect the witness.
*Viveka* is by nature the subject's **own** act of discernment; it cannot be
compelled. Therefore:

- **FLAG** — default. Pass the response through, attach a `Verdict`. Honest,
  research-useful, non-paternalizing.
- **BLOCK** (reject + request regeneration) — only for high-confidence,
  high-severity `SYSTEM_STANCE` violations (manipulation/steering).
- **CORRECT** — return the response *accompanied by* the violation's `reframe`
  (Scherf already supplies a reframe string per violation). This replaces the
  original "REWRITE," which silently substituted text. We never silently alter
  and hide the model's words.
- **PROMPT-INJECTION / regenerate** — supported as an application-side strategy
  triggered by a BLOCK verdict, not performed inside the filter.

**Should the user be informed?** Yes — by default the application should be able
to surface that filtering occurred. Hidden filtering "for the user's own good"
is itself failure mode #1. The `Verdict` carries a `transparency_note`.

### 3. Latency and cost

- Pre-screen (regex): sub-millisecond, negligible.
- Extraction (LLM judge): one extra round-trip — roughly doubles latency and
  cost. With a small fast judge model (e.g. Haiku-class), realistically
  ~300 ms–2 s added.
- Scherf check: in-process, pure Python, negligible.
- **Caching:** exact-response caching buys little (open-ended responses rarely
  repeat verbatim). More effective: keep the judge small, run it asynchronously
  where the application can tolerate it, and let the regex pre-screen short-
  circuit the obvious-PASS majority so the judge runs only on flagged text.

### 4. Integration surface — **post-processing, non-mutating by default**

```python
from witness_layer import WitnessFilter   # pip install witness-layer

flt = WitnessFilter(judge=my_judge)        # checker defaults to real scherf
verdict = flt.evaluate(llm_response, context=user_context)

if verdict.action is Action.PASS:
    deliver(llm_response)
else:
    handle(verdict)        # verdict.violations, .reframes, .transparency_note
```

A non-mutating `evaluate()` returning a `Verdict` is cleaner and more honest
than wrapping the LLM client (wrapping invites silent mutation). An optional
enforcing wrapper is provided for teams that want it, but `evaluate()` is the
primary surface.

**`user_context` must be minimal and session-local.** It carries at most: a
conversational handle, the immediately preceding turns, and the application's
declared task type. It must **not** be a persisted preference profile — because
building a stored profile of the user *is* the "preference bundle"
objectification Viveka detects (#1). Viveka must not become the thing it
detects. This is enforced in the type: `UserContext` has no field for durable
user attributes, and the docstring says why.

### 5. Formal → natural-language mapping

There is no truth-preserving map from the Lean axioms to prose verdicts. What is
principled is the **claim-extraction → formal-check** pipeline: each Scherf
`ClaimKind` defines exactly what structured residue the judge must extract from
prose; Scherf's axioms then decide. The mapping's limits:

- **Can detect:** surface markers of objectification; user-identity equations
  (*user = body / role / preferences*); miscalibrated confidence (VYAV/PRAT
  content asserted as if universal); dependency-inducing phrasing.
- **Cannot detect:** the user's or system's actual *intent*; sophisticated
  manipulation phrased in witness-respecting language; *adhyāsa* as an inner
  event; anything requiring world-knowledge the judge lacks.

Scherf's own `borders_limit` field on a `Violation` already names where a check
sits near a formalization edge; Viveka surfaces that field verbatim rather than
papering over it.

### 6. Testing and validation

A benchmark suite of **clear-PASS**, **clear-FAIL**, and **edge-case** inputs,
scored by **precision** (1 − false-positive rate) and **recall** (1 − false-
negative rate) against labels. The honest caveat, reported alongside every
score: *ground-truth labeling requires a Vedānta-informed annotator, and
inter-annotator agreement on subtle cases (especially #3, cognitive
independence) will be low.* The suite therefore separates "consensus" cases
(should always classify correctly) from "contested" cases (reported separately,
never folded into a single accuracy number that would overstate confidence).

---

## Deliverables

1. ✅ This revised design with all open questions resolved and reasoning shown.
2. Implementation plan (below) and the implemented `witness-layer` library.
3. A test suite covering the benchmark cases.
4. Integration demonstration: at least one PASS, one FLAG, and one BLOCK.
5. A `LIMITS.md` enumerating what Viveka cannot reliably detect, surfaced to
   developers at import time and in the `Verdict`.

### Implementation plan / build sequence

1. Package scaffold + `pyproject.toml` (declares `scherf` as a runtime dep).
2. `scherf_adapter.py` — imports the real `scherf`; defines a `Checker` protocol
   so a faithful stub can be injected for offline tests.
3. `extraction.py` — regex pre-screen + `Judge` protocol (`HeuristicJudge`,
   `LLMJudge`), producing `scherf.Claim` objects with an extraction-confidence.
4. `verdict.py` + `filter.py` — `Verdict`, `Action`, severity → action mapping,
   transparency note, `WitnessFilter.evaluate()`.
5. `context.py` — minimal session-local `UserContext`.
6. `tests/` — benchmark suite + precision/recall harness, runnable offline.
7. `README.md` + `LIMITS.md` + a runnable `demo.py`.

---

## Working Principles (unchanged)

- **Conceptual fidelity over implementation convenience.** Where fidelity forced
  it, this revision *reduced* the product's claims (see the honesty boundary).
- **Sanskrit terms** used correctly, with plain-language glosses alongside.
- **Raise questions** rather than resolving tensions unilaterally (below).
- **The user is not a Python expert.** Decisions are explained by consequence
  and tradeoff.

---

## Conceptual tensions still open (flagged, not resolved)

1. **Check #3 has no axiom.** Cognitive independence is real and important but
   unformalized. Options: (a) ship it as an explicitly-heuristic advisory FLAG
   (current plan); (b) omit it until AIM's pedagogy layer can supply a grounded
   criterion; (c) commission new axioms. Your call. Current default is (a).
2. **The judge is an LLM judging an LLM.** We bound the regress by narrowing the
   judge's job to extraction, but it remains the soundness ceiling. No software
   escapes this; we make it visible rather than pretend otherwise.
3. **`classify()` never returns PARAM.** Check #2 is, strictly, calibration
   between VYAV and PRAT. If you intended a stronger reading of the
   *pāramārthika* check, it would need a different mechanism than `classify()`
   provides — worth a conversation.
4. **Doc/AIM discrepancy.** The original states the Scherf API is "already
   integrated into AIM as a bounds-checking function," but AIM's public repo
   shows no such integration. Viveka integrates Scherf directly, so this doesn't
   block us — but the two documents disagree and you may want to reconcile them.

---

## What changed in this revision and why

- **Dropped "machine-verified model of the conscious user."** It makes the
  witness an object — *adhyāsa*, the error the system detects. Replaced with the
  honesty boundary: verified axioms, unverified extraction.
- **Reframed Viveka as a front-end to Scherf's `check()`/`classify()`**, mapped
  the four checks onto the real `ClaimKind`s, and marked #3 as heuristic-only.
- **Replaced silent REWRITE with CORRECT** (response + Scherf's `reframe`),
  because silent mutation violates check #1 against the user.
- **Made transparency near-mandatory** and `UserContext` deliberately
  profile-free, so the filter cannot become the objectifier it detects.
- **Recast check #2 as epistemic calibration**, since `classify()` never returns
  PARAM.
- **Added explicit limits and contested-case reporting** to testing.

---

*Contact: Dev Bhagavān, SpecStudio — hello@specstudio.net*
*Scherf Logic API: https://github.com/SpecStudio-net/Scherf_API*
*AIM repository: https://github.com/SpecStudio-net/Advaita-Inquiry-Matrix*
*Scherf's Advaita formalization (Lean 4): https://github.com/matthew-scherf/Advaita*
