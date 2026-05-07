---
title: "feat: Scaffold KRAKEN AstaBench Solver Package"
type: feat
status: completed
date: 2026-05-07
---

# feat: Scaffold KRAKEN AstaBench Solver Package

## Overview

Create the initial `kraken-chatbot-solver` Python package that wraps the KRAKEN discovery pipeline as an Inspect AI solver, runnable through AstaBench. This is a scaffold — no full pipeline execution, no cost tracking, no custom scorers.

## Problem Frame

KRAKEN's discovery pipeline (`kestrel_backend.graph`) runs as a LangGraph workflow. AstaBench expects solvers that implement the Inspect AI `@solver` interface. This package bridges the two: it imports the existing KRAKEN graph, adapts its input/output to the Inspect AI `TaskState` contract, and exposes a solver function that AstaBench can invoke.

## Requirements Trace

- R1. `uv sync` succeeds with editable install of `kestrel-backend`
- R2. `from kraken_solver.solver import kraken_discovery_solver` works
- R3. Smoke test passes (import, decorator, signature validation — no pipeline execution)
- R4. Solver can be referenced via `inspect eval --solver kraken_solver/solver.py:kraken_discovery_solver`
- R5. Do NOT modify `kraken-chatbot` — this repo only wraps it

## Scope Boundaries

