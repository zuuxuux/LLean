"""Utilities for tactic generation and exhaustive search."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List

from lean_interact import ProofStep
from lean_interact.interface import LeanError

from .levels import load_level_from_file


@dataclass
class SearchNode:
    state_id: str
    goals: List[str]
    depth: int
    tactics_tried: list[str] = field(default_factory=list)
    successes: list[tuple[str, str]] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


@dataclass
class SearchGraph:
    nodes: dict[str, SearchNode] = field(default_factory=dict)
    solutions: list[list[str]] = field(default_factory=list)
    root: str | None = None

    def record_node(self, state_id: str, goals: Iterable[str], depth: int) -> SearchNode:
        goals_list = list(goals)
        node = self.nodes.get(state_id)
        if node is None:
            node = SearchNode(state_id=state_id, goals=goals_list, depth=depth)
            self.nodes[state_id] = node
            if depth == 0 and self.root is None:
                self.root = state_id
        else:
            node.goals = goals_list
            node.depth = min(node.depth, depth)
        return node

    def record_attempt(
        self,
        state_id: str,
        tactic: str,
        *,
        success: bool,
        new_state: str | None = None,
    ) -> None:
        node = self.nodes.setdefault(state_id, SearchNode(state_id=state_id, goals=[], depth=0))
        node.tactics_tried.append(tactic)
        if success and new_state is not None:
            node.successes.append((tactic, new_state))
        elif not success:
            node.failures.append(tactic)

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


def generate_tactic_candidates(
    goal: str, available_tactics: Iterable[str], lemmas: Iterable[str]
) -> list[str]:
    """Construct tactic invocations for the given goal and available tactics."""

    available = set(available_tactics)
    eqs, induct_targets = _parse_goal(goal)
    lemma_list = [lemma for lemma in lemmas if lemma]

    rewrite_names: list[str] = []
    for name in eqs + lemma_list:
        if name not in rewrite_names:
            rewrite_names.append(name)

    candidates: list[str] = []
    if "rfl" in available:
        candidates.append("rfl")

    if "rw" in available:
        for name in rewrite_names:
            candidates.append(f"rw [{name}]")
            candidates.append(f"rw [← {name}]")

    if "nth_rewrite" in available:
        for position in range(1, 4):
            for name in rewrite_names:
                candidates.append(f"nth_rewrite {position} [{name}]")
                candidates.append(f"nth_rewrite {position} [← {name}]")

    if "induction" in available:
        for name in induct_targets:
            candidates.append(f"induction {name}")

    return candidates


def depth_first_search(
    level_path: Path,
    *,
    max_depth: int = 6,
    trace: SearchGraph | None = None,
) -> list[list[str]]:
    """Perform a depth-first search exploring tactic sequences up to ``max_depth``."""

    level_path = level_path.resolve()
    context = load_level_from_file(level_path, verbose=False)
    available = [tactic.name for tactic in context.tactics]
    rewrite_lemmas = context.lemmas

    try:
        root = context.server.run(ProofStep(tactic="skip", proofState=0))
        if isinstance(root, LeanError) or root.has_errors():
            return []

        root_state = str(root.proof_state)
        state_goals: dict[str, list[str]] = {root_state: root.goals or []}
        if trace is not None:
            trace.record_node(root_state, state_goals[root_state], 0)

        solutions: list[list[str]] = []
        stack: list[tuple[str, list[str]]] = [(root_state, [])]
        state_depth: dict[str, int] = {root_state: 0}
        explored_edges: set[tuple[str, str]] = set()

        while stack:
            state_id, sequence = stack.pop()
            if len(sequence) > max_depth:
                continue

            goals = state_goals.get(state_id, [])
            if not goals:
                solutions.append(sequence)
                if trace is not None:
                    trace.solutions.append(sequence)
                return solutions

            goal_str = goals[0]

            recorded_depth = state_depth.get(state_id)
            if recorded_depth is not None and recorded_depth < len(sequence):
                continue
            if recorded_depth is None or recorded_depth > len(sequence):
                state_depth[state_id] = len(sequence)

            candidates = generate_tactic_candidates(goal_str, available, rewrite_lemmas)
            children: list[tuple[str, list[str]]] = []
            for tactic in candidates:
                edge_key = (state_id, tactic)
                if edge_key in explored_edges:
                    continue
                explored_edges.add(edge_key)

                response = context.server.run(ProofStep(tactic=tactic, proofState=state_id))
                if isinstance(response, LeanError) or response.has_errors():
                    if trace is not None:
                        trace.record_attempt(state_id, tactic, success=False)
                    continue

                new_state = str(response.proof_state)
                state_goals[new_state] = response.goals or []
                if trace is not None:
                    trace.record_attempt(state_id, tactic, success=True, new_state=new_state)
                    trace.record_node(new_state, state_goals[new_state], len(sequence) + 1)
                new_depth = len(sequence) + 1
                recorded_child = state_depth.get(new_state)
                if recorded_child is not None and recorded_child <= new_depth:
                    continue
                state_depth[new_state] = new_depth
                children.append((new_state, sequence + [tactic]))

            for child in reversed(children):
                stack.append(child)

        return solutions
    finally:
        context.server.kill()


__all__ = [
    "generate_tactic_candidates",
    "depth_first_search",
    "SearchGraph",
    "SearchNode",
]
