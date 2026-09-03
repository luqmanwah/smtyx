"""Backward-compatible bridge entrypoint for v0.1."""

from .bridge import ToolCall, VocabOrchestrator, VocabToolRule

__all__ = ["VocabOrchestrator", "VocabToolRule", "ToolCall"]
