"""Precision/recall harness used by the benchmark test and the demo."""

from __future__ import annotations

from dataclasses import dataclass

from witness_layer import Action, WitnessFilter

from .benchmark import Case


@dataclass
class Metrics:
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0

    @property
    def n(self) -> int:
        return self.tp + self.fp + self.tn + self.fn

    @property
    def precision(self) -> float:
        d = self.tp + self.fp
        return self.tp / d if d else 1.0

    @property
    def recall(self) -> float:
        d = self.tp + self.fn
        return self.tp / d if d else 1.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    def report(self, title: str) -> str:
        return (f"{title}: n={self.n}  precision={self.precision:.2f}  "
                f"recall={self.recall:.2f}  f1={self.f1:.2f}  "
                f"(tp={self.tp} fp={self.fp} tn={self.tn} fn={self.fn})")


def score(filt: WitnessFilter, cases: list[Case]) -> Metrics:
    """Binary scoring: positive = 'should be flagged', predicted = action != PASS."""
    m = Metrics()
    for c in cases:
        flagged = filt.evaluate(c.text, c.context).action is not Action.PASS
        if c.should_flag and flagged:
            m.tp += 1
        elif c.should_flag and not flagged:
            m.fn += 1
        elif not c.should_flag and flagged:
            m.fp += 1
        else:
            m.tn += 1
    return m
