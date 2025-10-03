"""High-level helpers for loading Natural Number Game levels."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from lean_interact import LeanServer

from .utils import (
    LevelMetadata,
    get_problem_server_from_file,
    parse_level_file,
)


@dataclass(slots=True)
class Tactic:
    name: str
    usage: str


@dataclass(slots=True)
class LevelContext:
    server: LeanServer
    tactics: List[Tactic]
    lemmas: List[str]
    solutions: List[str]


def _accumulate_unique(existing: list[str], candidates: Iterable[str]) -> list[str]:
    for tactic in candidates:
        if tactic not in existing:
            existing.append(tactic)
    return existing


def _level_sort_key(metadata: LevelMetadata) -> tuple[int, str]:
    if metadata.level is None:
        return (10**6, "")
    try:
        return (int(metadata.level), metadata.level)
    except ValueError:
        return (10**6, metadata.level)


def _world_order(nng_path: Path, existing_worlds: Iterable[str]) -> list[str]:
    game_file = nng_path / "Game.lean"
    ordered: list[str] = []
    if game_file.is_file():
        pattern = re.compile(r"^\s*import\s+Game\.Levels\.([A-Za-z0-9_]+)")
        for line in game_file.read_text(encoding="utf-8").splitlines():
            match = pattern.match(line)
            if match:
                ordered.append(match.group(1))

    existing_set = set(existing_worlds)
    seen = set()
    result: list[str] = []
    for world in ordered:
        if world in existing_set and world not in seen:
            result.append(world)
            seen.add(world)

    remaining = sorted(existing_set - seen, key=str.casefold)
    result.extend(remaining)
    return result


def _collect_level_metadata(nng_path: Path) -> dict[Path, LevelMetadata]:
    levels_dir = nng_path / "Game" / "Levels"
    metadata_map: dict[Path, LevelMetadata] = {}
    for path in sorted(levels_dir.rglob("*.lean")):
        try:
            metadata = parse_level_file(path)
        except (ValueError, FileNotFoundError):
            continue
        metadata_map[path.resolve()] = metadata
    return metadata_map


def load_level_from_file(level_path: str | os.PathLike[str], *, verbose: bool = False) -> LevelContext:
    """Load a Natural Number Game level and report available tactics."""

    target_path = Path(level_path).expanduser().resolve()
    metadata = parse_level_file(target_path)

    nng_path = Path(os.environ["NNG_PATH"]).expanduser().resolve()
    metadata_map = _collect_level_metadata(nng_path)

    if target_path not in metadata_map:
        # Include the parsed metadata if `parse_level_file` accepted it but wasn't in the map.
        metadata_map[target_path] = metadata

    worlds: dict[str, list[tuple[Path, LevelMetadata]]] = {}
    for path, meta in metadata_map.items():
        world = meta.world or "Unknown"
        worlds.setdefault(world, []).append((path, meta))

    order = _world_order(nng_path, worlds.keys())

    available: list[str] = []
    hidden: list[str] = []
    lemmas: list[str] = []
    solutions: list[str] = []
    docs: dict[str, str] = {}
    target_metadata: LevelMetadata | None = None

    found = False
    for world in order:
        levels = sorted(worlds[world], key=lambda item: _level_sort_key(item[1]))
        for path, meta in levels:
            if meta.tactic_docs:
                for name, doc in meta.tactic_docs.items():
                    docs.setdefault(name, doc)
            if meta.new_tactics:
                _accumulate_unique(available, meta.new_tactics)
            if meta.hidden_tactics:
                _accumulate_unique(hidden, meta.hidden_tactics)
            if meta.new_theorems:
                for name in meta.new_theorems:
                    _accumulate_unique(lemmas, [name])
                    if "." in name:
                        short = name.split(".")[-1]
                        if short:
                            _accumulate_unique(lemmas, [short])
            if meta.solution:
                solutions.append(meta.solution)
            if path == target_path:
                target_metadata = meta
                found = True
                break
        if found:
            break

    if not found:
        raise ValueError(f"Level file '{target_path}' was not found in the detected worlds")

    combined: list[str] = []
    for name in available:
        if name not in combined:
            combined.append(name)
    for name in hidden:
        if name not in combined:
            combined.append(name)

    tactics: list[Tactic] = []
    for name in combined:
        usage = docs.get(name, "Documentation not found")
        tactics.append(Tactic(name=name, usage=usage))

    server = get_problem_server_from_file(target_path, verbose=verbose)
    return LevelContext(server=server, tactics=tactics, lemmas=lemmas, solutions=solutions)


__all__ = ["Tactic", "LevelContext", "load_level_from_file"]
