# towerctl/runner

The worker. Consumes `run.created` from the bus, executes the agent, reports
status via the gateway's internal API, and emits `run.completed` +
`cost.recorded`.

M0 agent kinds: `echo`. M1: `claude` (Anthropic API) with real token/cost
accounting and sandboxed tool use.

```bash
pip install -e .[dev]
GATEWAY_URL=http://localhost:8080 REDIS_URL=redis://localhost:6379 python -m runner.worker
```

Failure handling: any executor exception marks the run `failed` with the
error string; the worker never dies on a bad run. See
`infra/runbooks/runner-wedged.md` for on-call procedures.
