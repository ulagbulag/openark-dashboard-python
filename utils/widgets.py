from abc import ABCMeta, abstractmethod
from enum import Enum
import logging
import os
from typing import Any, Dict, Generic, List, Optional, Self, Tuple, TypeVar, override

import inflection
import jsonpointer
from pydantic import BaseModel, Field
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
import yaml

from dash.client import DashClient
from utils.actions import Actions
from utils.types import DataModel


_Assets = TypeVar('_Assets')
_BaseTemplateSpec = TypeVar('_BaseTemplateSpec')


class _TemplateRef(BaseModel):
    namespace: str
    name: str


class _BaseTemplate(_TemplateRef, Generic[_BaseTemplateSpec], metaclass=ABCMeta):
    title: str
    metadata: Dict[str, Any]
    spec: _BaseTemplateSpec

    @classmethod
    @abstractmethod
    def _expected_kind(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def _parse_metadata(
        cls,
        path: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        pass

    @classmethod
    @abstractmethod
    def _parse_spec(
        cls,
        spec: Dict[str, Any],
    ) -> _BaseTemplateSpec:
        pass

    @classmethod
    def _load(cls, path: str) -> Optional[Self]:
        filename, extension = os.path.splitext(os.path.split(path)[1])
        if extension != '.yaml':
            return None

        raw = yaml.safe_load(open(path, 'r'))

        api_version = jsonpointer.resolve_pointer(raw, '/apiVersion')
        assert isinstance(api_version, str), f'Template API version type mismatch: {
            path!r
        } -> {api_version}'
        assert api_version == 'ark.ulagbulag.io/v1alpha1', f'Unknown API version: {
            path!r
        }'

        kind = jsonpointer.resolve_pointer(raw, '/kind')
        assert isinstance(kind, str), f'Template kind type mismatch: {
            path!r
        } -> {kind}'
        assert kind == cls._expected_kind(), f'Unknown API Kind: {
            path!r
        } -> {kind}'

        name = jsonpointer.resolve_pointer(raw, '/metadata/name')
        assert isinstance(name, str), f'Template name type mismatch: {
            path!r
        } -> {name}'
        assert name == filename, f'Template name mismatch: {
            path!r
        } -> {name}'

        namespace = jsonpointer.resolve_pointer(
            raw,
            '/metadata/namespace',
            default='default',
        )
        assert isinstance(namespace, str), f'Template namespace type mismatch: {
            path!r
        } -> {namespace}'

        metadata = jsonpointer.resolve_pointer(
            raw,
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
            raw,
            '/spec',
            default={},
        )
        assert isinstance(spec, dict), f'Template spec type mismatch: {
            path!r
        } -> {spec}'

        return cls(
            namespace=namespace,
            name=name,
            metadata=metadata,
            title=title,
            spec=cls._parse_spec(spec),
            **kwargs,
        )

    @override
    def __str__(self) -> str:
        return self.title


class _ActionMetadataColumn(str, Enum):
    All = 'All'
    Current = 'Current'
    New = 'New'


class _ActionMetadataSpec(BaseModel):
    column: _ActionMetadataColumn = _ActionMetadataColumn.Current


class _ActionSpec(BaseModel):
    name: str
    kind: str
    metadata: _ActionMetadataSpec = _ActionMetadataSpec()
    spec: Dict[str, Any] = {}


class _WidgetSpec(BaseModel):
    actions: List[_ActionSpec] = []


class _WidgetTemplate(_BaseTemplate[_WidgetSpec]):
    page: Optional[str] = None

    @override
    @classmethod
    def _expected_kind(cls) -> str:
        return 'Widget'

    @override
    @classmethod
    def _parse_metadata(
        cls,
        path: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        page = jsonpointer.resolve_pointer(
            metadata,
            '/labels/dash.ulagbulag.io~1page',
            default=None,
        )
        assert page is None or isinstance(page, str), f'Template page type mismatch: {
            path!r
        } -> {page}'

        return dict(
            page=page,
        )

    @override
    @classmethod
    def _parse_spec(
        cls,
        spec: Dict[str, Any],
    ) -> _WidgetSpec:
        return _WidgetSpec.model_validate(
            obj=spec,
        )


class _PageSpec(BaseModel):
    pass


