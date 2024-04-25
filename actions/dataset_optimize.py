import streamlit as st

from assets import Assets
from kubegraph.data.graph import NetworkGraph, OptimalNetworkGraph
from kubegraph.solver.ortools import OrToolsSolver
from utils.types import DataModel, SessionReturn


async def render(assets: Assets, session: DataModel, name: str, spec: DataModel) -> SessionReturn:
    graph = session.get(
        keys=spec,
        path='/key',
        value_type=NetworkGraph,
    )

    optimized_graph = _draw_optimize(
        name=name,
        graph=graph,
    )
    if optimized_graph is None:
        st.warning('Failed to optimize graph :(')
        return {
            'state': 'Empty',
        }

    return {
        'state': 'Ok',
        'value': optimized_graph,
    }


def _draw_optimize_network_flow(name: str, graph: NetworkGraph) -> OptimalNetworkGraph | None:
    smcf = OrToolsSolver.with_scalar_network_graph(graph)
    return smcf.solve()


def _draw_optimize(name: str, graph: NetworkGraph) -> OptimalNetworkGraph | None:
    # NOTE: Ordered
    actions = {
        'Network Flow': _draw_optimize_network_flow,
    }

    selected_action = st.selectbox(
        key=f'{name}',
        label='Choose one of optimizers',
        options=actions.keys(),
    )
    if selected_action is None:
        return st.stop()

    with st.spinner('🔥 Optimizing...'):
        return actions[selected_action](
            name=f'{name}/{selected_action}',
            graph=graph,
        )
