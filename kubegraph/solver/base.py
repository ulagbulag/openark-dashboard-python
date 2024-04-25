from abc import ABCMeta, abstractmethod
from typing import Self


class BaseSolver[ResultT](metaclass=ABCMeta):
    def __init__(self) -> None:
        pass

    @classmethod
    @abstractmethod
    def with_scalar_network_graph(cls, kind: str, namespace: str) -> Self:
        pass

    @abstractmethod
    def solve(self) -> ResultT:
        pass
