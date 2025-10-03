"""List the canonical solutions embedded in each Natural Number Game level."""

from __future__ import annotations

import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Iterator

from llean.utils import LevelMetadata, parse_level_file


def iter_level_files(levels_dir: Path) -> Iterator[tuple[Path, LevelMetadata]]:
    for path in sorted(levels_dir.rglob("*.lean")):
        try:
            metadata = parse_level_file(path)
        except (ValueError, FileNotFoundError):
            continue
        yield path, metadata


def level_sort_key(metadata: LevelMetadata) -> tuple[int, str]:
    if metadata.level is None:
        return (10**6, "")
    try:
        return (int(metadata.level), metadata.level)
    except ValueError:
        return (10**6, metadata.level)


def world_order(nng_path: Path, worlds: Iterable[str]) -> list[str]:
    game_file = nng_path / "Game.lean"
    result: list[str] = []
    if game_file.is_file():
        pattern = re.compile(r"^\s*import\s+Game\.Levels\.([A-Za-z0-9_]+)")
        for line in game_file.read_text(encoding="utf-8").splitlines():
            match = pattern.match(line)
            if match:
                result.append(match.group(1))

    existing = set(worlds)
    ordered = [world for world in result if world in existing]
    ordered.extend(sorted(existing - set(ordered), key=str.casefold))
    return ordered


def main() -> None:
    nng_path = Path(os.environ["NNG_PATH"]).expanduser().resolve()
    levels_dir = nng_path / "Game" / "Levels"

    by_world: dict[str, list[tuple[Path, LevelMetadata]]] = defaultdict(list)
    for path, metadata in iter_level_files(levels_dir):
        world = metadata.world or "Unknown"
        by_world[world].append((path, metadata))

    ordered_worlds = world_order(nng_path, by_world.keys())

    for world in ordered_worlds:
        print(f"World: {world}")
        entries = sorted(by_world[world], key=lambda item: level_sort_key(item[1]))
        for path, metadata in entries:
            rel_path = path.relative_to(nng_path)
            level_label = metadata.level or "?"
            print(f"  Level {level_label} ({rel_path})")
            solution = metadata.solution
            if not solution:
                print("    Solution: <missing>")
                continue
            print("    Solution:")
            for line in solution.splitlines() or [""]:
                print(f"      {line}")
        print()


if __name__ == "__main__":
    main()
