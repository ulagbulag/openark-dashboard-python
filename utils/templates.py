import os
from typing import Any, Dict

import inflection
import jinja2
import streamlit as st
import yaml

from dash.client import DashClient


Session = Dict[str, Any]
Spec = Dict[str, Any]


class Templates:
    def __init__(self, path: str = './templates') -> None:
        self._dash_client = DashClient()
        self._env = jinja2.Environment(
            enable_async=True,
        )
        self._namespaces = {}
        self._templates = {}

        for filename in os.listdir(path):
            filepath = f'{path}/{filename}'
            if os.path.isfile(filepath):
                namespace, name, spec = _load_template(filepath)
                if spec is not None:
                    self._namespaces.setdefault(namespace, []).append(name)
                    self._templates[(namespace, name)] = spec

    @property
    def dash_client(self) -> DashClient:
        return self._dash_client

    def get_names(self):
        return dict(self._namespaces)

    async def render(self, namespace: str, name: str, columns: list[str]) -> None:
        template = self._templates[(namespace, name)]
        actions = template['actions']

        session = st.session_state.get('session', {})
        for action in actions:
            action_template = self._env.from_string(yaml.dump(action))
            action_widget = yaml.safe_load(await action_template.render_async(**session))

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
                templates=self,
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

    api_version = raw['apiVersion']
    assert api_version == 'ark.ulagbulag.io/v1alpha1', f'Unknown API version: {
        path!r
    }'

    kind = raw['kind']
    assert kind == 'Widget', f'Unknown API Kind: {
        path!r
    } -> {name}'

    name = raw['metadata']['name']
    assert name == filename, f'Template name mismatch: {
        path!r
    } -> {name}'

    namespace = raw['metadata'].get('namespace', 'default')
    spec = raw['spec']

    return namespace, name, spec
