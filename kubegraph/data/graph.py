from enum import Enum
from io import BytesIO
import json
import os
from pathlib import Path
from tarfile import TarFile, TarInfo
from typing import IO, Any, Self, override
import uuid

import graphviz
import polars as pl
from pydantic import BaseModel
import pyvis
import matplotlib
import matplotlib.figure
import matplotlib.pyplot as plt
import networkx as nx
import streamlit as st
from streamlit.runtime import exists as _is_streamlit_running

# Load environment variables
_HAS_DISPLAY = 'DISPLAY' in os.environ
_IS_STREAMLIT_RUNNING = _is_streamlit_running()

# Load matplotlib backend
if _HAS_DISPLAY:
    # options: [GTK3Agg, GTK3Cairo]
    matplotlib.use(os.environ.get('MPLBACKEND', 'GTK3Agg'))


class NetworkGraphDrawBackend(Enum):
    Matplotlib = 'matplotlib'
    Pyvis = 'pyvis'

    @classmethod
    def default(cls) -> 'NetworkGraphDrawBackend':
        return cls.Matplotlib


class NetworkGraph(BaseModel, arbitrary_types_allowed=True):
    id: uuid.UUID = uuid.uuid4()
    edges: pl.DataFrame
    nodes: pl.DataFrame

    def __eq__(self, other: Self) -> bool:
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def load(
        cls,
        fileobj: str | Path | IO[bytes],
    ) -> Self:
        archive = TarFile(
            fileobj=fileobj,  # type: ignore
            mode='r',
        )
        this = cls(
            edges=_load_dataframe(
                archive=archive,
                name='edges',
            ),
            nodes=_load_dataframe(
                archive=archive,
                name='nodes',
            ),
        )
        archive.close()

        return this

    def dump(
        self,
        fileobj: str | Path | IO[bytes],
    ) -> None:
        archive = TarFile(
            fileobj=fileobj,  # type: ignore
            mode='w',
        )
        self._dump_to(archive)
        archive.close()

    def _dump_to(
        self,
        archive: TarFile,
    ) -> None:
        _dump_dataframe(
            archive=archive,
            name='edges',
            df=self.edges,
        )
        _dump_dataframe(
            archive=archive,
            name='nodes',
            df=self.nodes,
        )

    def dumps(self) -> BytesIO:
        buffer = BytesIO()
        self.dump(buffer)
        return buffer

    def is_geolocational(self) -> bool:
        return 'latitude' in self.nodes.columns and 'longitude' in self.nodes.columns

    def draw(
        self,
        backend: NetworkGraphDrawBackend | str | None = None,
        base_dir: Path | str | None = None,
        show: bool = True,
    ) -> matplotlib.figure.Figure | pyvis.network.Network:
        if backend is None:
            backend = NetworkGraphDrawBackend.default()
        elif isinstance(backend, str):
            backend = NetworkGraphDrawBackend(backend)

        if base_dir is not None:
            os.makedirs(base_dir, exist_ok=True)

        match backend:
            case NetworkGraphDrawBackend.Matplotlib:
                return self.draw_with_matplotlib(base_dir=base_dir, show=show)
            case NetworkGraphDrawBackend.Pyvis:
                return self.draw_with_pyvis(base_dir=base_dir, show=show)
            case _:
                raise Exception(f'Unknown backend type: {backend}')

    def draw_with_matplotlib(
        self,
        base_dir: Path | str | None = None,
        show: bool = True,
    ) -> matplotlib.figure.Figure:
        G = self.to_networkx()

        elarge = [(u, v)
                  for (u, v, d) in G.edges(data=True) if d['weight'] >= 1 and u != '__START__' and v != '__START__']
        esmall = [(u, v)
                  for (u, v, d) in G.edges(data=True) if d['weight'] < 1 and u != '__START__' and v != '__START__']

        # positions for all nodes - seed for reproducibility
        pos = nx.circular_layout(G)

        # nodes
        nx.draw_networkx_nodes(G, pos, nodelist=[n for n in G.nodes(
        ) if n != '__START__'], node_size=700)

        # edges
        nx.draw_networkx_edges(G, pos, edgelist=elarge,
                               width=6, arrows=True, arrowsize=20, arrowstyle='->',)
        nx.draw_networkx_edges(
            G, pos, edgelist=esmall, width=6, alpha=0.5, edge_color='b', style='dashed', arrows=True, arrowsize=20, arrowstyle='->',
        )

        # node labels
        nx.draw_networkx_labels(G, pos, font_size=20, font_family='sans-serif')
        # edge weight labels
        edge_labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels)

        fig, ax = plt.subplots()
        ax.margins(0.08)
        ax.axis('off')
        ax.axis('off')
        fig.tight_layout()

        if base_dir is not None:
            fig.savefig(f'{base_dir}/output.png')

        if show:
            # NOTE: Ordered
            if _IS_STREAMLIT_RUNNING:
                st.write(fig)
            elif _HAS_DISPLAY:
                fig.show()

        return fig

    def draw_with_pyvis(
        self,
        base_dir: Path | str | None = None,
        show: bool = True,
    ) -> pyvis.network.Network:
        net = pyvis.network.Network()
        net.add_nodes(
            self.nodes.rows_by_key(('name',)),
        )
        # net.add_edges(
        #     self.edges.rows_by_key(('start', 'end', 'traffic')),
        # )
        net.add_edges(
            self.edges.rows_by_key(('start', 'end')),
        )

        if base_dir is not None and show:
            iframe = net.show(f'{base_dir}/output.html', notebook=False)
            if _IS_STREAMLIT_RUNNING:
                st.write(iframe)
        return net

    def to_graphviz(self) -> graphviz.Digraph:
        net = graphviz.Digraph()

        # Add edges
        STOP_WORDS = ['__START__', '__END__']
        has_traffic = 'traffic' in self.edges.columns
        for start, end, capacity, *traffic in self.edges.rows_by_key((
            'start',
            'end',
            'capacity',
            'traffic',
        )):
            if start in STOP_WORDS or end in STOP_WORDS:
                continue

            if not traffic:
                traffic = capacity
            else:
                traffic = traffic[0]

            is_full = capacity <= traffic
            is_overheat = capacity * 0.5 <= traffic
            is_moderate = capacity * 0.2 <= traffic
            is_empty = capacity <= 0

            if is_empty:
                continue

            net.edge(
                tail_name=start,
                head_name=end,
                label=f'{traffic}/{capacity}' if has_traffic else str(traffic),
                # attributes
                color=(
                    'red' if is_full else (
                        'orange' if is_overheat else (
                            'yellow' if is_moderate else 'yellowgreen'
                        )
                    )
                ) if has_traffic else 'black',
                style='solid' if has_traffic else 'dashed',
            )

        # Add nodes
        has_traffic = 'loss' in self.nodes.columns and 'gain' in self.nodes.columns
        for name, traffic, *io in self.nodes.rows_by_key((
            'name',
            'traffic',
            'loss',
            'gain',
        )):
            if name in STOP_WORDS:
                continue

            if len(io) == 2:
                [loss, gain] = io
            else:
                loss = gain = 0

            if has_traffic and max(loss, gain) == 0:
                continue

            net.node(
                name=name,
                label=f'{name} <-{loss}/+{gain}={gain -
                                                 loss}>' if has_traffic else name,
                # attributes
                color=(
                    'red' if loss < gain else 'blue'
                ) if has_traffic else 'black',
            )

        return net

    def to_networkx(self) -> nx.Graph:
        net = nx.Graph()
        net.add_weighted_edges_from(
            self.edges.rows_by_key(('start', 'end', 'traffic')),
        )
        net.add_nodes_from(
            self.nodes.rows_by_key(('name',)),
        )
        return net


