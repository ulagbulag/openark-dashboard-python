from abc import ABCMeta, abstractmethod
from inspect import isclass
import os
from types import GenericAlias
from typing import Any, Self, override

import inflection
import jsonpointer
from pydantic import BaseModel, Field
import yaml


class ResourceRef(BaseModel):
    namespace: str = 'default'
    name: str


class BaseTemplate[BaseSpec](BaseModel, metaclass=ABCMeta):
    apiVersion: str
    kind: str

    ref: ResourceRef = Field(exclude=True)

    title: str = Field(exclude=True)
    metadata: dict[str, Any]
    spec: BaseSpec

    @classmethod
    def _spec_type(cls) -> type[BaseSpec]:
        if 'spec' not in cls.__annotations__:
            raise ValueError('No spec type defined.')
        return cls.__annotations__['spec']

    @classmethod
    @abstractmethod
    def _expected_kind(cls) -> str:
        pass

    @classmethod
    def _parse_metadata(
        cls,
        path: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return {}

    @classmethod
    def _parse_spec(
        cls,
        spec: dict[str, Any],
    ) -> BaseSpec:
        spec_type = cls._spec_type()
        if isclass(spec_type) and issubclass(spec_type, BaseModel):
            return spec_type.model_validate(
                obj=spec,
            )  # type: ignore
        elif isinstance(spec_type, GenericAlias) and issubclass(spec_type.__origin__, dict):
            return spec  # type: ignore
        else:
            raise ValueError('Spec type should be dict')

    @classmethod
    def load(cls, path: str) -> Self | None:
        filename, extension = os.path.splitext(os.path.split(path)[1])
        if extension != '.yaml':
            return None

        return cls.loads(
            obj=yaml.safe_load(open(path, 'r')),
            filename=filename,
            path=path,
        )

    @classmethod
    def loads(
        cls,
        obj: Any,
        *,
        filename: str | None = None,
        path: str = '__input__',
    ) -> Self:
        api_version = jsonpointer.resolve_pointer(obj, '/apiVersion')
        assert isinstance(api_version, str), f'Template API version type mismatch: {
            path!r
        } -> {api_version}'
        assert api_version == 'ark.ulagbulag.io/v1alpha1', f'Unknown API version: {
            path!r
        }'

        kind = jsonpointer.resolve_pointer(obj, '/kind')
        assert isinstance(kind, str), f'Template kind type mismatch: {
            path!r
        } -> {kind}'
        assert kind == cls._expected_kind(), f'Unknown API Kind: {
            path!r
        } -> {kind}'

        name = jsonpointer.resolve_pointer(obj, '/metadata/name')
        assert isinstance(name, str), f'Template name type mismatch: {
            path!r
        } -> {name}'
        if filename is not None:
            assert name == filename, f'Template name mismatch: {
                path!r
            } -> {name}'

        namespace = jsonpointer.resolve_pointer(
            obj,
            '/metadata/namespace',
            default='default',
        )
        assert isinstance(namespace, str), f'Template namespace type mismatch: {
            path!r
        } -> {namespace}'

        metadata = jsonpointer.resolve_pointer(
            obj,
            '/metadata',
            default={},
        )
        assert isinstance(metadata, dict), f'Template metadata type mismatch: {
            path!r
        }'

        title = jsonpointer.resolve_pointer(
            metadata,
            '/annotations/dash.ulagbulag.io~1title',
            default=inflection.titleize(name),
        )
        assert isinstance(title, str), f'Template title type mismatch: {
            path!r
        } -> {title}'

        kwargs = cls._parse_metadata(
            path=path,
            metadata=metadata,
        )

        spec = jsonpointer.resolve_pointer(
            obj,
            '/spec',
            default={},
        )
        assert isinstance(spec, dict), f'Template spec type mismatch: {
            path!r
        } -> {spec}'

        return cls(
            apiVersion=api_version,
            kind=kind,
            ref=ResourceRef(
                namespace=namespace,
                name=name,
            ),
            metadata=metadata,
            title=title,
            spec=cls._parse_spec(spec),
            **kwargs,
        )

    @property
    def name(self) -> str:
        return self.ref.name

    @property
    def namespace(self) -> str:
        return self.ref.namespace

    @override
    def __str__(self) -> str:
        return self.title
