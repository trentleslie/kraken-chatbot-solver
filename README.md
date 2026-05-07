# KRAKEN AstaBench Solver

KRAKEN discovery pipeline wrapped as an Inspect AI solver for AstaBench evaluation.

## Setup

```bash
cp .env.example .env
# Fill in API keys
uv sync
```

## Usage

```bash
uv run inspect eval --solver kraken_solver/solver.py:kraken_discovery_solver --model anthropic/claude-sonnet-4-6
```