class OptimalNetworkGraph(NetworkGraph):
    total_cost: int

    @override
    @classmethod
    def load(
        cls,
        fileobj: str | Path | IO[bytes],
    ) -> Self:
        archive = TarFile(
            fileobj=fileobj,  # type: ignore
            mode='r',
        )
        this = cls(
            edges=_load_dataframe(
                archive=archive,
                name='edges',
            ),
            nodes=_load_dataframe(
                archive=archive,
                name='nodes',
            ),
            **_load_json(
                archive=archive,
                name='optimization.json',
            )
        )
        archive.close()

        return this

    @override
    def _dump_to(
        self,
        archive: TarFile,
    ) -> None:
        super()._dump_to(archive)

        _dump_json(
            archive=archive,
            name='optimization',
            data={
                'cost': self.total_cost,
            },
        )


def _load_dataframe(
    archive: TarFile,
    name: str,
) -> pl.DataFrame:
    buffer = archive.extractfile(f'{name}.parquet')
    if buffer is None:
        raise ValueError(f'Empty {name} data')
    return pl.read_parquet(buffer)


def _load_json(
    archive: TarFile,
    name: str,
) -> Any:
    buffer = archive.extractfile(f'{name}.json')
    if buffer is None:
        raise ValueError(f'Empty {name} data')
    return json.load(buffer)


def _dump_dataframe(
    archive: TarFile,
    name: str,
    df: pl.DataFrame,
) -> None:
    buffer = BytesIO()
    df.write_parquet(buffer, compression='uncompressed')
    buffer.seek(0)

    info = TarInfo(f'{name}.parquet')
    info.size = buffer.getbuffer().nbytes

    archive.addfile(info, buffer)


def _dump_json(
    archive: TarFile,
    name: str,
    data: Any,
) -> None:
    value = json.dumps(data).encode('utf-8')
    buffer = BytesIO(value)

    info = TarInfo(f'{name}.json')
    info.size = buffer.getbuffer().nbytes

    archive.addfile(info, buffer)
