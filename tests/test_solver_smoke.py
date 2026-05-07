"""Smoke tests for the KRAKEN solver scaffold.

Verifies the solver is importable and structurally valid without
running the full pipeline (which requires DB, API keys, etc.).
"""

from pydantic import BaseModel


def test_solver_importable():
    """The solver function can be imported."""
    from kraken_solver.solver import kraken_discovery_solver

    assert kraken_discovery_solver is not None


def test_solver_returns_callable():
    """Calling the solver factory returns a callable (the inner solve function)."""
    from kraken_solver.solver import kraken_discovery_solver

    solve_fn = kraken_discovery_solver()
    assert callable(solve_fn)


def test_package_reexports_solver():
    """The package __init__.py re-exports the solver."""
    from kraken_solver import kraken_discovery_solver

    assert kraken_discovery_solver is not None


def test_format_output_empty_hypotheses():
    """format_output_for_benchmark handles empty hypotheses list."""
    from kraken_solver.formatting import format_output_for_benchmark

    result = format_output_for_benchmark("report text", [])
    assert isinstance(result, str)
    assert "report text" in result


def test_format_output_empty_report():
    """format_output_for_benchmark handles empty report."""
    from kraken_solver.formatting import format_output_for_benchmark

    result = format_output_for_benchmark("", [])
    assert isinstance(result, str)


def test_serialize_empty_state():
    """serialize_kraken_state handles empty dict."""
    from kraken_solver.formatting import serialize_kraken_state

    result = serialize_kraken_state({})
    assert result == {}


def test_serialize_plain_values():
    """serialize_kraken_state passes through plain values."""
    from kraken_solver.formatting import serialize_kraken_state

    state = {"raw_query": "test", "errors": ["err1"]}
    result = serialize_kraken_state(state)
    assert result == {"raw_query": "test", "errors": ["err1"]}


def test_serialize_pydantic_model():
    """serialize_kraken_state converts Pydantic models to dicts."""
    from kraken_solver.formatting import serialize_kraken_state

    class SampleModel(BaseModel):
        name: str
        value: int

    state = {"model": SampleModel(name="test", value=42)}
    result = serialize_kraken_state(state)
    assert result == {"model": {"name": "test", "value": 42}}


def test_serialize_nested_pydantic_in_list():
    """serialize_kraken_state handles Pydantic models inside lists."""
    from kraken_solver.formatting import serialize_kraken_state

    class Inner(BaseModel):
        x: int

    state = {"items": [Inner(x=1), Inner(x=2)]}
    result = serialize_kraken_state(state)
    assert result == {"items": [{"x": 1}, {"x": 2}]}
