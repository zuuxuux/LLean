import os
import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from functools import singledispatch
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from lean_interact import Command, LeanREPLConfig, LeanServer, LocalProject
from lean_interact.interface import CommandResponse, LeanError, ProofStepResponse

if not load_dotenv():
    print("No .env file found")
if "NNG_PATH" not in os.environ:
    raise EnvironmentError("NNG_PATH not set in environment variables")


@contextmanager
def _suppress_output(enabled: bool):
    if not enabled:
        yield
        return

    sys.stdout.flush()
    sys.stderr.flush()
    with open(os.devnull, "w") as devnull:
        stdout_fd = os.dup(1)
        stderr_fd = os.dup(2)
        try:
            os.dup2(devnull.fileno(), 1)
            os.dup2(devnull.fileno(), 2)
            yield
        finally:
            os.dup2(stdout_fd, 1)
            os.dup2(stderr_fd, 2)
            os.close(stdout_fd)
            os.close(stderr_fd)


def _summarize_docstring(doc: str) -> str:
    """Extract a short usage string from a Lean doc comment."""

    doc = doc.strip()
    if not doc:
        return ""

    lines = [line.strip() for line in doc.splitlines()]

    summary_lines: list[str] = []
    collecting = False
    for line in lines:
        if line.lower().startswith("## summary"):
            collecting = True
            continue
        if collecting and line.startswith("## "):
            break
        if collecting:
            summary_lines.append(line)

    summary = " ".join(filter(None, (line.strip() for line in summary_lines)))
    if summary:
        return summary

    paragraphs = doc.split("\n\n")
    for paragraph in paragraphs:
        text = " ".join(paragraph.split())
        if text:
            return text

    return " ".join(lines)


@dataclass
class LevelMetadata:
    """Metadata extracted from a Natural Number Game level file."""

    module: str
    namespace: str | None
    signature: str
    statement_name: str | None = None
    new_tactics: list[str] | None = None
    hidden_tactics: list[str] | None = None
    world: str | None = None
    level: str | None = None
    tactic_docs: dict[str, str] | None = None
    new_theorems: list[str] | None = None


def parse_level_file(level_path: str | os.PathLike[str]) -> LevelMetadata:
    """Parse a Natural Number Game level file and extract metadata needed to load it."""

    nng_path = Path(os.environ["NNG_PATH"]).expanduser().resolve()
    path = Path(level_path).expanduser().resolve()

    if not path.is_file():
        raise FileNotFoundError(f"Level file '{path}' does not exist")

    try:
        relative = path.relative_to(nng_path)
    except ValueError as exc:
        raise ValueError(
            f"Level file '{path}' is not inside the Natural Number Game directory '{nng_path}'"
        ) from exc

    module = ".".join(relative.with_suffix("").parts)
    contents = path.read_text(encoding="utf-8")

    namespace_match = re.search(r"^\s*namespace\s+([A-Za-z0-9_'.]+)", contents, re.MULTILINE)
    namespace = namespace_match.group(1) if namespace_match else None

    world_match = re.search(r'^\s*World\s+"([^"]+)"', contents, re.MULTILINE)
    world = world_match.group(1) if world_match else None
    level_match = re.search(r"^\s*Level\s+([^\n]+)", contents, re.MULTILINE)
    level = level_match.group(1).strip() if level_match else None

    statement_match = re.search(r"^\s*Statement\b", contents, re.MULTILINE)
    if not statement_match:
        raise ValueError(f"Level file '{path}' does not contain a Statement block")

    after_statement = contents[statement_match.end() :]
    try:
        signature_block, _ = after_statement.split(":=", 1)
    except ValueError as exc:
        raise ValueError(f"Unable to find ':=' after Statement in '{path}'") from exc

    trimmed = signature_block.strip()
    if not trimmed:
        raise ValueError(f"Empty Statement signature in '{path}'")

    statement_name = None
    name_match = re.match(r"([A-Za-z0-9_']+)\s+(.*)", trimmed, re.DOTALL)
    if name_match and not trimmed.startswith(("(", "{")):
        statement_name = name_match.group(1)
        signature_body = name_match.group(2)
    else:
        signature_body = trimmed

    signature = " ".join(signature_body.split())

    def _extract_tactics(directive: str) -> list[str]:
        pattern = rf"^\s*{directive}[^\S\n]*([^\n]*)"
        tactics: list[str] = []
        for match in re.finditer(pattern, contents, re.MULTILINE):
            remainder = match.group(1)
            if remainder is None:
                continue
            cleaned = remainder.split("--", 1)[0].strip()
            if not cleaned:
                continue
            tactics.extend(cleaned.split())
        return tactics

    new_tactics = _extract_tactics("NewTactic")
    hidden_tactics = _extract_tactics("NewHiddenTactic")

    tactic_docs: dict[str, str] = {}
    for match in re.finditer(
        r"/--(?P<doc>.*?)-/\s*TacticDoc\s+(?P<name>[^\s]+)", contents, re.DOTALL
    ):
        name = match.group("name")
        raw_doc = match.group("doc")
        summary = _summarize_docstring(raw_doc)
        if summary:
            tactic_docs.setdefault(name, summary)
    new_theorems: list[str] = []
    theorem_pattern = re.compile(
        r"^\s*NewTheorem\s+([^\n]*(?:\n[ \t]+[^\n]*)*)",
        re.MULTILINE,
    )
    for match in theorem_pattern.finditer(contents):
        block = match.group(1)
        for line in block.splitlines():
            cleaned = line.split("--", 1)[0].strip()
            if not cleaned:
                continue
            for name in cleaned.split():
                if name:
                    new_theorems.append(name)

    return LevelMetadata(
        module=module,
        namespace=namespace,
        signature=signature,
        statement_name=statement_name,
        new_tactics=new_tactics or None,
        hidden_tactics=hidden_tactics or None,
        world=world,
        level=level,
        tactic_docs=tactic_docs or None,
        new_theorems=new_theorems or None,
    )


