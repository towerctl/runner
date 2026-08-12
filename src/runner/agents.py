"""Agent executors. M0: echo. M1: claude."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExecResult:
    output: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0


def execute(kind: str, input_text: str) -> ExecResult:
    if kind == "echo":
        n = max(1, len(input_text.split()))
        return ExecResult(output=input_text, tokens_in=n, tokens_out=n, cost_usd=0.0)
    raise ValueError(f"unknown agent kind: {kind}")
