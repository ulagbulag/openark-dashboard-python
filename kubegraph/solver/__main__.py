import argparse
from pathlib import Path

from kubegraph.data.db.local import LocalNetworkGraphDB
from kubegraph.solver.ortools import OrToolsSolver


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--kind',
        default='warehouse',
        help='which kind to be analyzed',
        type=str,
    )
    parser.add_argument(
        '--namespace',
        default='optimization',
        help='which namespace to be analyzed',
        type=str,
    )
    parser.add_argument(
        '--save_dir',
        default='./outputs/',
        help='where to save outputs',
        type=Path,
    )
    parser.add_argument(
        '--show',
        action=argparse.BooleanOptionalAction,
        help='whether to display on the host machine',
        type=bool,
    )
    parser.add_argument(
        '--templates_dir',
        default='./templates/db/',
        help='where to load templates',
        type=Path,
    )
    args = parser.parse_args()

    # Init the minimum cost flow solver.
    db = LocalNetworkGraphDB(
        base_dir=str(args.templates_dir),
    )
    smcf = OrToolsSolver.with_scalar_network_graph(
        graph=db.load(
            kind=args.kind,
            namespace=args.namespace,
        ),
    )

    # Find the minimum cost flow.
    graph = smcf.solve()
    if graph is None:
        print('Optimization Failed')
        return

    print(f'Total cost = {graph.total_cost}')
    print()

    edges = graph.edges[['start', 'end', 'traffic', 'cost']]
    print(edges.filter(edges['traffic'] > 0))

    # Visualize graph
    graph.draw(
        base_dir=args.save_dir,
        show=args.show,
    )


if __name__ == '__main__':
    main()
