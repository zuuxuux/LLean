import json

from lean_interact import Command, LeanREPLConfig, LeanServer
from lean_interact.interface import CommandResponse
from rich import print as pprint

# Start the server as before. We import Mathlib to get a rich set of tactics.
config = LeanREPLConfig(verbose=True)
server = LeanServer(config)
# Pre-load Mathlib so we get a rich set of tactics to list.
print("Loading Mathlib...")
server.run(Command(cmd="import Mathlib"))
print("Mathlib loaded.")

# This is the DEFINITIVE Lean metaprogramming command.
list_tactics_command = """
import Lean.Elab.Tactic

open Lean Elab Tactic Meta Parser.Tactic in
def listAllTactics : MetaM Json := do
  let env ← getEnv
  let mut tacticDocs : Array Json := #[]
  let mut seen : HashSet String := {}
  
  -- Get all constants in the environment
  for (name, _) in env.constants do
    let nameStr := name.toString
    
    -- Multiple patterns to catch different tactic definitions
    let patterns := [
      ("Lean.Elab.Tactic.eval", ""),
      ("Mathlib.Tactic.eval", ""),
      ("Mathlib.Tactic.Eval", ""),
      ("Aesop.Frontend.eval", ""),
      ("Lean.Parser.Tactic.", ""),
      ("Mathlib.Tactic.", "tactic_"),
      ("Std.Tactic.", "")
    ]
    
    for (prefix, removePrefix) in patterns do
      if nameStr.startsWith prefix then
        -- Extract tactic name
        let tacticName := nameStr.replace prefix ""
        -- Clean up the name
        let cleanName := tacticName
          |>.replace "._@." ""
          |>.replace "._hyg." "_"
          |>.splitOn "."
          |>.getLast!
          |>.splitOn "_"
          |>.head!
        
        -- Skip if we've seen this tactic
        if !seen.contains cleanName then
          seen := seen.insert cleanName
          
          -- Try to get documentation
          let doc ← findDocString? env name
          match doc with
          | some docStr =>
            tacticDocs := tacticDocs.push (Json.mkObj [
              ("name", Json.str cleanName),
              ("fullName", Json.str nameStr),
              ("doc", Json.str docStr)
            ])
          | none =>
            -- Include even without docs to see all tactics
            tacticDocs := tacticDocs.push (Json.mkObj [
              ("name", Json.str cleanName),
              ("fullName", Json.str nameStr),
              ("doc", Json.str "")
            ])
  
  return Json.arr tacticDocs

-- Create a command that runs this
open Lean Elab Command in
elab "list_all_tactics" : command => do
  let result ← liftTermElabM <| listAllTactics
  -- Convert JSON to string for output
  let jsonStr := toString result
  logInfo jsonStr

list_all_tactics
"""

print("\n--- Programmatically listing all available tactics ---")
response = server.run(Command(cmd=list_tactics_command))

# Parse the JSON response
if isinstance(response, CommandResponse) and response.messages:
    for msg in response.messages:
        if msg.severity == "info":
            try:
                # Parse the JSON
                tactic_list = json.loads(msg.data)

                # Filter out duplicates and sort by name
                unique_tactics = {}
                for tactic in tactic_list:
                    name = tactic["name"]
                    if name not in unique_tactics or len(tactic["doc"]) > len(
                        unique_tactics[name]["doc"]
                    ):
                        unique_tactics[name] = tactic

                tactic_list = sorted(
                    unique_tactics.values(), key=lambda x: x["name"].lower()
                )

                print(f"Successfully found {len(tactic_list)} unique tactics")

                # Find simp
                for tactic in tactic_list:
                    if tactic["name"].lower() == "simp":
                        print("\n--- Documentation for 'simp' ---")
                        pprint(
                            {
                                "name": tactic["name"],
                                "doc": tactic["doc"][:500] + "..."
                                if len(tactic["doc"]) > 500
                                else tactic["doc"],
                            }
                        )
                        break

                # Show some well-known tactics
                print("\n--- Sample of well-known tactics ---")
                known_tactics = [
                    "simp",
                    "rw",
                    "apply",
                    "exact",
                    "intro",
                    "cases",
                    "induction",
                    "constructor",
                    "rfl",
                    "sorry",
                    "omega",
                    "ring",
                    "linarith",
                    "norm_num",
                ]

                found_known = []
                for known in known_tactics:
                    for tactic in tactic_list:
                        if tactic["name"].lower() == known.lower():
                            found_known.append(tactic["name"])
                            break

                print(f"Found these well-known tactics: {', '.join(found_known)}")

                # Show all tactics with documentation
                print("\n--- All tactics with documentation (first 30) ---")
                documented = [t for t in tactic_list if t["doc"]]
                for tactic in documented[:30]:
                    doc_preview = tactic["doc"][:100].replace("\n", " ")
                    if len(tactic["doc"]) > 100:
                        doc_preview += "..."
                    print(f"  • {tactic['name']}: {doc_preview}")

                # Save full list to file
                with open("lean_tactics.json", "w") as f:
                    json.dump(tactic_list, f, indent=2)
                print(f"\nFull list saved to lean_tactics.json")

            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {e}")
                print(f"Response data: {msg.data[:500]}")

server.kill()
