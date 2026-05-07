# Agent Task: Scaffold KRAKEN AstaBench Solver

## Goal

Create the initial `kraken-chatbot-solver` Python package that wraps the KRAKEN discovery pipeline as an Inspect AI solver, runnable through AstaBench.

## Context

- **AstaBench** (`~/projects/asta-bench/`) is AI2's scientific agent benchmark framework, built on Inspect AI. It's already installed and running in Docker (`make shell` from that directory).
- **KRAKEN** (`~/trentleslie@gmail.com/Google Drive/projects/kraken-chatbot/`) is the discovery pipeline. The graph lives at `backend/src/kestrel_backend/graph/`. The builder is `builder.py`, state is `state.py`, entry point is `build_discovery_graph()` from `builder.py`.
- The solver needs to be a **separate repo** that imports from `kestrel_backend` (via editable install) and exposes an Inspect AI solver function.
- **DO NOT modify kraken-chatbot** — that has its own agent task. This repo only wraps the existing pipeline.

## What to Build

### 1. Package structure

```
kraken-chatbot-solver/
├── pyproject.toml
├── README.md
├── .env.example          # ANTHROPIC_API_KEY, ASTA_TOOL_KEY, HF_TOKEN
├── src/
│   └── kraken_solver/
│       ├── __init__.py
│       ├── solver.py     # The Inspect solver wrapper
│       └── formatting.py # Output formatting helpers
└── tests/
    └── test_solver_smoke.py
```

### 2. pyproject.toml

- Package name: `kraken-asta-solver`
- Python >=3.12
- Dependencies: `inspect-ai`, `kestrel-backend` (editable, path to local kraken-chatbot/backend), `litellm`, `langgraph`
- Dev deps: `pytest`, `pytest-asyncio`
- Build system: hatchling

### 3. solver.py — Core solver function

Reference the solver wrapper sketch from the eval strategy. Key points:

```python
from inspect_ai.solver import solver, TaskState, Generate
from kestrel_backend.graph.builder import build_discovery_graph  # verify this import path
from kestrel_backend.graph.state import DiscoveryState

@solver
def kraken_discovery_solver(
    model: str = "anthropic/claude-sonnet-4-6",
    enable_literature_grounding: bool = True,
    **tool_options,
):
    """KRAKEN discovery pipeline as an Inspect solver."""
    
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        # 1. Build initial state from benchmark input
        initial_state: DiscoveryState = {
            "raw_query": state.input_text,
            "conversation_history": [],
        }
        
        # 2. Run the KRAKEN graph
        graph = build_discovery_graph()  # check builder.py for actual signature
        final_state = await graph.ainvoke(initial_state)
        
        # 3. Format output for benchmark scoring
        state.output.completion = format_output_for_benchmark(
            synthesis_report=final_state.get("synthesis_report", ""),
            hypotheses=final_state.get("hypotheses", []),
        )
        
        # 4. Preserve structured state for custom scorers
        state.metadata["kraken_state"] = serialize_kraken_state(final_state)
        
        # 5. Cost tracking (will work once model_usages is added to DiscoveryState)
        for usage in final_state.get("model_usages", []):
            record_model_usage_with_inspect(usage.model_name, usage.to_inspect_usage())
        
        return state
    
    return solve
```

**IMPORTANT**: Read `builder.py` carefully to understand the actual `build_discovery_graph()` signature. The sketch above is from a planning doc — the real function may take different arguments. Also verify the import path works: `from kestrel_backend.graph.builder import build_discovery_graph`.

### 4. formatting.py

- `format_output_for_benchmark(synthesis_report, hypotheses)` — converts KRAKEN's structured output into text suitable for benchmark scoring
- `serialize_kraken_state(final_state)` — serializes all Pydantic models in DiscoveryState to dicts for metadata attachment

### 5. Smoke test

A minimal test that:
- Imports the solver successfully
- Verifies it's a valid Inspect solver (right decorator, right signature)
- Does NOT run the full pipeline (that requires DB connections etc.)

## Key References

- AstaBench custom solver docs: see "Building an AstaBench Agent" section in `~/projects/asta-bench/README.md`
- Cost logging: use `from astabench.util.model import record_model_usage_with_inspect`
- KRAKEN state schema: `~/trentleslie@gmail.com/Google Drive/projects/kraken-chatbot/backend/src/kestrel_backend/graph/state.py`
- KRAKEN graph builder: `~/trentleslie@gmail.com/Google Drive/projects/kraken-chatbot/backend/src/kestrel_backend/graph/builder.py`
- Eval strategy doc: `~/Documents/Trent's Vault/Active 🎯/Work/Strategy/KRAKEN/Evaluation Strategy.md`

## What NOT to do

- Don't modify anything in kraken-chatbot
- Don't implement cost tracking in the solver yet (the `model_usages` field doesn't exist on DiscoveryState yet — that's being added separately)
- Don't try to run the full pipeline — just get the scaffold, imports, and solver structure right
- Don't build custom scorers yet — that's Phase 4
- Don't fork or copy asta-bench code — import from it

## Success Criteria

- `uv sync` succeeds with editable install of kestrel-backend
- `from kraken_solver.solver import kraken_discovery_solver` works
- Smoke test passes
- Solver can be referenced by import path for `inspect eval --solver kraken_solver/solver.py:kraken_discovery_solver`
