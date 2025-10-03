"""Summarise the Lean tactics exercised by canonical Natural Number Game proofs."""

from __future__ import annotations

import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from llean.tactic_models import TACTIC_REGISTRY, TacticParseError, parse_tactic
from llean.utils import parse_level_file


def _toggle_hint_state(current: bool, line: str) -> bool:
    escaped = False
    state = current
    for char in line:
        if char == "\\" and not escaped:
            escaped = True
            continue
        if char == '"' and not escaped:
            state = not state
        else:
            escaped = False
    return state


def iter_level_files(levels_dir: Path) -> Iterable[Path]:
    for path in sorted(levels_dir.rglob("*.lean")):
        yield path


def extract_commands(solution: str) -> list[str]:
    commands: list[str] = []
    in_hint = False
    pending_hint = False
    for raw_line in solution.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        normalized = stripped.lstrip("· ")
        if not normalized:
            continue
        if normalized.startswith("Hint"):
            in_hint = _toggle_hint_state(in_hint, raw_line)
            if '"' not in raw_line:
                pending_hint = True
            continue
        if pending_hint:
            in_hint = _toggle_hint_state(in_hint, raw_line)
            pending_hint = False
            continue
        if in_hint:
            in_hint = _toggle_hint_state(in_hint, raw_line)
            continue
        if normalized.startswith("--"):
            continue
        first = normalized[0]
        if not first.isalpha() or not first.islower():
            continue
        commands.append(normalized)
    return commands


def main() -> None:
    nng_path = Path(os.environ["NNG_PATH"]).expanduser().resolve()
    levels_dir = nng_path / "Game" / "Levels"

    totals = Counter()
    unique_commands: dict[str, set[str]] = defaultdict(set)
    parsed_counts = Counter()
    parse_errors: dict[str, set[str]] = defaultdict(set)

    for path in iter_level_files(levels_dir):
        try:
            metadata = parse_level_file(path)
        except Exception:
            continue
        if not metadata.solution:
            continue
        for command in extract_commands(metadata.solution):
            keyword = command.split(maxsplit=1)[0]
            totals[keyword] += 1
            unique_commands[keyword].add(command)
            if keyword in TACTIC_REGISTRY:
                try:
                    parse_tactic(command)
                except TacticParseError:
                    parse_errors[keyword].add(command)
                else:
                    parsed_counts[keyword] += 1

    total_commands = sum(totals.values())
    print(f"Processed {total_commands} tactic commands across all solutions.\n")

    header = f"{'keyword':>12} | {'count':>6} | {'unique':>6} | {'parsed':>6}"
    print(header)
    print("-" * len(header))

    for keyword, count in sorted(totals.items(), key=lambda item: (-item[1], item[0])):
        unique = len(unique_commands[keyword])
        parsed = parsed_counts.get(keyword, 0)
        print(f"{keyword:>12} | {count:6} | {unique:6} | {parsed:6}")

    if parse_errors:
        print("\nCommands that failed to parse:")
        for keyword, commands in sorted(parse_errors.items()):
            print(f"- {keyword}: {len(commands)} unparsed")
            for command in sorted(commands):
                print(f"    {command}")


if __name__ == "__main__":
    main()
