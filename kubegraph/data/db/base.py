from abc import ABCMeta, abstractmethod
from typing import List, Optional, override

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
        kind: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> List[NetworkGraphRef]:
        pass

    @abstractmethod
    def load(
        self,
        kind: str,
        namespace: Optional[str] = None,
    ) -> NetworkGraph:
        pass
