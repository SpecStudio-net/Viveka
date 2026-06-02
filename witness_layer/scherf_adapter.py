"""The bridge to the Scherf API — the only module that touches ``scherf``.

This is the line below which everything is machine-verified and above which
everything is interpretation. A :class:`Checker` takes the *unverified* findings
the extraction layer produced, translates each into a Scherf ``Claim``, and runs
Scherf's ``Interaction().check()``. Findings Scherf does not confirm are dropped
— that is the formal layer correcting the heuristic's false positives.

``ScherfChecker`` uses the real, Lean-backed package (``verified=True``).
``StubChecker`` uses the bundled faithful stub (``verified=False``) so the
library runs with nothing installed. ``default_checker()`` picks the real one if
importable, else the stub, and says which.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .findings import Finding, WitnessViolation
from .sorts import CheckKind, FORMAL_CHECKS, Level, Severity, State

_SEVERITY = {
    CheckKind.SUBJECT_OBJECT: Severity.HIGH,
    CheckKind.ADHYASA: Severity.HIGH,
    CheckKind.EPISTEMIC_LEVEL: Severity.MEDIUM,
}


@runtime_checkable
class Checker(Protocol):
    """Anything that can turn findings into confirmed violations."""

    verified: bool
    backend_name: str

    def verify(self, findings: list[Finding], handle: str) -> list[WitnessViolation]:
        ...


class _ScherfBackedChecker:
    """Shared logic over any module exposing the Scherf contract."""

    def __init__(self, scherf_module, *, verified: bool, backend_name: str) -> None:
        self._s = scherf_module
        self.verified = verified
        self.backend_name = backend_name

    # -- translation: Viveka enums -> Scherf enums --------------------------
    def _level(self, level: Level | None):
        if level is None:
            return None
        return {
            Level.PARAM: self._s.Level.PARAM,
            Level.VYAV: self._s.Level.VYAV,
            Level.PRAT: self._s.Level.PRAT,
        }[level]

    def _states(self, states: set[State]):
        m = {
            State.JAGRAT: self._s.State.JAGRAT,
            State.SVAPNA: self._s.State.SVAPNA,
            State.SUSUPTI: self._s.State.SUSUPTI,
        }
        return {m[s] for s in states}

    def _to_claim(self, f: Finding, handle: str):
        S = self._s
        text = f.claim_text or f.text
        if f.kind is CheckKind.ADHYASA:
            level = self._level(f.level) or S.Level.VYAV
            return S.Claim.about(handle).says(text).at(level)
        if f.kind is CheckKind.SUBJECT_OBJECT:
            return S.Claim.system_stance(text)
        if f.kind is CheckKind.EPISTEMIC_LEVEL:
            b = S.Claim.output(text)
            if f.present_in:
                b = b.manifests_in(*self._states(f.present_in))
            if f.absent_in:
                b = b.absent_from(*self._states(f.absent_in))
            level = self._level(f.level)
            return b.at(level) if level is not None else b.build()
        raise ValueError(f"{f.kind} is not a formal check")

    def verify(self, findings: list[Finding], handle: str) -> list[WitnessViolation]:
        out: list[WitnessViolation] = []
        for f in findings:
            if f.kind not in FORMAL_CHECKS:
                continue  # heuristic-only checks never reach Scherf
            claim = self._to_claim(f, handle)
            result = self._s.Interaction().assert_claim(claim).check()
            for v in result.violations:
                out.append(WitnessViolation(
                    check=f.kind,
                    severity=_SEVERITY[f.kind],
                    verified=self.verified,
                    extraction_confidence=f.confidence,
                    source_text=f.text,
                    axiom_id=getattr(v, "axiom_id", ""),
                    term=getattr(v, "term", ""),
                    explanation=getattr(v, "explanation", ""),
                    reframe=getattr(v, "reframe", ""),
                    borders_limit=getattr(v, "borders_limit", ""),
                ))
        return out


class ScherfChecker(_ScherfBackedChecker):
    """Uses the real, machine-verified ``scherf`` package."""

    def __init__(self) -> None:
        try:
            import scherf  # type: ignore
        except ImportError as e:  # pragma: no cover - environment dependent
            raise ImportError(
                "The real 'scherf' package is not installed. Either install it\n"
                "  pip install git+https://github.com/SpecStudio-net/Scherf_API\n"
                "or use StubChecker() / default_checker() to run against the "
                "bundled (UNVERIFIED) faithful stub."
            ) from e
        # The engine API may live at top level or in scherf.engine depending on
        # the installed version; bind defensively.
        if not hasattr(scherf, "Claim"):
            from scherf import engine as _engine  # type: ignore
            for name in ("Claim", "Interaction", "classify"):
                setattr(scherf, name, getattr(_engine, name))
        super().__init__(scherf, verified=True, backend_name="scherf (Lean-verified)")


class StubChecker(_ScherfBackedChecker):
    """Uses the bundled faithful stub. Verdicts are NOT machine-verified."""

    def __init__(self) -> None:
        from . import _scherf_stub as stub
        super().__init__(stub, verified=False,
                         backend_name="STUB (NOT verified — install scherf for real checks)")


def default_checker() -> Checker:
    """Real ``scherf`` if importable, else the faithful stub."""
    try:
        return ScherfChecker()
    except ImportError:
        return StubChecker()
