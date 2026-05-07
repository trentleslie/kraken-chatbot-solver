"""KRAKEN discovery pipeline as an Inspect AI solver."""

from inspect_ai.solver import Generate, Solver, TaskState, solver

from kestrel_backend.graph.builder import build_discovery_graph
from kestrel_backend.graph.state import DiscoveryState

from kraken_solver.formatting import format_output_for_benchmark, serialize_kraken_state


@solver
def kraken_discovery_solver(
    model: str = "anthropic/claude-sonnet-4-6",  # TODO: wire to graph when config support is added upstream
    enable_literature_grounding: bool = True,  # TODO: wire to graph when config support is added upstream
    **tool_options,
) -> Solver:
    """KRAKEN discovery pipeline as an Inspect solver."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        # 1. Build initial state from benchmark input
        initial_state: DiscoveryState = {
            "raw_query": state.input_text,
            "conversation_history": [],
        }

        # 2. Run the KRAKEN graph
        graph = build_discovery_graph()
        final_state = await graph.ainvoke(initial_state)

        # 3. Format output for benchmark scoring
        state.output.completion = format_output_for_benchmark(
            synthesis_report=final_state.get("synthesis_report", ""),
            hypotheses=final_state.get("hypotheses", []),
        )

        # 4. Preserve structured state for custom scorers
        state.metadata["kraken_state"] = serialize_kraken_state(final_state)

        # 5. Cost tracking
        # TODO: Add cost tracking once model_usages field is added to DiscoveryState upstream.
        # When available, iterate final_state["model_usages"] and call
        # record_model_usage_with_inspect() from astabench.util.model.

        return state

    return solve
