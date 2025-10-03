"""Tests for solution extraction helpers."""

from pathlib import Path

import pytest

from llean.utils import parse_level_file


@pytest.mark.parametrize(
    "relative_path",
    [
        "Game/Levels/Algorithm/L02add_algo1.lean",
        "Game/Levels/Implication/L02exact2.lean",
        "Game/Levels/OldFunction/Level_1.lean",
    ],
)
def test_solution_extraction_stops_before_doc_blocks(relative_path: str, env_nng_path: Path) -> None:
    level_path = env_nng_path / relative_path
    metadata = parse_level_file(level_path)
    assert metadata.solution is not None

    solution = metadata.solution.splitlines()
    assert solution  # sanity check

    # Ensure we only captured indented proof lines (allow blank ones).
    for line in solution[1:]:  # first line may be empty
        if not line.strip():
            continue
        assert line.startswith(" ") or line.startswith("\t"), line

    # Make sure known post-proof markers did not leak into the solution.
    forbidden_markers = {"TheoremTab", "Conclusion", "## Summary", "TacticDoc"}
    for marker in forbidden_markers:
        assert all(marker not in line for line in solution)

