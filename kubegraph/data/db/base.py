from abc import ABCMeta, abstractmethod
from typing import override

from pydantic.dataclasses import dataclass

from kubegraph.data.graph import NetworkGraph


@dataclass(eq=True, frozen=True)
class NetworkGraphRef:
    kind: str
    namespace: str

    @override
    def __repr__(self) -> str:
        return f'{self.kind} :: {self.namespace}'


class BaseNetworkGraphDB(metaclass=ABCMeta):
    @abstractmethod
    def list(
        self,
        kind: str | None = None,
        namespace: str | None = None,
    ) -> list[NetworkGraphRef]:
        pass

    @abstractmethod
    def load(
        self,
        kind: str,
        namespace: str | None = None,
    ) -> NetworkGraph:
        pass
