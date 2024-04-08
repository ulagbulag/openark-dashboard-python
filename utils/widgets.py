import os
from typing import Any

import inflection
import jsonpointer
import streamlit as st
import yaml

from dash.client import DashClient
from utils.actions import Actions


class Widgets:
    def __init__(self, path: str) -> None:
        self._actions = Actions(
            path=f'{path}/actions',
        )
        self._dash_client = DashClient()
        self._namespaces = {}
        self._templates = {}

        path = f'{path}/widgets'
        for filename in os.listdir(path):
            filepath = f'{path}/{filename}'
            if os.path.isfile(filepath):
                namespace, name, title, spec = _load_template(filepath)
                if spec is not None:
                    self._namespaces.setdefault(namespace, []).append(
                        (name, title),
                    )
                    self._templates[(namespace, name)] = spec

    @property
    def actions(self) -> Actions:
        return self._actions

    @property
    def dash_client(self) -> DashClient:
        return self._dash_client

    def get_names(self):
        return dict(self._namespaces)

    async def render(self, namespace: str, name: str, columns: list[Any]) -> None:
        template = self._templates[(namespace, name)]
        actions = template['actions']

        session = st.session_state.get('session', {})
        for action_widget in actions:
            action_name = action_widget['name']
            action_kind = inflection.underscore(action_widget['kind'])
            action_spec = action_widget.get('spec', {})

            action_metadata = action_widget.get('metadata', {})
            action_new_column = action_metadata.get('newColumn', False)

            action_module = __import__(
                name=f'actions.{action_kind}',
                fromlist=['render'],
            )
            action_renderer = getattr(action_module, 'render')

            if action_new_column:
                if columns:
                    action_column = columns.pop()
                    action_column.__enter__()
                else:
                    action_new_column = False

            updated_session = session[action_name] = st.session_state['session'] = await action_renderer(
                widgets=self,
                session=session,
                name=action_name,
                spec=action_spec,
            )

            if action_new_column:
                action_column.__exit__(None, None, None)

            state = updated_session.get('state', 'none')
            match state:
                case 'Ok':
                    continue
                case _:
                    break
        return session


def _load_template(path: str):
    filename, extension = os.path.splitext(os.path.split(path)[1])
    if extension != '.yaml':
        return '', '', None

    raw = yaml.safe_load(open(path, 'r'))

    api_version = jsonpointer.resolve_pointer(raw, '/apiVersion')
    assert api_version == 'ark.ulagbulag.io/v1alpha1', f'Unknown API version: {
        path!r
    }'

    kind = jsonpointer.resolve_pointer(raw, '/kind')
    assert kind == 'Widget', f'Unknown API Kind: {
        path!r
    } -> {name}'

    name = jsonpointer.resolve_pointer(raw, '/metadata/name')
    assert name == filename, f'Template name mismatch: {
        path!r
    } -> {name}'

    namespace = jsonpointer.resolve_pointer(
        raw,
        '/metadata/namespace',
        default='default',
    )

    title = jsonpointer.resolve_pointer(
        raw,
        '/metadata/annotations/dash.ulagbulag.io~1title',
        default=inflection.titleize(name),
    )

    spec = jsonpointer.resolve_pointer(raw, '/spec')
    return namespace, name, title, spec
