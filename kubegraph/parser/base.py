from abc import ABCMeta, abstractmethod

from kubegraph.data.db.base import NetworkGraphRef


class BaseParser(metaclass=ABCMeta):
    @abstractmethod
    def parse(
        self,
        datasets_annotations: dict[NetworkGraphRef, list[str]],
        question: str,
    ) -> list[NetworkGraphRef] | None:
        pass
