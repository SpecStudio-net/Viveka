"""Shared fixtures. Tests pin the StubChecker so results are deterministic
regardless of whether the real ``scherf`` package happens to be installed."""

from __future__ import annotations

import pytest

from witness_layer import HeuristicJudge, Policy, StubChecker, WitnessFilter


@pytest.fixture
def filt() -> WitnessFilter:
    return WitnessFilter(judge=HeuristicJudge(), checker=StubChecker(), policy=Policy())
