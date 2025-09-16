"""Depth-first tactic exploration for Tutorial levels."""

from pathlib import Path

from llean.search import SearchGraph, depth_first_search


def main() -> None:
    level_dir = Path("NNG4/Game/Levels/Tutorial")
    levels = sorted(level_dir.glob("L0*.lean"))

    summary: list[tuple[str, int]] = []

    for level_path in levels:
        print(f"Level: {level_path.name}")
        trace = SearchGraph()
        solutions = depth_first_search(level_path, max_depth=10, trace=trace)
        summary.append((level_path.name, len(solutions)))
        if not solutions:
            print("  No solution found within depth limit")
            root = trace.root
            if root is not None:
                root_node = trace.nodes.get(root)
                if root_node:
                    tried = (
                        ", ".join(root_node.tactics_tried)
                        if root_node.tactics_tried
                        else "-"
                    )
                    print(f"  Tactics attempted at root: {tried}")
                    failed_only = [
                        t
                        for t in root_node.failures
                        if t not in {tac for tac, _ in root_node.successes}
                    ]
                    if failed_only:
                        print(f"  Failed tactics: {', '.join(failed_only)}")
            stuck_nodes = [
                n for n in trace.nodes.values() if n.goals and not n.successes
            ]
            if stuck_nodes:
                sample = stuck_nodes[:3]
                print("  Sample stuck goals:")
                for info in sample:
                    goal_preview = (
                        info.goals[0].split("\n", 1)[0] if info.goals else "<completed>"
                    )
                    tried = ", ".join(info.tactics_tried) if info.tactics_tried else "-"
                    print(f"    depth {info.depth}: {goal_preview} | tried: {tried}")
            continue
        for idx, solution in enumerate(solutions[:5], start=1):
            tactic_str = ", ".join(solution) if solution else "<empty>"
            print(f"  Solution {idx}: {tactic_str}")
        if len(solutions) > 5:
            print(f"  ... {len(solutions) - 5} more solutions omitted")

    print("\nSummary (solutions within depth limit):")
    for level_name, count in summary:
        print(f"  {level_name}: {count}")


if __name__ == "__main__":
    main()