class PageTemplate(_BaseTemplate[_PageSpec]):
    priority: int = 1_000
    widgets: List[_WidgetTemplate] = []

    @override
    @classmethod
    def _expected_kind(cls) -> str:
        return 'Page'

    @override
    @classmethod
    def _parse_metadata(
        cls,
        path: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        priority_raw = jsonpointer.resolve_pointer(
            metadata,
            '/annotations/dash.ulagbulag.io~1priority',
            default=1_000,
        )
        assert isinstance(priority_raw, str), f'Template page priority type mismatch: {
            path!r
        } -> {priority_raw}'
        assert priority_raw.isdigit(), f'Template page priority mismatch: {
            path!r
        } -> {priority_raw}'
        priority = int(priority_raw)

        return dict(
            priority=priority,
        )

    @override
    @classmethod
    def _parse_spec(
        cls,
        spec: Dict[str, Any],
    ) -> _PageSpec:
        return _PageSpec.model_validate(
            obj=spec,
        )


class Widgets[_Assets]:
    def __init__(
        self,
        dash_client: DashClient,
        templates_dir: str,
    ) -> None:
        self._actions = Actions(
            path=f'{templates_dir}/actions',
        )
        self._dash_client = dash_client

        self._pages_map: Dict[Tuple[str, str], PageTemplate] = {}
        pages_dir = f'{templates_dir}/pages'
        for filename in os.listdir(pages_dir):
            filepath = f'{pages_dir}/{filename}'
            if os.path.isfile(filepath):
                page = PageTemplate._load(filepath)
                if page is not None:
                    namespace, name = page.namespace, page.name
                    self._pages_map[(namespace, name)] = page

        self._pages = sorted(
            self._pages_map.values(),
            key=lambda page: (page.priority, page.name),
        )

        self._widgets_map: Dict[Tuple[str, str], _WidgetTemplate] = {}
        widgets_dir = f'{templates_dir}/widgets'
        for filename in os.listdir(widgets_dir):
            filepath = f'{widgets_dir}/{filename}'
            if os.path.isfile(filepath):
                widget = _WidgetTemplate._load(filepath)
                if widget is not None:
                    namespace, name = widget.namespace, widget.name
                    self._widgets_map[(namespace, name)] = widget

        for widget in self._widgets_map.values():
            namespace, page = widget.namespace, widget.page
            if page is not None:
                self._pages_map[(namespace, page)].widgets.append(widget)
            else:
                logging.warning(
                    'Skipping registering widget: '
                    f'{widget.namespace}/{widget.name}',
                )

    @property
    def actions(self) -> Actions:
        return self._actions

    @property
    def dash_client(self) -> DashClient:
        return self._dash_client

    def get_home_page(
        self,
        namespace: Optional[str] = None,
    ) -> Optional[PageTemplate]:
        return self._pages_map.get((namespace or 'default', 'home'))

    def get_pages(self) -> List[PageTemplate]:
        return list(self._pages)

    async def render(
        self,
        assets: _Assets,
        namespace: str,
        name: str,
        columns: List[DeltaGenerator],
    ) -> Dict[str, Any]:
        template = self._widgets_map[(namespace, name)]
        actions = template.spec.actions

        session_name = f'/_page/session/{namespace}/{name}'
        session = _validate_session(
            session=st.session_state.get(session_name, {}),
        )

        if columns:
            column = columns.pop(0)
        else:
            column = st.container()

        for action_index, action_widget in enumerate(actions):
            action_name = action_widget.name
            action_kind_name = action_widget.kind
            action_kind = inflection.underscore(action_kind_name)

            action_is_first = action_index == 0
            action_metadata = action_widget.metadata

            action_module_path = \
                f'{os.path.dirname(__file__)}/..' \
                f'/actions/{action_kind}.py'
            if not os.path.exists(action_module_path):
                raise ValueError(
                    'No such action: '
                    f'{action_name} -> {action_kind_name}',
                )

            action_module = __import__(
                name=f'actions.{action_kind}',
                fromlist=['render'],
            )
            action_renderer = getattr(action_module, 'render')

            match action_metadata.column:
                case _ActionMetadataColumn.All:
                    action_column = st.container()
                case _ActionMetadataColumn.Current:
                    action_column = column
                case _ActionMetadataColumn.New:
                    if not action_is_first and columns:
                        action_column = column = columns.pop(0)
                    else:
                        action_column = column

            with action_column:
                updated_session = _validate_session(
                    session=await action_renderer(
                        assets=assets,
                        session=DataModel(
                            data=session,
                        ),
                        name=action_name,
                        spec=DataModel(
                            data=action_widget.spec,
                        ),
                    ),
                )
            session[action_name] = st.session_state[session_name] = updated_session

            state = updated_session.get('state', 'none')
            match state:
                case 'Ok':
                    continue
                case _:
                    break
        return session


def _validate_session(session: Any) -> Dict[str, Any]:
    if session is None:
        session = {}
    if not isinstance(session, dict):
        raise ValueError(
            'Expected session to be dict, '
            f'Found {str(type(session))}',
        )
    return session
