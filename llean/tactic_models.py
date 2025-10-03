"""Structured representations for common Lean tactics used in solutions."""

from __future__ import annotations

import re
from typing import ClassVar, Literal, Pattern, Type, TypeVar

from pydantic import BaseModel, Field, field_validator


class TacticParseError(ValueError):
    """Raised when a tactic string cannot be parsed into a structured model."""


def _strip_inline_comment(command: str) -> str:
    head, *_tail = command.split("--", 1)
    return head.strip()


def _split_arguments(argument_block: str) -> list[str]:
    """Split a comma separated block while respecting bracket nesting."""

    entries: list[str] = []
    current: list[str] = []
    depth = 0
    for char in argument_block:
        if char == "," and depth == 0:
            entry = "".join(current).strip()
            if entry:
                entries.append(entry)
            current = []
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth = max(depth - 1, 0)
        current.append(char)

    tail = "".join(current).strip()
    if tail:
        entries.append(tail)
    return entries


RewriteDirection = Literal["forward", "backward"]


class RewriteRule(BaseModel):
    expression: str = Field(
        ..., description="Lean expression supplied to `rw`/`nth_rewrite`"
    )
    direction: RewriteDirection = Field(
        "forward", description="Rewrite direction: forward (default) or backward"
    )

    @field_validator("expression")
    @classmethod
    def _strip_expression(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("rewrite expression cannot be empty")
        return cleaned

    def to_string(self) -> str:
        prefix = "← " if self.direction == "backward" else ""
        return f"{prefix}{self.expression}"

    @classmethod
    def from_string(cls, token: str) -> RewriteRule:
        trimmed = token.strip()
        direction: RewriteDirection = "forward"
        if trimmed.startswith("←"):
            direction = "backward"
            trimmed = trimmed[1:].lstrip()
        return cls(expression=trimmed, direction=direction)


class TacticModel(BaseModel):
    """Base class for structured tactic representations."""

    tactic: ClassVar[str | None] = None

    def to_string(self) -> str:  # pragma: no cover - interface definition
        raise NotImplementedError

    @classmethod
    def from_string(cls, command: str) -> "TacticModel":
        """Dispatch to the appropriate concrete tactic model."""

        if cls is TacticModel:
            stripped = _strip_inline_comment(command)
            if not stripped:
                raise TacticParseError("Empty tactic command")
            keyword = stripped.split(maxsplit=1)[0]
            factory = TACTIC_REGISTRY.get(keyword)
            if not factory:
                raise TacticParseError(f"Unsupported tactic keyword: '{keyword}'")
            return factory.from_string(stripped)
        raise NotImplementedError


class RewriteTactic(TacticModel):
    """Representation of the `rw` tactic."""

    tactic: ClassVar[str] = "rw"

    rules: list[RewriteRule]
    location: str | None = Field(default=None, description="Optional `at` target")

    _pattern: ClassVar[Pattern[str]] = re.compile(
        r"^rw\s+\[(?P<body>.+)](?:\s+at\s+(?P<location>.+))?$",
        re.DOTALL,
    )

    def to_string(self) -> str:
        body = ", ".join(rule.to_string() for rule in self.rules)
        result = f"rw [{body}]"
        if self.location:
            result += f" at {self.location}"
        return result

    @classmethod
    def from_string(cls, command: str) -> RewriteTactic:
        cleaned = _strip_inline_comment(command)
        match = cls._pattern.fullmatch(cleaned)
        if not match:
            raise TacticParseError(f"Unable to parse rewrite command: '{command}'")
        body = match.group("body").strip()
        location = match.group("location")
        tokens = _split_arguments(body)
        if not tokens:
            raise TacticParseError("`rw` requires at least one rewrite rule")
        rules = [RewriteRule.from_string(token) for token in tokens]
        target = location.strip() if location else None
        return cls(rules=rules, location=target)


class ApplyTactic(TacticModel):
    """Representation of the `apply` tactic."""

    tactic: ClassVar[str] = "apply"

    expression: str
    location: str | None = Field(default=None, description="Optional `at` target")

    _pattern: ClassVar[Pattern[str]] = re.compile(
        r"^apply\s+(?P<expr>.+?)(?:\s+at\s+(?P<location>.+))?$",
        re.DOTALL,
    )

    @field_validator("expression")
    @classmethod
    def _strip_expression(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("`apply` requires a non-empty expression")
        return cleaned

    def to_string(self) -> str:
        base = f"apply {self.expression}"
        if self.location:
            base += f" at {self.location}"
        return base

    @classmethod
    def from_string(cls, command: str) -> ApplyTactic:
        cleaned = _strip_inline_comment(command)
        match = cls._pattern.fullmatch(cleaned)
        if not match:
            raise TacticParseError(f"Unable to parse apply command: '{command}'")
        expression = match.group("expr")
        location = match.group("location")
        return cls(expression=expression, location=location.strip() if location else None)


class NthRewriteTactic(TacticModel):
    """Representation of the `nth_rewrite` tactic."""

    tactic: ClassVar[str] = "nth_rewrite"

    index: int
    rule: RewriteRule
    location: str | None = Field(default=None, description="Optional `at` target")

    _pattern: ClassVar[Pattern[str]] = re.compile(
        r"^nth_rewrite\s+(?P<index>\d+)\s+\[(?P<body>.+)](?:\s+at\s+(?P<location>.+))?$",
        re.DOTALL,
    )

    def to_string(self) -> str:
        body = self.rule.to_string()
        result = f"nth_rewrite {self.index} [{body}]"
        if self.location:
            result += f" at {self.location}"
        return result

    @classmethod
    def from_string(cls, command: str) -> NthRewriteTactic:
        cleaned = _strip_inline_comment(command)
        match = cls._pattern.fullmatch(cleaned)
        if not match:
            raise TacticParseError(
                f"Unable to parse nth_rewrite command: '{command}'"
            )
        body = match.group("body").strip()
        tokens = _split_arguments(body)
        if len(tokens) != 1:
            raise TacticParseError(
                "`nth_rewrite` currently supports exactly one rewrite rule"
            )
        rule = RewriteRule.from_string(tokens[0])
        index = int(match.group("index"))
        location = match.group("location")
        return cls(rule=rule, index=index, location=location.strip() if location else None)


TacticType = TypeVar("TacticType", bound=TacticModel)

TACTIC_REGISTRY: dict[str, Type[TacticModel]] = {
    RewriteTactic.tactic: RewriteTactic,
    ApplyTactic.tactic: ApplyTactic,
    NthRewriteTactic.tactic: NthRewriteTactic,
}


def parse_tactic(command: str) -> TacticModel:
    """Parse a tactic string into the appropriate structured model."""
    return TacticModel.from_string(command)


__all__ = [
    "ApplyTactic",
    "NthRewriteTactic",
    "RewriteRule",
    "RewriteTactic",
    "TacticModel",
    "TacticParseError",
    "parse_tactic",
]
