"""Dump the DFS trace for Tutorial level L08."""

from pathlib import Path

from llean.search import SearchGraph, depth_first_search


def format_goal(goal: str) -> str:
    lines = goal.splitlines()
    preview = lines[:6]
    result = "\n      " + "\n      ".join(preview)
    if len(lines) > 6:
        result += "\n      ..."
    return result


def main() -> None:
    level_path = Path("NNG4/Game/Levels/Tutorial/L08twoaddtwo.lean")
    trace = SearchGraph()
    solutions = depth_first_search(level_path, max_depth=2, trace=trace)

    print(f"Solutions found: {len(solutions)}")
    for idx, solution in enumerate(solutions, start=1):
        print(f"  Solution {idx}: {', '.join(solution)}")

    print("\nTrace nodes (first 100 by depth):")
    sorted_nodes = sorted(
        trace.nodes.values(), key=lambda node: (node.depth, node.state_id)
    )
    for node in sorted_nodes[:100]:
        print(f"State {node.state_id} (depth {node.depth})")
        if node.goals:
            for goal in node.goals:
                print(format_goal(goal))
        else:
            print("    <no goals>")
        if node.tactics_tried:
            print(f"    Tactics tried: {', '.join(node.tactics_tried)}")
        if node.successes:
            for tactic, child in node.successes[:10]:
                print(f"    Success -> {child} via {tactic}")
            if len(node.successes) > 10:
                print(f"    ... {len(node.successes) - 10} more successes")
        if node.failures:
            print(f"    Failures: {', '.join(node.failures[:12])}")
            if len(node.failures) > 12:
                print(f"    ... {len(node.failures) - 12} more failures")
        print()

    remaining = sorted_nodes[100:]
    if remaining:
        print(f"... {len(remaining)} additional nodes not shown")


if __name__ == "__main__":
    main()
