from lean_interact import Command, ProofStep

from llean.utils import get_problem_server, pprint

level = "Tutorial.L01rfl"
problem = "(x q : ℕ) : 37 * x + q = 37 * x + q"

server = get_problem_server(problem, level, verbose=True)

output = server.run(Command(cmd="#help tactic"))
pprint(output)
output = server.run(ProofStep(tactic="rfl", proofState=0))
pprint(output)
