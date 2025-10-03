"""Public API for the llean helper package."""

from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = [
    "ApplyTactic",
    "LevelContext",
    "NthRewriteTactic",
    "RewriteRule",
    "RewriteTactic",
    "Tactic",
    "TacticModel",
    "TacticParseError",
    "load_level_from_file",
    "parse_tactic",
]

_LAZY_IMPORTS = {
    "LevelContext": ("levels", "LevelContext"),
    "Tactic": ("levels", "Tactic"),
    "load_level_from_file": ("levels", "load_level_from_file"),
    "ApplyTactic": ("tactic_models", "ApplyTactic"),
    "NthRewriteTactic": ("tactic_models", "NthRewriteTactic"),
    "RewriteRule": ("tactic_models", "RewriteRule"),
    "RewriteTactic": ("tactic_models", "RewriteTactic"),
    "TacticModel": ("tactic_models", "TacticModel"),
    "TacticParseError": ("tactic_models", "TacticParseError"),
    "parse_tactic": ("tactic_models", "parse_tactic"),
}

if TYPE_CHECKING:  # pragma: no cover - import side effects for type checkers only
    from .levels import LevelContext, Tactic, load_level_from_file
    from .tactic_models import (
        ApplyTactic,
        NthRewriteTactic,
        RewriteRule,
        RewriteTactic,
        TacticModel,
        TacticParseError,
        parse_tactic,
    )


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute = _LAZY_IMPORTS[name]
    except KeyError as exc:  # pragma: no cover - fall back to default behaviour
        raise AttributeError(f"module 'llean' has no attribute '{name}'") from exc
    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:  # pragma: no cover - simple static listing
    return sorted(set(__all__ + list(globals().keys())))
