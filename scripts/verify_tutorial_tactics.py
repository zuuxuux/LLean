"""Verify tactic model coverage against Tutorial world reference solutions."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from lean_interact import Command, LeanServer
from lean_interact.interface import LeanError

from llean.tactic_models import TacticModel, TacticParseError
from llean.utils import get_nng_config, parse_level_file


@dataclass
class LevelResult:
    path: Path
    commands: list[str]
    unsupported: list[str]
    prefix_failures: list[tuple[int, str]]
    final_ok: bool


def toggle_hint_state(active: bool, line: str) -> bool:
    escaped = False
    state = active
    for char in line:
        if char == "\\" and not escaped:
            escaped = True
            continue
        if char == '"' and not escaped:
            state = not state
        else:
            escaped = False
    return state


def extract_solution_commands(solution: str) -> list[str]:
    commands: list[str] = []
    in_hint = False
    pending_hint = False
    for raw_line in solution.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        clean = stripped.lstrip("· ")
        if not clean:
            continue
        if clean.startswith("Hint"):
            in_hint = toggle_hint_state(in_hint, raw_line)
            if '"' not in raw_line:
                pending_hint = True
            continue
        if pending_hint:
            in_hint = toggle_hint_state(in_hint, raw_line)
            pending_hint = False
            continue
        if in_hint:
            in_hint = toggle_hint_state(in_hint, raw_line)
            continue
        if clean.startswith("--"):
            continue
        commands.append(clean)
    return commands


def verify_snippet(level_path: Path, commands: Sequence[str], allow_sorry: bool) -> tuple[bool, str | None]:
    metadata = parse_level_file(level_path)
    code_lines: list[str] = [f"import {metadata.module}", ""]
    if metadata.namespace:
        code_lines.extend([f"open {metadata.namespace}", ""])
    code_lines.extend([f"theorem ex {metadata.signature} := by"])
    body_lines = [f"    {cmd}" for cmd in commands]
    if allow_sorry:
        body_lines.append("    sorry")
    snippet = "\n".join(code_lines + body_lines)

    server = LeanServer(get_nng_config(verbose=False))
    try:
        response = server.run(Command(cmd=snippet))
    except LeanError as exc:
        return False, str(exc)

    errors = [msg.data for msg in getattr(response, "messages", []) if msg.severity == "error"]
    if errors:
        combined = "; ".join(errors)
        if allow_sorry and "no goals to be solved" in combined:
            return True, None
        return False, combined

    if not allow_sorry:
        sorries = getattr(response, "sorries", [])
        if sorries:
            goal = getattr(sorries[0], "goal", "goal remained")
            return False, f"unresolved goal: {goal}"

    return True, None


def round_trip_command(command: str) -> tuple[str, bool]:
    try:
        model = TacticModel.from_string(command)
    except TacticParseError:
        return command, False
    return model.to_string(), True


def iter_tutorial_levels(nng_path: Path) -> Iterable[Path]:
    tutorial_dir = nng_path / "Game" / "Levels" / "Tutorial"
    for path in sorted(tutorial_dir.glob("L*.lean")):
        if path.is_file():
            yield path.resolve()


def evaluate_level(level_path: Path) -> LevelResult:
    metadata = parse_level_file(level_path)
    if not metadata.solution:
        raise RuntimeError(f"No solution data for {level_path}")

    original_commands = extract_solution_commands(metadata.solution)
    processed: list[str] = []
    unsupported: list[str] = []
    for command in original_commands:
        round_trip, supported = round_trip_command(command)
        processed.append(round_trip)
        if not supported:
            unsupported.append(command)

    prefix_failures: list[tuple[int, str]] = []
    for idx in range(1, len(processed) + 1):
        ok, error = verify_snippet(level_path, processed[:idx], allow_sorry=True)
        if not ok:
            prefix_failures.append((idx, error or "unknown error"))
            break

    final_ok, final_error = verify_snippet(level_path, processed, allow_sorry=False)
    if not final_ok:
        prefix_failures.append((len(processed), final_error or "final proof incomplete"))

    return LevelResult(
        path=level_path,
        commands=processed,
        unsupported=unsupported,
        prefix_failures=prefix_failures,
        final_ok=final_ok,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--nng-path",
        help="Override NNG_PATH for locating the Natural Number Game repository",
    )
    args = parser.parse_args()

    if args.nng_path:
        nng_path = Path(args.nng_path).expanduser().resolve()
    else:
        nng_path = (Path.cwd() / "NNG4").resolve()
        if not nng_path.exists():
            raise FileNotFoundError("Unable to locate NNG4 directory; specify --nng-path")

    os.environ.setdefault("NNG_PATH", str(nng_path))

    results: list[LevelResult] = []
    for level_path in iter_tutorial_levels(nng_path):
        results.append(evaluate_level(level_path))

    summary = {
        "levels": [
            {
                "path": str(result.path),
                "command_count": len(result.commands),
                "unsupported": result.unsupported,
                "prefix_failures": result.prefix_failures,
                "final_ok": result.final_ok,
            }
            for result in results
        ]
    }

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
