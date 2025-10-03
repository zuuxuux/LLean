"""Inspect tactic availability for a Natural Number Game level."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from llean import (
    ApplyTactic,
    NthRewriteTactic,
    RflTactic,
    RewriteRule,
    RewriteTactic,
    load_level_from_file,
)


def _unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def build_rewrite_schemas(lemmas: Iterable[str]) -> list[RewriteTactic]:
    schemas: list[RewriteTactic] = []
    for lemma in lemmas:
        rule_forward = RewriteRule(expression=lemma, direction="forward")
        rule_backward = RewriteRule(expression=lemma, direction="backward")
        schemas.append(RewriteTactic(rules=[rule_forward]))
        schemas.append(RewriteTactic(rules=[rule_backward]))
    return schemas


def build_apply_schemas(lemmas: Iterable[str]) -> list[ApplyTactic]:
    return [ApplyTactic(expression=lemma) for lemma in lemmas]


def build_nth_rewrite_schemas(lemmas: Iterable[str]) -> list[NthRewriteTactic]:
    schemas: list[NthRewriteTactic] = []
    for lemma in lemmas:
        schemas.append(NthRewriteTactic(index=1, rule=RewriteRule(expression=lemma)))
        schemas.append(
            NthRewriteTactic(
                index=1,
                rule=RewriteRule(expression=lemma, direction="backward"),
            )
        )
    return schemas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("level", help="Path to the Natural Number Game level (.lean) file")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose Lean server startup output",
    )
    args = parser.parse_args()

    level_path = Path(args.level).expanduser().resolve()
    context = load_level_from_file(level_path, verbose=args.verbose)

    tactic_names = [t.name for t in context.tactics]
    lemmas = _unique(context.lemmas)

    print(f"Level: {level_path}")
    print(f"Available tactics ({len(tactic_names)}): {', '.join(tactic_names) or '-'}")
    print(f"Known lemmas ({len(lemmas)}): {', '.join(lemmas) or '-'}")
    print()

    schema_records: list[dict[str, object]] = []
    rendered_commands: list[str] = []

    if "rw" in tactic_names:
        for schema in build_rewrite_schemas(lemmas):
            schema_records.append({"tactic": "rw", **schema.model_dump()})
            rendered_commands.append(schema.to_string())

    if "apply" in tactic_names:
        for schema in build_apply_schemas(lemmas):
            schema_records.append({"tactic": "apply", **schema.model_dump()})
            rendered_commands.append(schema.to_string())

    if "nth_rewrite" in tactic_names:
        for schema in build_nth_rewrite_schemas(lemmas):
            schema_records.append({"tactic": "nth_rewrite", **schema.model_dump()})
            rendered_commands.append(schema.to_string())

    if "rfl" in tactic_names:
        schema_records.append({"tactic": "rfl", **RflTactic().model_dump()})
        rendered_commands.append(RflTactic().to_string())

    print("Tactic schemas:")
    if schema_records:
        print(json.dumps(schema_records, indent=2, sort_keys=True))
    else:
        print("  (no structured schemas available for the detected tactics)")

    print()
    print("Rendered commands:")
    if rendered_commands:
        for command in rendered_commands:
            print(f"  {command}")
    else:
        print("  (no structured commands generated)")


if __name__ == "__main__":
    main()