- No cost tracking (the `model_usages` field doesn't exist on `DiscoveryState` yet)
- No custom scorers (Phase 4 work)
- No full pipeline execution — just the scaffold, imports, and solver structure
- No forking or copying asta-bench code — import from it

## Context & Research

### Relevant Code and Patterns

- `kestrel_backend.graph.builder.build_discovery_graph()` — takes no arguments, returns a compiled LangGraph `StateGraph`. Entry point for the pipeline.
- `kestrel_backend.graph.state.DiscoveryState` — `TypedDict(total=False)`. Key input fields: `raw_query` (str), `conversation_history` (list of tuples). Key output fields: `synthesis_report` (str), `hypotheses` (list[Hypothesis]).
- `astabench.util.model.record_model_usage_with_inspect` — the cost logging utility (deferred, not used yet).
- AstaBench solver pattern: `@solver` decorator, returns `async def solve(state: TaskState, generate: Generate) -> TaskState`. Output set via `state.output.completion`.
- `kestrel-backend` uses hatchling build system, packages from `src/kestrel_backend`, requires Python >=3.12.
- AstaBench pins `inspect_ai==0.3.114`.

### Key API Details Verified from Source

- `build_discovery_graph()` signature: no parameters, returns `workflow.compile()` (a compiled graph)
- Graph invocation: `await graph.ainvoke(initial_state)` where `initial_state` is a `DiscoveryState` dict
- `DiscoveryState["hypotheses"]` contains `list[Hypothesis]` — each has `.title`, `.claim`, `.tier`, `.supporting_entities`, `.structural_logic`, `.literature_support`
- `DiscoveryState["synthesis_report"]` is a plain string
- The `Hypothesis` model uses Pydantic `BaseModel` with `frozen=True`

## Key Technical Decisions

- **Build system: hatchling** — matches `kestrel-backend` convention
- **Package name `kraken-asta-solver`** — per task spec, distinct from the import path `kraken_solver`
- **Editable install of kestrel-backend via path dependency** — avoids forking, keeps solver in sync with upstream changes
- **Solver parameters deferred** — the `model` and `enable_literature_grounding` params from the sketch are placeholders. The graph currently takes no configuration. Include them as no-ops with TODO comments rather than omitting them, so the interface is ready when configuration support is added upstream.
- **Serialization via Pydantic `.model_dump()`** — `DiscoveryState` values are Pydantic `BaseModel` instances; `.model_dump()` handles recursive serialization to dicts

## Open Questions

### Resolved During Planning

- **Q: Does `build_discovery_graph()` accept arguments?** No — verified from `builder.py:74-180`. It returns `workflow.compile()` directly with no parameters.
- **Q: What's the correct import path?** `from kestrel_backend.graph.builder import build_discovery_graph` — verified, package root is `src/kestrel_backend` per hatch config.
- **Q: Which Inspect AI version?** AstaBench pins `0.3.114`. The solver package should pin the same to avoid version conflicts.

### Deferred to Implementation

- **Exact formatting of hypothesis output** — the `format_output_for_benchmark` function's output shape depends on what AstaBench scorers expect. Start with a reasonable text rendering and refine when custom scorers are built.
- **Whether `graph.ainvoke()` needs a config dict** — LangGraph's `ainvoke` accepts an optional `config` parameter. The current call should work without it, but implementation may reveal the need for runtime config (e.g., recursion limit).

## Implementation Units

- [x] **Unit 1: Package structure and pyproject.toml**

**Goal:** Create the package skeleton with correct build config and dependencies.

**Requirements:** R1

**Dependencies:** None

**Files:**
- Create: `pyproject.toml`
- Create: `src/kraken_solver/__init__.py`
- Create: `.env.example`

**Approach:**
- Use hatchling build system to match kestrel-backend
- Pin `inspect-ai==0.3.114` to match AstaBench
- Reference `kestrel-backend` as editable path dependency pointing to `../kraken-chatbot/backend`
- Include `langgraph` as a direct dep (used by kestrel-backend at runtime)
- Dev deps: `pytest`, `pytest-asyncio`
- `__init__.py` exports the solver for convenient import

**Patterns to follow:**
- `kraken-chatbot/backend/pyproject.toml` for hatchling config and package layout

**Test scenarios:**
- Happy path: `uv sync` completes without errors and `kestrel-backend` is importable

**Verification:**
- `uv sync` succeeds
- `python -c "import kraken_solver"` exits 0

---

- [x] **Unit 2: solver.py — Core solver wrapper**

**Goal:** Implement the Inspect AI solver that bridges `TaskState` to the KRAKEN graph.

**Requirements:** R2, R4, R5

**Dependencies:** Unit 1

**Files:**
- Create: `src/kraken_solver/solver.py`

**Approach:**
- Decorate with `@solver` from `inspect_ai.solver`
- Accept `model` and `enable_literature_grounding` as parameters with TODO comments noting they're not yet wired to the graph
- Inner `solve` function: build `DiscoveryState` from `state.input_text`, invoke `build_discovery_graph()`, format output into `state.output.completion`, attach serialized state to `state.metadata["kraken_state"]`
- Cost tracking section: leave as commented-out placeholder with TODO referencing the upstream `model_usages` work

**Patterns to follow:**
- AstaBench solver pattern from `astabench/evals/utils.py` — `@solver` returning `Solver` type, inner async function with `(state: TaskState, generate: Generate) -> TaskState` signature

**Test scenarios:**
- Happy path: solver function is importable and has the `@solver` decorator
- Happy path: solver can be referenced by path `kraken_solver/solver.py:kraken_discovery_solver`

**Verification:**
- `from kraken_solver.solver import kraken_discovery_solver` succeeds
- The function is recognized as a valid Inspect solver

---

- [x] **Unit 3: formatting.py — Output formatting helpers**

**Goal:** Implement helpers that convert KRAKEN's structured output into benchmark-compatible text and serializable dicts.

**Requirements:** R2 (supports solver output)

**Dependencies:** Unit 1

**Files:**
- Create: `src/kraken_solver/formatting.py`

**Approach:**
- `format_output_for_benchmark(synthesis_report: str, hypotheses: list) -> str` — renders the synthesis report and hypothesis list as structured text suitable for LLM-based scoring
- `serialize_kraken_state(final_state: dict) -> dict` — walks the `DiscoveryState` dict and calls `.model_dump()` on any Pydantic `BaseModel` instances, returning a JSON-serializable dict
- Keep formatting simple — text rendering of report + numbered hypotheses with claims and tiers

**Patterns to follow:**
- Pydantic serialization: use `model_dump()` (v2 API) not `dict()` (v1 deprecated)

**Test scenarios:**
- Happy path: `format_output_for_benchmark("report text", [])` returns a string containing the report text
- Edge case: `serialize_kraken_state({})` returns an empty dict without errors
- Edge case: `serialize_kraken_state` handles a mix of Pydantic models and plain values

**Verification:**
- Both functions are importable and handle empty inputs gracefully

---

- [x] **Unit 4: Smoke test**

**Goal:** Verify the solver is importable and structurally valid without running the full pipeline.

**Requirements:** R3

**Dependencies:** Units 1, 2, 3

**Files:**
- Create: `tests/test_solver_smoke.py`

**Approach:**
- Test that `kraken_discovery_solver` is importable
- Test that calling it returns a callable (the inner `solve` function)
- Test that formatting helpers handle degenerate inputs
- Do NOT attempt to invoke the full graph (requires DB, API keys, etc.)

**Patterns to follow:**
- `kestrel-backend/tests/` for pytest-asyncio conventions

**Test scenarios:**
- Happy path: `from kraken_solver.solver import kraken_discovery_solver` succeeds
- Happy path: `kraken_discovery_solver()` returns a callable
- Happy path: `format_output_for_benchmark("report", [])` returns a non-empty string
- Happy path: `serialize_kraken_state({})` returns `{}`
- Edge case: `serialize_kraken_state` with nested Pydantic model returns a plain dict

**Verification:**
- `uv run pytest tests/test_solver_smoke.py` passes

## System-Wide Impact

- **Interaction graph:** The solver imports from `kestrel_backend` but does not modify it. Changes to `DiscoveryState` fields or `build_discovery_graph()` signature upstream will require updates here.
- **Error propagation:** Graph execution errors from KRAKEN should propagate as-is — the solver does not add error handling beyond what the graph provides. Benchmark infrastructure handles solver failures.
- **Unchanged invariants:** `kraken-chatbot` is not modified. AstaBench framework is imported, not forked.

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| `kestrel-backend` editable install path is machine-specific (`../kraken-chatbot/backend`) | Document in README and `.env.example`. Configurable via `uv` workspace or env var in future. |
| Path dependency resolves through `Google Drive` (space in path) which may break `uv`/`pip` | Test `uv sync` early. If it fails, symlink kestrel-backend to a space-free path or use proper quoting in `pyproject.toml`. |
| `inspect-ai` version mismatch between solver and AstaBench | Pin to same version (`0.3.114`) in `pyproject.toml` |
| `build_discovery_graph()` signature changes upstream | Solver is thin wrapper — easy to update. Import path is verified. |

## Sources & References

- KRAKEN graph builder: `kraken-chatbot/backend/src/kestrel_backend/graph/builder.py`
- KRAKEN state schema: `kraken-chatbot/backend/src/kestrel_backend/graph/state.py`
- AstaBench README "Building an AstaBench Agent" section
- AstaBench cost logging: `astabench/util/model.py`
- Task description: `AGENT-TASK-solver-scaffold.md`
