"""Recreates the Tutorial level using metadata parsed from the original Lean file."""

import os
from pathlib import Path

from lean_interact import Command, ProofStep

from llean.utils import get_problem_server_from_file, pprint

level_path = Path(os.environ["NNG_PATH"]) / "Game/Levels/Tutorial/L01rfl.lean"

server = get_problem_server_from_file(level_path, verbose=True)

output = server.run(Command(cmd="#help tactic"))
pprint(output)
output = server.run(ProofStep(tactic="rfl", proofState=0))
pprint(output)
