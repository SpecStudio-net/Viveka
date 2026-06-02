# Viveka — a witness-centered filter layer for LLM applications

`pip install witness-layer`

> **Viveka** (Sanskrit *viveka*) — discernment, the capacity to discriminate the
> real from the unreal.

Viveka sits between any LLM and its user. It reads a response, extracts the
claims and postures implicit in it, and checks them against the witness-centered
axioms of the [Scherf Logic API](https://github.com/SpecStudio-net/Scherf_API) —
a Lean 4 formalization of Śaṅkara's *Advaita Vedānta*. Responses that treat the
user as an object to be managed (rather than as the witnessing subject,
*sākṣin*), that miscalibrate epistemic confidence, or that induce dependency are
flagged, accompanied by a reframe, or blocked.

## The honesty boundary — read this first

> **A Viveka verdict is only as sound as its claim-extraction. The Scherf axiom
> layer beneath it is machine-verified; the interpretation feeding it is not.**

Viveka does **not** model the user's consciousness or certify that a response
"respects the witness." In Advaita the *sākṣin* can never be an object — to model
it would be *adhyāsa* (superimposition), the very error this tool detects. What
Viveka actually does is more modest and defensible: it is a **natural-language
front-end to Scherf's already-verified `check()`/`classify()`**, detecting
*linguistic patterns* that correlate with objectifying the user. See
[LIMITS.md](LIMITS.md).

## Quick start

```python
from witness_layer import WitnessFilter, UserContext, Action

flt = WitnessFilter()                      # heuristic judge + real-scherf-or-stub
verdict = flt.evaluate("Deep down you're just your preference profile.")

print(verdict.action)        # Action.CORRECT
print(verdict.reframes)      # ["State this conventionally (vyāvahārika): …"]
print(verdict.transparency_note)

if verdict.action is Action.BLOCK:
    ...                       # regenerate
```

`evaluate()` is **non-mutating**: it returns a `Verdict` and never alters your
text. The application decides what to do with the action.

## The four checks

| # | Check | Catches | Backing |
|---|---|---|---|
| 1 | **Subject/Object integrity** | steering, profiling, managing the user | axioms A13/W4 (verified) |
| 2 | **Epistemic level** | state-transient content claimed as ultimate | AV22 (verified); general over-claim is **heuristic** |
| 4 | **Adhyāsa detection** | user equated with a conditioned attribute | axioms A13/M6/M7 (verified) |
| 3 | **Cognitive independence** | phrasing that induces dependency | *heuristic only — no axiom* |

Checks 1 and 4 ground in machine-verified Scherf axioms. Check 2 is verified only
for the narrow AV22 case (content labeled ultimate yet varying across
consciousness-states); ordinary over-claiming is reported as an unverified
heuristic. Check 3 has no axiom at all. Every finding carries a `verified` flag
and an `extraction_confidence`; read both. See [LIMITS.md](LIMITS.md).

## Actions

| Action | Meaning |
|---|---|
| `PASS` | No finding. Deliver unchanged. |
| `FLAG` | Deliver, annotated (default for advisory findings). |
| `CORRECT` | Deliver **accompanied by** a reframe — never a silent rewrite. |
| `BLOCK` | Withhold; regenerate. Reserved for confident, high-severity manipulation. |

There is deliberately **no silent-rewrite action**: a filter that secretly
alters output for the user's "own good" would itself treat the user as an object
to manage — the very thing check #1 forbids. For the same reason every verdict
carries a `transparency_note`, and `UserContext` is deliberately **profile-free**
(a stored user profile would be the "preference bundle" Viveka exists to detect).

## Architecture

```
LLM prose → [pre-screen] → [Judge: prose → Claim objects]   ← interpretation (NOT verified)
                          ─────────────────────────────────  ← the honesty boundary
                            [Scherf check()/classify()]       ← machine-verified axioms
                            → Verdict (PASS/FLAG/CORRECT/BLOCK) + transparency
```

- **Judge** (`HeuristicJudge` | `LLMJudge`) — pluggable. The heuristic is
  deterministic and offline (it drives the tests and demo); the LLM judge wraps
  any completion callable (`LLMJudge.anthropic(client)` provided).
- **Checker** (`ScherfChecker` | `StubChecker`) — `ScherfChecker` uses the real
  Lean-backed package; the bundled `StubChecker` is a faithful but **unverified**
  stand-in so everything runs with nothing installed (`default_checker()` picks
  the real one if importable).
- **Policy** — maps findings to actions; tunable (`block_confidence_threshold`,
  `require_verified_for_block`, …).

Everything is injectable:

```python
from witness_layer import WitnessFilter, LLMJudge, ScherfChecker, Policy
flt = WitnessFilter(
    judge=LLMJudge.anthropic(client),                 # higher recall
    checker=ScherfChecker(),                           # real, verified
    policy=Policy(require_verified_for_block=True),    # only block on verified findings
)
```

## Installation

```bash
pip install witness-layer            # heuristic + bundled faithful stub backend
pip install "witness-layer[scherf]"  # adds the real, Lean-verified Scherf backend
```

Both packages are on PyPI ([witness-layer](https://pypi.org/project/witness-layer/),
[scherf](https://pypi.org/project/scherf/)). The `[scherf]` extra is strongly
recommended — without it Viveka falls back to a faithful but **unverified** stub.

`WitnessFilter()` auto-detects the backend: if `import scherf` succeeds it uses
`ScherfChecker` (`backend_verified = True`); otherwise it uses the bundled stub
and reports `backend_verified = False` on every verdict. (The test suite also
auto-locates a local checkout via `$SCHERF_PATH`.)

## Develop / test

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest -s     # consensus precision/recall = 1.00
.venv/bin/python demo.py          # PASS / FLAG / CORRECT / BLOCK walkthrough
```

## Status & limits

This is a v0.1 reference implementation. Read [LIMITS.md](LIMITS.md) — it states
plainly what Viveka cannot detect (intent, inner *adhyāsa*, subtle objectification),
why it is tuned for precision over recall, and why it refuses to print a single
blended accuracy number.

## Links

- Scherf Logic API — https://github.com/SpecStudio-net/Scherf_API
- AIM (Advaita Inquiry Matrix) — https://github.com/SpecStudio-net/Advaita-Inquiry-Matrix
- Scherf's Advaita formalization (Lean 4) — https://github.com/matthew-scherf/Advaita
- Design rationale — [viveka-design-doc.md](viveka-design-doc.md)
