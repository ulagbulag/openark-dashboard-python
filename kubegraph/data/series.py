from abc import ABCMeta, abstractmethod
from typing import Generic, Optional, Self, TypeVar, override

import polars as pl
from pydantic import BaseModel

from kubegraph.data.graph import NetworkGraph

SqlResult = TypeVar('SqlResult')


class NetworkGraphSeriesMixin(BaseModel, Generic[SqlResult], metaclass=ABCMeta):
    timestamp: str
    step_unit: str

    @abstractmethod
    def __next__(self) -> Self:
        pass

    @abstractmethod
    def __sql__(self, query: str) -> SqlResult:
        pass

    def step(self, nstep: int = 1) -> Self:
        if nstep == 0:
            return self
        elif nstep < 0:
            raise ValueError('Negative step is not supported yet')

        series = self
        for _ in range(nstep):
            series = next(self)
        return series


class NetworkGraphSeries(
    NetworkGraph,
    NetworkGraphSeriesMixin[pl.LazyFrame],
):
    _ctx: Optional[pl.SQLContext] = None

    @override
    def __next__(self) -> Self:
        # TODO: to be implemented
        return self.model_copy()

    @override
    def __repr__(self) -> str:
        return 'NetworkGraphSeries(' \
            f'nodes={self.nodes.shape!r}, ' \
            f'edges={self.edges.shape!r}, ' \
            f'timestamp={self.timestamp!r}, ' \
            f'step_unit={self.step_unit!r})'

    @override
    def __sql__(self, query: str) -> pl.LazyFrame:
        if self._ctx is None:
            # Connect to database
            self._ctx = pl.SQLContext(
                frames={
                    'edges': self.edges,
                    'nodes': self.nodes,
                },
                register_globals=False,
            )

        return self._ctx.execute(
            query=query,
            eager=False,
        )
