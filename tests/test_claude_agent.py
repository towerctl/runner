"""Claude executor tests — Anthropic API fully mocked, no key or network."""

import sys
import types
from dataclasses import dataclass

import pytest

from runner.agents import DEFAULT_MODEL, cost_usd, execute


def test_cost_table():
    # 1M in + 1M out on haiku 4.5 = $1 + $5
    assert cost_usd("claude-haiku-4-5-20251001", 1_000_000, 1_000_000) == 6.0
    # unknown models use the default price, never crash
    assert cost_usd("claude-mystery-9", 1_000_000, 0) == 3.0


def test_claude_requires_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        execute("claude", "hi")


def test_claude_happy_path(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

    @dataclass
    class Block:
        type: str
        text: str

    @dataclass
    class Usage:
        input_tokens: int
        output_tokens: int

    @dataclass
    class Msg:
        content: list
        usage: Usage

    class FakeMessages:
        def create(self, **kw):
            assert kw["model"] == DEFAULT_MODEL
            return Msg(content=[Block("text", "pong")], usage=Usage(12, 4))

    class FakeAnthropic:
        def __init__(self, *a, **kw):
            self.messages = FakeMessages()

    fake_mod = types.ModuleType("anthropic")
    fake_mod.Anthropic = FakeAnthropic
    monkeypatch.setitem(sys.modules, "anthropic", fake_mod)

    r = execute("claude", "ping")
    assert r.output == "pong"
    assert (r.tokens_in, r.tokens_out) == (12, 4)
    assert r.cost_usd == cost_usd(DEFAULT_MODEL, 12, 4)
