import glob
import os
from typing import List, Optional, override

import polars as pl
from pydantic import BaseModel

from kubegraph.data.db.base import BaseNetworkGraphDB, NetworkGraphRef
from kubegraph.data.graph import NetworkGraph


class LocalNetworkGraphDB(BaseModel, BaseNetworkGraphDB):
    base_dir: str = './templates/db/'

    @override
    def list(
        self,
        kind: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> List[NetworkGraphRef]:
        results = []
        for edge_file in glob.glob(r'templates/[0-9a-z-]*_[0-9a-z-]*/edges.csv'):
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
        namespace: Optional[str] = None,
    ) -> NetworkGraph:
        return NetworkGraph(
            # Define the directed graph for the flow.
            edges=pl.read_csv(f'{self.base_dir}/{kind}_{namespace}/edges.csv'),

            # Define an array of supplies at each node.
            nodes=pl.read_csv(f'{self.base_dir}/{kind}_{namespace}/nodes.csv'),
        )
