"""Dump the full DFS trace for Tutorial level L03."""

from pathlib import Path

from llean.search import SearchGraph, depth_first_search


def format_goal(goal: str) -> str:
    lines = goal.splitlines()
    if len(lines) <= 6:
        return "\n      " + "\n      ".join(lines)
    return "\n      " + "\n      ".join(lines[:6]) + "\n      ..."


def main() -> None:
    level_path = Path("NNG4/Game/Levels/Tutorial/L03two_eq_ss0.lean")
    trace = SearchGraph()
    solutions = depth_first_search(level_path, max_depth=20, trace=trace)

    print(f"Solutions found: {len(solutions)}")
    for idx, solution in enumerate(solutions, start=1):
        print(f"  Solution {idx}: {', '.join(solution)}")

    print("\nTrace nodes:")
    for state_id, node in sorted(trace.nodes.items(), key=lambda item: item[1].depth):
        print(f"State {state_id} (depth {node.depth})")
        if node.goals:
            for goal in node.goals:
                print(format_goal(goal))
        else:
            print("    <no goals>")
        if node.tactics_tried:
            print(f"    Tactics tried: {', '.join(node.tactics_tried)}")
        if node.successes:
            for tactic, child in node.successes:
                print(f"    Success -> {child} via {tactic}")
        if node.failures:
            print(f"    Failures: {', '.join(node.failures)}")
        print()


if __name__ == "__main__":
    main()
