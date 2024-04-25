from typing import override

from pydantic import BaseModel

from kubegraph.data.db.base import NetworkGraphRef
from kubegraph.parser.base import BaseParser
from kubegraph.parser.retrieval import RetrievalParser


class AutoParser(BaseModel, BaseParser):
    retrival: RetrievalParser = RetrievalParser()

    @override
    def parse(
        self,
        datasets_annotations: dict[NetworkGraphRef, list[str]],
        question: str,
    ) -> list[NetworkGraphRef] | None:
        return self.retrival.parse(
            datasets_annotations=datasets_annotations,
            question=question,
        )
