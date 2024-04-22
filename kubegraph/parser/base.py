from abc import ABCMeta, abstractmethod
from typing import Dict, List, Optional

from kubegraph.data.db.base import NetworkGraphRef


class BaseParser(metaclass=ABCMeta):
    @abstractmethod
    def parse(
        self,
        datasets_annotations: Dict[NetworkGraphRef, List[str]],
        question: str,
    ) -> Optional[List[NetworkGraphRef]]:
        pass
