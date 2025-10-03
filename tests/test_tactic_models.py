"""Tests for structured tactic representations."""

import pytest

from llean.tactic_models import (
    ApplyTactic,
    NthRewriteTactic,
    RflTactic,
    RewriteTactic,
    TacticModel,
    TacticParseError,
    parse_tactic,
)


@pytest.mark.parametrize(
    ("command", "expected_type"),
    [
        ("rw [two_eq_succ_one]", RewriteTactic),
        ("rw [← add_assoc, add_comm] at h", RewriteTactic),
        ("apply mul_left_ne_zero at h", ApplyTactic),
        ("apply f", ApplyTactic),
        ("nth_rewrite 2 [two_eq_succ_one]", NthRewriteTactic),
        ("nth_rewrite 2 [← zero_add y] at h", NthRewriteTactic),
        ("rfl", RflTactic),
    ],
)
def test_model_round_trip(command: str, expected_type) -> None:
    model = TacticModel.from_string(command)
    assert isinstance(model, expected_type)
    assert model.to_string() == command


def test_parse_tactic_round_trip(tactic_samples: dict[str, list[str]]) -> None:
    for commands in tactic_samples.values():
        for command in commands:
            model = parse_tactic(command)
            assert model.to_string() == command


def test_base_model_round_trip(tactic_samples: dict[str, list[str]]) -> None:
    for commands in tactic_samples.values():
        for command in commands:
            model = TacticModel.from_string(command)
            assert model.to_string() == command


def test_parse_tactic_unknown_keyword() -> None:
    with pytest.raises(TacticParseError):
        parse_tactic("foo bar")
