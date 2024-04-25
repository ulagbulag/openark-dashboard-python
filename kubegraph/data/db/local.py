import glob
import os
from typing import override

import polars as pl
from pydantic import BaseModel

from kubegraph.data.db.base import BaseNetworkGraphDB, NetworkGraphRef
from kubegraph.data.graph import NetworkGraph


class LocalNetworkGraphDB(BaseModel, BaseNetworkGraphDB):
    base_dir: str = './templates/db/'

    @override
    def list(
        self,
        kind: str | None = None,
        namespace: str | None = None,
    ) -> list[NetworkGraphRef]:
        edges_filter = rf'{self.base_dir}/[0-9a-z-]*_[0-9a-z-]*/edges.csv'

        results = []
        for edge_file in glob.glob(edges_filter):
            template_dir = os.path.dirname(edge_file)
            node_file = f'{template_dir}/nodes.csv'
            if os.path.exists(node_file):
                kind, namespace = os.path.basename(template_dir).split('_')
                results.append(NetworkGraphRef(
                    kind=kind,
                    namespace=namespace,
                ))
        return results

    @override
    def load(
        self,
        kind: str,
        namespace: str | None = None,
    ) -> NetworkGraph:
        return NetworkGraph(
            # Define the directed graph for the flow.
            edges=pl.read_csv(f'{self.base_dir}/{kind}_{namespace}/edges.csv'),

            # Define an array of supplies at each node.
            nodes=pl.read_csv(f'{self.base_dir}/{kind}_{namespace}/nodes.csv'),
        )
