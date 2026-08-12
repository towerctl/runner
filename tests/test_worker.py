from towerctl_core.bus import InMemoryBus
from towerctl_core.events import COST_RECORDED, RUN_COMPLETED, RUN_CREATED, Event
from towerctl_core.models import AgentSpec, Run, RunUpdate

from runner.agents import execute
from runner.worker import Worker


class FakeClient:
    """Stands in for GatewayClient — same duck type, no HTTP."""

    def __init__(self):
        self.agent = AgentSpec(name="echo-1", kind="echo")
        self.run = Run(agent_id=self.agent.id, input="hello world")
        self.updates: list[RunUpdate] = []

    def get_run(self, run_id):
        return self.run

    def list_agents(self):
        return [self.agent]

    def update_run(self, run_id, upd):
        self.updates.append(upd)
        return self.run


def test_echo_agent():
    r = execute("echo", "one two three")
    assert r.output == "one two three"
    assert r.tokens_in == 3


def test_worker_happy_path():
    client = FakeClient()
    bus = InMemoryBus()
    Worker(client, bus)
    bus.publish(
        Event(topic=RUN_CREATED, payload={"run_id": client.run.id, "agent_id": client.agent.id})
    )
    bus.poll()
    statuses = [u.status.value for u in client.updates]
    assert statuses == ["running", "succeeded"]
    topics = [e.topic for e in bus.history]
    assert RUN_COMPLETED in topics and COST_RECORDED in topics
