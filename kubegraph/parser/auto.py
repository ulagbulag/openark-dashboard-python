from typing import Dict, List, Optional, override

from pydantic import BaseModel

from kubegraph.data.db.base import NetworkGraphRef
from kubegraph.parser.base import BaseParser
from kubegraph.parser.retrieval import RetrievalParser


class AutoParser(BaseModel, BaseParser):
    retrival: RetrievalParser = RetrievalParser()

    @override
    def parse(
        self,
        datasets_annotations: Dict[NetworkGraphRef, List[str]],
        question: str,
    ) -> Optional[List[NetworkGraphRef]]:
        return self.retrival.parse(
            datasets_annotations=datasets_annotations,
            question=question,
        )
