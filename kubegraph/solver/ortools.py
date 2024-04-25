from typing import Self, override

import numpy as np
from ortools.graph.python import min_cost_flow
import polars as pl

from kubegraph.data.graph import NetworkGraph, OptimalNetworkGraph
from kubegraph.solver.base import BaseSolver


class OrToolsSolver(BaseSolver[OptimalNetworkGraph | None]):
    def __init__(
        self,
        graph: NetworkGraph,
        solver: min_cost_flow.SimpleMinCostFlow,
    ) -> None:
        super(BaseSolver, self).__init__()
        self._graph = graph
        self._solver = solver

    @override
    @classmethod
    def with_scalar_network_graph(  # noqa: C901
        cls,
        graph: NetworkGraph,
    ) -> Self:
        solver = min_cost_flow.SimpleMinCostFlow()

        # Simulate node supplies

        def simulate_supply(args: tuple[int, float]) -> int:
            mean, std = args
            if std <= 0:
                return mean
            return max(int(np.random.normal(mean, std)), 0)

        supply = graph.nodes[['traffic', 'std']] \
            .map_rows(simulate_supply) \
            .get_columns()[-1] \
            .alias('supply')

        graph = graph.model_copy()
        graph.nodes = _update_column(
            df=graph.nodes,
            key='supply',
            values=supply,
        )

        max_supply = graph.nodes.get_column('supply').abs().sum()

        # Check special nodes
        has_start_node = '__START__' in graph.nodes.get_column('name')
        has_end_node = '__END__' in graph.nodes.get_column('name')

        # Add special edges
        special_edges = []
        if not has_start_node:
            special_edges.append(pl.DataFrame([
                {
                    'start': '__START__',
                    'end': node,
                    'capacity': 0,
                    'cost': 0,
                }
                for node in graph.nodes.get_column('name')
            ]))
        if not has_end_node:
            special_edges.append(pl.DataFrame([
                {
                    'start': node,
                    'end': '__END__',
                    'capacity': max_supply,
                    'cost': cost,
                }
                for (node, cost) in graph.nodes.rows_by_key(('name', 'cost'))
            ]))
        if special_edges:
            graph.edges = pl.concat(
                items=[
                    graph.edges,
                    *special_edges,
                ],
                how='align',
            )

        # Add special nodes
        special_nodes = []
        if not has_start_node:
            special_nodes.append({
                'name': '__START__',
                'traffic': 0,
                'cost': 0,
                'std': 0,
                'supply': 0,
            })
        if not has_end_node:
            special_nodes.append({
                'name': '__END__',
                'traffic': -max_supply,
                'cost': 0,
                'std': 0,
                'supply': -max_supply,
            })
        if special_nodes:
            graph.nodes = pl.concat(
                items=[
                    graph.nodes,
                    pl.DataFrame(special_nodes),
                ],
                how='diagonal',
            )

        if 'id' not in graph.nodes.columns:
            graph.nodes = graph.nodes.with_row_index('id')

        def select_id(key: str) -> pl.Series:
            return graph.edges.join(
                other=graph.nodes,
                left_on=key,
                right_on='name',
                how='left',
            )['id']

        # Add each arc.
        solver.add_arcs_with_capacity_and_unit_cost(
            select_id('start'),  # type: ignore
            select_id('end'),  # type: ignore
            graph.edges['capacity'],  # type: ignore
            graph.edges['cost'],  # type: ignore
        )

        # Add node supplies.
        solver.set_nodes_supplies(
            graph.nodes['id'],  # type: ignore
            graph.nodes['supply'],  # type: ignore
        )

        return cls(
            graph=graph,
            solver=solver,
        )

    @override
    def solve(self) -> OptimalNetworkGraph | None:
        status = self._solver.solve_max_flow_with_min_cost()

        if status != self._solver.OPTIMAL:
            return None

        num_nodes = len(self._graph.nodes) - 2
        node_gains = np.zeros(
            shape=num_nodes,
            dtype=np.uint64,
        )
        node_losses = np.zeros(
            shape=num_nodes,
            dtype=np.uint64,
        )

        def collect_edges() -> pl.DataFrame:
            items = []
            for arc in range(self._solver.num_arcs()):
                edge = dict(zip(
                    self._graph.edges.columns,
                    self._graph.edges.row(arc),
                ))
                if edge['start'] == '__START__' or edge['end'] == '__END__':
                    continue

                cost = self._solver.unit_cost(arc)
                traffic = self._solver.flow(arc)

                node_losses[self._solver.tail(arc)] += traffic
                node_gains[self._solver.head(arc)] += traffic

                items.append({
                    **edge,
                    'cost': cost,
                    'traffic': traffic,
                })
            return pl.DataFrame(items)

        def collect_nodes() -> pl.DataFrame:
            nodes = self._graph.nodes.clone() \
                .drop(('id', 'supply')) \
                .slice(0, num_nodes)

            # NOTE: Ordered
            nodes = _update_column(
                df=nodes,
                key='loss',
                values=node_losses,
            )
            nodes = _update_column(
                df=nodes,
                key='gain',
                values=node_gains,
            )
            return nodes

        return OptimalNetworkGraph(
            edges=collect_edges(),
            nodes=collect_nodes(),
            total_cost=self._solver.optimal_cost(),
        )


def _update_column(
    df: pl.DataFrame,
    key: str,
    values: np.ndarray | pl.Series,
) -> pl.DataFrame:
    if isinstance(values, np.ndarray):
        values = pl.Series(
            name=key,
            values=values,
        )

    if key in df.columns:
        return df.replace_column(
            index=df.get_column_index(key),
            column=values,
        )
    else:
        return df.insert_column(
            index=len(df.columns),
            column=values,
        )
