"""Depth-first tactic exploration for Tutorial levels."""

from pathlib import Path

from llean.search import depth_first_search


def main() -> None:
    level_dir = Path("NNG4/Game/Levels/Tutorial")
    levels = sorted(level_dir.glob("L0*.lean"))

    summary: list[tuple[str, int]] = []

    for level_path in levels:
        print(f"Level: {level_path.name}")
        solutions = depth_first_search(level_path, max_depth=20)
        summary.append((level_path.name, len(solutions)))
        if not solutions:
            print("  No solution found within depth limit")
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