def get_problem_server_from_file(
    level_path: str | os.PathLike[str], *, verbose: bool = False
) -> LeanServer:
    """Start a Lean server configured to work on the goal extracted from a level file."""

    metadata = parse_level_file(level_path)
    code_lines: list[str] = [f"import {metadata.module}", ""]
    if metadata.namespace:
        code_lines.extend([f"open {metadata.namespace}", ""])
    code_lines.extend(
        [
            f"theorem ex {metadata.signature} := by",
            "    sorry",
        ]
    )

    config = get_nng_config(verbose=verbose)
    with _suppress_output(not verbose):
        server = LeanServer(config)
        output = server.run(Command(cmd="\n".join(code_lines)))
    if verbose:
        pprint(output)
    return server


def get_problem_server(theorem: str, level: str, *, verbose=False) -> LeanServer:
    code = f"""
import Game.Levels.{level}

theorem ex {theorem}  := by
    sorry
"""
    config = get_nng_config(verbose=verbose)
    with _suppress_output(not verbose):
        server = LeanServer(config)  # start Lean REPL
        output = server.run(Command(cmd=code))
    if verbose:
        pprint(output)
    return server


def get_nng_config(*, verbose: bool = False) -> LeanREPLConfig:
    nng_path = os.environ["NNG_PATH"]
    if not os.path.isdir(nng_path):
        raise NotADirectoryError(f"NNG_PATH '{nng_path}' is not a valid directory")
    with _suppress_output(not verbose):
        nng_project = LocalProject(directory=nng_path)
    return LeanREPLConfig(
        project=nng_project,
        verbose=verbose,
    )


@singledispatch
def pprint(x: Any) -> None:
    print(x)


@pprint.register
def _(x: CommandResponse) -> None:
    # Check if there are any errors
    has_errors = x.has_errors()

    # Print status with color
    if has_errors:
        print("\033[91mBuild completed with errors\033[0m")  # Red
    else:
        print("\033[92mBuild completed successfully\033[0m")  # Green

    # Print messages
    if x.messages:
        print("\nMessages:")
        for msg in x.messages:
            severity_color = (
                "\033[91m" if msg.severity == "error" else "\033[93m"
            )  # Red for error, yellow for warning
            print(
                f"  {severity_color}[{msg.severity.upper()}]\033[0m at line {msg.start_pos.line}, col {msg.start_pos.column}-{msg.end_pos.column}"
            )
            print(f"    {msg.data}")

    # Print sorries
    if x.sorries:
        print(f"\n\033[96mSorries found: {len(x.sorries)}\033[0m")  # Cyan
        for i, sorry in enumerate(x.sorries, 1):
            print(
                f"  Sorry {i} at line {sorry.start_pos.line}, col {sorry.start_pos.column}-{sorry.end_pos.column}"
            )
            print(f"    Goal: {sorry.goal}")

    # Print environment info
    print(f"\n\033[90mEnvironment: {x.env}\033[0m")  # Dark gray


@pprint.register
def _(x: ProofStepResponse) -> None:
    status_color = (
        "\033[92m" if x.proof_status == "Completed" else "\033[93m"
    )  # Green for completed, yellow for others
    print(f"{status_color}Proof Step: {x.proof_status}\033[0m")
    print(f"  Proof state: \033[90m{x.proof_state}\033[0m")  # Gray

    if x.goals:
        print(f"  \033[93mRemaining goals: {len(x.goals)}\033[0m")  # Yellow
        for i, goal in enumerate(x.goals, 1):
            print(f"    Goal {i}: {goal}")
    else:
        print("  \033[92mNo remaining goals\033[0m")  # Green


@pprint.register
def _(x: LeanError) -> None:
    print("\033[91mLean Error:\033[0m")  # Red header
    # Clean up the message by removing the "Lean error:\n" prefix if present
    message = x.message
    if message.startswith("Lean error:\n"):
        message = message[12:]  # Remove "Lean error:\n"

    # Print each line of the error with proper indentation
    for line in message.split("\n"):
        if line.strip():  # Skip empty lines
            print(f"  {line}")
