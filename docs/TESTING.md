# Testing

The default test suite is fully offline. It must not call a real LLM,
SerpAPI, SendGrid, LangSmith, or another network service.

## Test layout

```text
tests/
├── conftest.py                    # Fake credentials and isolated memory
├── test_agent_workflow.py         # Phase 2 graph and multi-turn flow
├── test_phase2_nodes.py           # Route, budget, itinerary, safety, formatting
├── test_collect_preferences.py    # Preference extraction and normalization
├── test_flights_finder.py         # SerpAPI flight adapter with mocks
├── test_hotels_finder.py          # SerpAPI hotel adapter with mocks
├── test_memory_simple.py          # Preference persistence
└── test_memory_integration.py     # Tool and memory integration with a fake LLM
```

## Offline policy

- LLM-backed nodes receive deterministic stub objects through dependency
  injection.
- SerpAPI modules are patched at the adapter boundary.
- Email tests use an in-memory transport instead of SendGrid.
- Each test receives an isolated temporary preference store.
- Test environment variables contain fake credentials.
- LangSmith tracing is disabled before application modules are imported.

Run the complete offline suite:

```bash
poetry run pytest -q
```

Run only the Phase 2 workflow tests:

```bash
poetry run pytest -q tests/test_agent_workflow.py tests/test_phase2_nodes.py
```

Generate coverage:

```bash
poetry run pytest --cov=agents --cov-report=html
```

## Real-service tests

Real LLM or external-service checks are intentionally separate from the
default suite. They should use the existing pytest markers:

- `external`: calls an external API
- `e2e`: exercises the deployed integration
- `slow`: unsuitable for the normal edit/test loop

Do not run or add a real-LLM test to the default suite. Before executing one,
obtain explicit approval, use dedicated test credentials, disable production
side effects, and set strict timeout and cost limits.

After dedicated external tests exist, offline CI can exclude them with:

```bash
poetry run pytest -m "not external and not e2e and not slow"
```

## Phase 2 coverage

The workflow suite verifies:

- all Phase 2 nodes are present;
- incomplete preferences stop before destination search;
- clarification is requested at most once;
- a second user turn merges preferences and resumes planning;
- complete input reaches the email interrupt;
- no place is dropped when distributing activities across days;
- budget days and accommodation nights are consistent;
- standard output contains constraints, overview, daily plans, budget,
  risks, alternatives, confirmation items, and safety review;
- sensitive requests require manual confirmation;
- email resume uses an injected offline transport.
