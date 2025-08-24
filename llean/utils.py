from functools import singledispatch
from typing import Any

from lean_interact.interface import CommandResponse, LeanError, ProofStepResponse


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
