"""Recreates the Tutorial level using the higher-level level loader."""

from pathlib import Path

from lean_interact import Command, ProofStep

from llean.levels import load_level_from_file
from llean.utils import pprint

level_path = Path("../NNG4/Game/Levels/Tutorial/L01rfl.lean")

context = load_level_from_file(level_path, verbose=True)

print("Available tactics:")
for tactic in context.tactics:
    print(f"  {tactic.name}: {tactic.usage}")

output = context.server.run(ProofStep(tactic="rfl", proofState=0))
pprint(output)
