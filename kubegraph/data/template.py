from typing import IO, Any, Iterable, Iterator, Literal, override

import jsonpointer
from pydantic import BaseModel, Field
import yaml

from utils.data import BaseTemplate


Value = bool | int | float


class NodeTemplate(BaseTemplate[dict[str, Value]]):
    spec: dict[str, Value] = {}

    @override
    @classmethod
    def _expected_kind(cls) -> str:
        return 'Node'


class _NodeGroupSamplesSpec(BaseModel):
    count: int = Field(default=1, ge=1)


class _NodeGroupValueNormalSpec(BaseModel):
    type: Literal['Normal']
    mean: int
    std: int = Field(default=1, gt=0)


class _NodeGroupValueStaticSpec(BaseModel):
    type: Literal['Static']
    value: Value


_NodeGroupValueType = _NodeGroupValueNormalSpec | _NodeGroupValueStaticSpec


class _NodeGroupSpec(BaseModel):
    samples: _NodeGroupSamplesSpec
    values: dict[str, _NodeGroupValueType] = Field(discriminator='type')


class NodeGroupTemplate(BaseTemplate[_NodeGroupSpec]):
    spec: _NodeGroupSpec

    @override
    @classmethod
    def _expected_kind(cls) -> str:
        return 'NodeGroup'


_Template = NodeTemplate | NodeGroupTemplate


def _get_template_type(obj: Any, /) -> type[_Template]:
    match jsonpointer.resolve_pointer(
        doc=obj,
        pointer='/kind',
    ):
        case 'Node':
            return NodeTemplate
        case 'NodeGroup':
            return NodeGroupTemplate
        case kind:
            raise ValueError(f'Unsupported template kind: {kind}')


def loads(obj: Any) -> _Template:
    return _get_template_type(obj).loads(
        obj=obj,
    )


def loads_all(templates: Iterable[Any]) -> Iterator[_Template]:
    return (
        loads(template)
        for template in templates
    )


def load_all(stream: IO) -> Iterator[_Template]:
    return loads_all(
        templates=yaml.safe_load_all(stream),
    )
