"""Utilities for tactic generation and exhaustive search."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from lean_interact import ProofStep
from lean_interact.interface import LeanError

from .levels import load_level_from_file

def _parse_goal(goal: str) -> tuple[list[str], list[str]]:
    """Return equality hypotheses and possible induction targets."""

    eqs: list[str] = []
    induct: list[str] = []

    for raw_line in goal.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("case"):
            continue
        if line.startswith("⊢"):
            break
        if ":" not in line:
            continue
        name, type_str = line.split(":", 1)
        raw_names = [part for part in name.replace(",", " ").split() if part]
        type_str = type_str.strip()
        if not raw_names:
            continue
        if "=" in type_str:
            eqs.extend(raw_names)
            continue
        if any(token in type_str for token in ["→", "∀", "∃", "↔", "≠", "≤", "≥", "⊢", ":="]):
            continue
        induct.extend(raw_names)

    return eqs, induct


def generate_tactic_candidates(goal: str, available_tactics: Iterable[str]) -> list[str]:
    """Construct tactic invocations for the given goal and available tactics."""

    available = set(available_tactics)
    eqs, induct_targets = _parse_goal(goal)

    candidates: list[str] = []
    if "rfl" in available:
        candidates.append("rfl")

    if "rw" in available:
        for name in eqs:
            candidates.append(f"rw [{name}]")
            candidates.append(f"rw [← {name}]")

    if "nth_rewrite" in available:
        for position in range(1, 4):
            for name in eqs:
                candidates.append(f"nth_rewrite {position} [{name}]")
                candidates.append(f"nth_rewrite {position} [← {name}]")

    if "induction" in available:
        for name in induct_targets:
            candidates.append(f"induction {name}")

    return candidates


def depth_first_search(level_path: Path, *, max_depth: int = 6) -> list[list[str]]:
    """Perform a depth-first search exploring tactic sequences up to ``max_depth``."""

    level_path = level_path.resolve()
    context = load_level_from_file(level_path, verbose=False)
    available = [tactic.name for tactic in context.tactics]

    try:
        root = context.server.run(ProofStep(tactic="skip", proofState=0))
        if isinstance(root, LeanError) or root.has_errors():
            return []

        root_state = str(root.proof_state)
        state_goals: dict[str, list[str]] = {root_state: root.goals or []}

        solutions: list[list[str]] = []
        stack: list[tuple[str, list[str]]] = [(root_state, [])]
        best_depth: dict[str, int] = {}
        explored_edges: set[tuple[str, str]] = set()

        while stack:
            state_id, sequence = stack.pop()
            if len(sequence) > max_depth:
                continue

            goals = state_goals.get(state_id, [])
            if not goals:
                solutions.append(sequence)
                continue

            goal_str = goals[0]
            if goal_str in best_depth and best_depth[goal_str] <= len(sequence):
                continue
            best_depth[goal_str] = len(sequence)

            candidates = generate_tactic_candidates(goal_str, available)
            for tactic in reversed(candidates):
                edge_key = (state_id, tactic)
                if edge_key in explored_edges:
                    continue
                explored_edges.add(edge_key)

                response = context.server.run(ProofStep(tactic=tactic, proofState=state_id))
                if isinstance(response, LeanError) or response.has_errors():
                    continue

                new_state = str(response.proof_state)
                state_goals[new_state] = response.goals or []
                stack.append((new_state, sequence + [tactic]))

        return solutions
    finally:
        context.server.kill()


__all__ = [
    "generate_tactic_candidates",
    "depth_first_search",
]
