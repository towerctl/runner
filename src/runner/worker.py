"""towerctl runner: consumes run.created, executes the agent, reports back.

Consumes: run.created.  Emits: run.completed, cost.recorded.
Talks to the gateway only through the core SDK (internal endpoints).

M0 agent kinds: echo. M1 adds claude (Anthropic API) with per-run cost.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from towerctl_core.bus import EventBus, bus_from_env
from towerctl_core.client import GatewayClient
from towerctl_core.events import COST_RECORDED, RUN_COMPLETED, RUN_CREATED, Event
from towerctl_core.models import RunStatus, RunUpdate

from runner.agents import execute


class Worker:
    def __init__(self, client: GatewayClient, bus: EventBus) -> None:
        self.client = client
        self.bus = bus
        bus.subscribe(RUN_CREATED, self.handle)

    def handle(self, ev: Event) -> None:
        run_id = ev.payload["run_id"]
        run = self.client.get_run(run_id)
        agent = {a.id: a for a in self.client.list_agents()}.get(run.agent_id)
        started = datetime.now(timezone.utc)
        self.client.update_run(run_id, RunUpdate(status=RunStatus.RUNNING, started_at=started))
        t0 = time.perf_counter()
        try:
            result = execute(agent.kind if agent else "echo", run.input)
            status = RunStatus.SUCCEEDED
            upd = RunUpdate(
                status=status,
                output=result.output,
                tokens_in=result.tokens_in,
                tokens_out=result.tokens_out,
                cost_usd=result.cost_usd,
            )
        except Exception as e:  # noqa: BLE001 — worker must survive any executor failure
            status = RunStatus.FAILED
            upd = RunUpdate(status=status, error=f"{type(e).__name__}: {e}")
        self.client.update_run(run_id, upd)
        duration = time.perf_counter() - t0
        self.bus.publish(
            Event(
                topic=RUN_COMPLETED,
                payload={
                    "run_id": run_id,
                    "agent_id": run.agent_id,
                    "status": status.value,
                    "duration_s": round(duration, 4),
                },
            )
        )
        if status is RunStatus.SUCCEEDED:
            self.bus.publish(
                Event(
                    topic=COST_RECORDED,
                    payload={
                        "run_id": run_id,
                        "agent_id": run.agent_id,
                        "tokens_in": upd.tokens_in or 0,
                        "tokens_out": upd.tokens_out or 0,
                        "cost_usd": upd.cost_usd or 0.0,
                    },
                )
            )

    def loop(self) -> None:
        while True:
            self.bus.poll(block_ms=2000)


def main() -> None:
    client = GatewayClient(
        base_url=os.environ.get("GATEWAY_URL", "http://localhost:8080"),
        api_key=os.environ.get("TOWERCTL_INTERNAL_KEY", "internal-key"),
    )
    Worker(client, bus_from_env(group="runner")).loop()


if __name__ == "__main__":
    main()
