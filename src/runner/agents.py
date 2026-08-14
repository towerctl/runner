"""Agent executors. M0: echo. M1: claude (Anthropic API, real cost accounting)."""

from __future__ import annotations

import os
from dataclasses import dataclass

# USD per million tokens (input, output). Verify against
# https://docs.claude.com/en/docs/about-claude/pricing before relying on
# exact figures — prices change; unknown models fall back to DEFAULT_PRICE.
PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "claude-sonnet-5": (3.00, 15.00),
}
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_PRICE = (3.00, 15.00)


@dataclass
class ExecResult:
    output: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    p_in, p_out = PRICES_PER_MTOK.get(model, DEFAULT_PRICE)
    return round((tokens_in * p_in + tokens_out * p_out) / 1_000_000, 6)


def _execute_echo(input_text: str) -> ExecResult:
    n = max(1, len(input_text.split()))
    return ExecResult(output=input_text, tokens_in=n, tokens_out=n, cost_usd=0.0)


def _execute_claude(input_text: str, model: str | None, system_prompt: str | None) -> ExecResult:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY not set — cannot run claude agents")
    import anthropic

    client = anthropic.Anthropic()
    model = model or DEFAULT_MODEL
    msg = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt or "You are a helpful agent running on the towerctl platform.",
        messages=[{"role": "user", "content": input_text}],
    )
    output = "".join(block.text for block in msg.content if block.type == "text")
    t_in, t_out = msg.usage.input_tokens, msg.usage.output_tokens
    return ExecResult(
        output=output,
        tokens_in=t_in,
        tokens_out=t_out,
        cost_usd=cost_usd(model, t_in, t_out),
    )


def execute(
    kind: str, input_text: str, model: str | None = None, system_prompt: str | None = None
) -> ExecResult:
    if kind == "echo":
        return _execute_echo(input_text)
    if kind == "claude":
        return _execute_claude(input_text, model, system_prompt)
    raise ValueError(f"unknown agent kind: {kind}")
