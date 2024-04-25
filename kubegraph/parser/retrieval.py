from abc import ABCMeta, abstractmethod
import logging
import os
from typing import override

from langchain_community.llms.huggingface_endpoint import HuggingFaceEndpoint
from langchain_community.vectorstores.docarray import DocArrayInMemorySearch
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages.base import BaseMessage
from langchain_core.output_parsers import BaseTransformOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableSerializable
from langchain_core.vectorstores import VectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel

from kubegraph.data.db.base import NetworkGraphRef
from kubegraph.parser.base import BaseParser


class BaseVectorStoreBuilder(BaseModel, metaclass=ABCMeta):
    @abstractmethod
    def build(
        self,
        datasets_annotations: dict[NetworkGraphRef, list[str]],
    ) -> VectorStore:
        pass


class InMemoryVectorStoreBuilder(BaseVectorStoreBuilder, metaclass=ABCMeta):
    _embedding: Embeddings | None = None

    def embedding(self) -> Embeddings:
        if self._embedding is None:
            self._embedding = self._load_embedding()
        return self._embedding

    @abstractmethod
    def _load_embedding(self) -> Embeddings:
        pass

    @override
    def build(
        self,
        datasets_annotations: dict[NetworkGraphRef, list[str]],
    ) -> VectorStore:
        return DocArrayInMemorySearch.from_texts(
            [
                annotation
                for annotations in datasets_annotations.values()
                for annotation in annotations
            ],
            embedding=self.embedding(),
        )


class OpenAIVectorStoreBuilder(InMemoryVectorStoreBuilder):
    model: str = 'text-embedding-ada-002'

    @override
    def _load_embedding(self) -> Embeddings:
        return OpenAIEmbeddings(
            model=self.model,
        )


class RetrievalParser(BaseModel, BaseParser):
    lm: BaseLanguageModel[BaseMessage] | BaseLanguageModel[str] | None = None

    output_parser: BaseTransformOutputParser[str] = StrOutputParser()

    prompt: ChatPromptTemplate = ChatPromptTemplate.from_template(
        template=r'''Print dataset numbers that can explain or solve the given question.

        Datasets:
        {context}

        Answering Rule:
        1. Do not print any explanation.
        2. Do not print any note, questions, comment like "(As a AI, ...)", etc.
        3. If datasets are matched: Print like "Answer: 42", "Answer: 42, 94, 172", etc.
        4. If no dataset is matched: Print only "Answer: Not Found".

        Question: {question}
        ''',
    )

    vectorstore: BaseVectorStoreBuilder = OpenAIVectorStoreBuilder()

    _logger: logging.Logger = logging.getLogger('kubegraph')

    def _load_lm(self) -> BaseLanguageModel[str] | BaseLanguageModel[BaseMessage]:
        if self.lm is None:
            try:
                self.lm = HuggingFaceEndpoint(
                    endpoint_url=f"http://text-generation/",
                    huggingfacehub_api_token=os.environ['HUGGING_FACE_HUB_TOKEN'],
                    # max_new_tokens=512,
                    temperature=0.1,
                    # top_k=10,
                    # top_p=0.95,
                    # typical_p=0.95,
                    # streaming=True,
                )  # type: ignore
            except ValueError:
                pass
        if self.lm is None:
            try:
                self.lm = ChatOpenAI(
                    model='gpt-4-turbo',
                    temperature=0.0,
                )
            except ValueError:
                pass
        if self.lm is None:
            raise ValueError('Failed to initialize LLM')
        return self.lm

    def build_chain(
        self,
        datasets_annotations: dict[NetworkGraphRef, list[str]],
    ) -> RunnableSerializable[str, str]:
        vectorstore = self.vectorstore.build(
            datasets_annotations=datasets_annotations,
        )
        retriever = vectorstore.as_retriever()

        setup_and_retrieval = RunnableParallel({
            'context': retriever,
            'question': RunnablePassthrough(),
        })

        return setup_and_retrieval | self.prompt | self._load_lm() | self.output_parser

    @override
    def parse(
        self,
        datasets_annotations: dict[NetworkGraphRef, list[str]],
        question: str,
    ) -> list[NetworkGraphRef] | None:
        chain = self.build_chain(datasets_annotations)
        datasets = list(datasets_annotations.keys())

        answer = chain.invoke(question)
        self._logger.info(
            f'Question: {question}, '
            f'{answer.replace('\n', ' ').strip()}',
        )

        for answer_line in answer.split('\n'):
            answer_line = answer_line.strip()

            PROMPT = r'Response: '
            if answer_line.startswith(PROMPT):
                answer_line = answer_line[len(PROMPT):]

            PROMPT = r'Answer: '
            if answer_line.startswith(PROMPT):
                maybe_indices = answer_line.split(PROMPT)[-1]

                indices: list[int] = []
                for maybe_index in maybe_indices.split(','):
                    maybe_index = maybe_index.strip()
                    if not maybe_index.isnumeric():
                        continue
                    index = int(maybe_index)
                    if index >= len(datasets):
                        continue
                    indices.append(index)

                if not indices:
                    return None

                return [
                    datasets[index]
                    for index in indices
                ]
