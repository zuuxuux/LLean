from lean_interact import Command, LeanREPLConfig, LeanServer, ProofStep

from llean.utils import pprint

config = LeanREPLConfig(verbose=True)  # download and build Lean REPL
server = LeanServer(config)  # start Lean REPL
output = server.run(
    Command(cmd="theorem ex (x q : Nat) : 37 * x + q = 37 * x + q  := sorry")
)
pprint(output)
output = server.run(ProofStep(tactic="rfl", proofState=0))
pprint(output)
