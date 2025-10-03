"""Shared pytest fixtures for repository tests."""

import os
from pathlib import Path
from typing import Dict, List

import pytest


@pytest.fixture
def env_nng_path() -> Path:
    """Resolve the Natural Number Game root or skip if unavailable."""

    root = os.environ.get("NNG_PATH")
    if not root:
        pytest.skip(
            "NNG_PATH not configured; integration tests require the Natural Number Game repository"
        )
    path = Path(root).expanduser().resolve()
    if not path.exists():
        pytest.skip(f"NNG_PATH path '{path}' does not exist")
    return path


@pytest.fixture
def tactic_samples() -> Dict[str, List[str]]:
    """Provide representative tactic invocations for round-trip tests."""

    return {
        "rw": [
            "rw [two_eq_succ_one]",
            "rw [← add_assoc, add_comm] at h",
            "rw [mul_add, add_mul, add_mul]",
        ],
        "apply": [
            "apply succ_inj at h",
            "apply mul_left_ne_zero at h",
            "apply f",
        ],
        "nth_rewrite": [
            "nth_rewrite 2 [two_eq_succ_one]",
            "nth_rewrite 2 [← zero_add y] at h",
        ],
    }
