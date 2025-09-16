"""Report the tactics introduced in each Natural Number Game level."""

import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from llean.utils import LevelMetadata, parse_level_file


def iter_level_files(base_dir: Path) -> Iterable[tuple[Path, LevelMetadata]]:
    for path in sorted(base_dir.rglob("*.lean")):
        try:
            metadata = parse_level_file(path)
        except (ValueError, FileNotFoundError):
            continue  # Skip non-level helpers (e.g., world aggregators)
        yield path, metadata


def level_sort_key(metadata: LevelMetadata) -> tuple[int, str]:
    if metadata.level is None:
        return (10**6, "")
    try:
        return (int(metadata.level), metadata.level)
    except ValueError:
        return (10**6, metadata.level)


def accumulate_unique(existing: list[str], candidates: Iterable[str]) -> list[str]:
    for tactic in candidates:
        if tactic not in existing:
            existing.append(tactic)
    return existing


def main() -> None:
    nng_path = Path(os.environ["NNG_PATH"]).expanduser().resolve()
    levels_dir = nng_path / "Game" / "Levels"
    game_file = nng_path / "Game.lean"

    by_world: dict[str, list[tuple[Path, LevelMetadata]]] = defaultdict(list)
    for path, metadata in iter_level_files(levels_dir):
        world = metadata.world or "Unknown"
        by_world[world].append((path, metadata))

    world_order: list[str] = []
    if game_file.is_file():
        import_pattern = re.compile(r"^\s*import\s+Game\.Levels\.([A-Za-z0-9_]+)")
        for line in game_file.read_text(encoding="utf-8").splitlines():
            match = import_pattern.match(line)
            if match:
                world_order.append(match.group(1))

    remaining_worlds = set(by_world)

    global_available: list[str] = []
    global_hidden: list[str] = []

    ordered_worlds = [w for w in world_order if w in by_world]
    ordered_worlds.extend(sorted(remaining_worlds - set(world_order), key=str.casefold))

    for world in ordered_worlds:
        print(f"World: {world}")
        available: list[str] = global_available.copy()
        hidden_available: list[str] = global_hidden.copy()

        for path, metadata in sorted(by_world[world], key=lambda item: level_sort_key(item[1])):
            rel_path = path.relative_to(nng_path)
            level_label = metadata.level or "?"
            new_tactics = metadata.new_tactics or []
            hidden_tactics = metadata.hidden_tactics or []
            if new_tactics:
                accumulate_unique(available, new_tactics)
            if hidden_tactics:
                accumulate_unique(hidden_available, hidden_tactics)

            print(f"  Level {level_label} ({rel_path})")
            print(f"    New tactics: {', '.join(new_tactics) if new_tactics else '-'}")
            print(f"    Hidden tactics: {', '.join(hidden_tactics) if hidden_tactics else '-'}")
            print(
                f"    Available now: {', '.join(available) if available else '-'}"
            )
            if hidden_available:
                print(
                    f"    Hidden available: {', '.join(hidden_available)}"
                )
        print()

        global_available = available
        global_hidden = hidden_available


if __name__ == "__main__":
    main()
