import os
from typing import Any, Never, Self

import requests
import streamlit as st
from streamlit.web.server.websocket_headers import _get_websocket_headers

from dash.data.function import DashFunction
from dash.data.job import DashJob
from dash.data.model import DashModel
from dash.data.resource import ResourceRef
from dash.data.session import SessionRef
from dash.data.user import User


class DashClient:
    def __new__(cls) -> Self:
        @st.cache_resource()
        def init() -> Self:
            client = object.__new__(cls)
            client.__init__()
            return client

        return init()

    def __init__(self) -> None:
        self._session = requests.Session()
        self._host = os.environ.get('DASH_HOST') \
            or 'https://mobilex.kr/dash/api/'

    def __reduce__(self):
        return ()

    def _call_raw(
        self, *, namespace: str | None = None,
        method: str, path: str, value: Any = None,
        ok: bool = False,
    ) -> Any:
        def call(
            namespace: str | None,
            method: str, path: str, value: Any = None,
            ok: bool = False,
        ):
            headers = _get_websocket_headers() or {}
            headers_pass_through = [
                'Authorization',
                'Cookie',
            ]

            headers = {
                header: headers.get(header, None)
                for header in headers_pass_through
            }
            if namespace:
                headers['X-ARK-NAMESPACE'] = namespace

            response = self._session.request(
                method=method,
                url=f'{self._host}{path}',
                headers=headers,
                json=value,
            )

            if response.status_code != 200:
                _handle_error(path, response)

            if ok:
                return None

            if response.text:
                data = response.json()
            else:
                raise Exception(f'Failed to execute {path!r}: no response')

            if response.status_code == 200:
                if 'spec' in data:
                    return data['spec']
                raise Exception(f'Failed to execute {path!r}: no output')
            if 'spec' in data:
                raise Exception(f'Failed to execute {path!r}: {data["spec"]}')

            _handle_error(path, response)

        if method in ['GET', 'OPTION']:
            @st.cache_data(ttl=30)
            def call_cached(
                namespace: str | None,
                method: str, path: str, value: Any = None,
                ok: bool = False,
            ):
                return call(
                    namespace=namespace,
                    method=method,
                    path=path,
                    value=value,
                    ok=ok,
                )
            return call_cached(
                namespace=namespace,
                method=method,
                path=path,
                value=value,
                ok=ok,
            )
        return call(
            namespace=namespace,
            method=method,
            path=path,
            value=value,
            ok=ok,
        )

    def user_session(self) -> int:
        cookie = (_get_websocket_headers() or {}).get('Cookie')
        if not cookie:
            st.error('Login is required!')
            st.stop()

        @st.cache_data()
        def get_hashed_cookie(cookie: str | None) -> int:
            return hash(cookie)

        return get_hashed_cookie(cookie)

    def delete_job(
        self, *, namespace: str | None = None,
        function_name: str, job_name: str,
    ) -> None:
        return self._call_raw(
            namespace=namespace,
            method='DELETE',
            path=f'/task/{function_name}/job/{job_name}/',
        )

    def get_job(
        self, *, namespace: str | None = None,
        function_name: str, job_name: str,
    ) -> DashJob:
        return DashJob(
            data=self._call_raw(
                namespace=namespace,
                method='GET',
                path=f'/task/{function_name}/job/{job_name}/',
            )
        )

    def get_job_list(
        self, *, namespace: str | None = None,
    ) -> list[DashJob]:
        return [
            DashJob(
                data=data,
            )
            for data in self._call_raw(
                namespace=namespace,
                method='GET',
                path=f'/job/',
            )
        ]

    def get_job_list_with_function_name(
        self, *, namespace: str | None = None,
        function_name: str,
    ) -> list[DashJob]:
        return [
            DashJob(
                data=data,
            )
            for data in self._call_raw(
                namespace=namespace,
                method='GET',
                path=f'/task/{function_name}/job/',
            )
        ]

    def post_job(
        self, *, namespace: str | None = None,
        function_name: str, value: Any,
    ) -> DashJob:
        return DashJob(
            data=self._call_raw(
                namespace=namespace,
                method='POST',
                path=f'/task/{function_name}/job/',
                value=value,
            ),
        )

    def post_job_batch(
        self, *, payload: list[dict[str, Any]],
    ) -> list[DashJob]:
        return [
            DashJob(
                data=data
            )
            for data in self._call_raw(
                method='POST',
                path=f'/batch/job/',
                value=payload,
            )
        ]

    def restart_job(
        self, *, namespace: str | None = None,
        function_name: str, job_name: str,
    ) -> DashJob:
        return DashJob(
            data=self._call_raw(
                namespace=namespace,
                method='POST',
                path=f'/task/{function_name}/job/{job_name}/restart/',
            ),
        )

    def get_function(
        self, *, namespace: str | None = None,
        name: str,
    ) -> DashFunction:
        return DashFunction(
            data=self._call_raw(
                namespace=namespace,
                method='GET',
                path=f'/task/{name}/',
            ),
        )

    def get_function_list(
        self, *, namespace: str | None = None,
    ) -> list[ResourceRef]:
        return [
            ResourceRef(
                data=data,
            )
            for data in self._call_raw(
                namespace=namespace,
                method='GET',
                path=f'/task/',
            )
        ]

    def get_model(
        self, *, namespace: str | None = None,
        name: str,
    ) -> DashModel:
        return DashModel(
            data=self._call_raw(
                namespace=namespace,
                method='GET',
                path=f'/model/{name}/',
            ),
        )

    def get_model_function_list(
        self, *, namespace: str | None = None,
        name: str,
    ) -> list[DashFunction]:
        return [
            DashFunction(
                data=data,
            )
            for data in self._call_raw(
                namespace=namespace,
                method='GET',
                path=f'/model/{name}/task/',
            )
        ]

    def get_model_list(
        self, *, namespace: str | None = None,
    ) -> list[ResourceRef]:
        return [
            ResourceRef(
                data=data,
            )
            for data in self._call_raw(
                namespace=namespace,
                method='GET',
                path=f'/model/',
            )
        ]

    def get_model_item(
        self, *, namespace: str | None = None,
        name: str, item: str,
    ) -> DashModel:
        return DashModel(
            data=self._call_raw(
                namespace=namespace,
                method='GET',
                path=f'/model/{name}/item/{item}/',
            ),
        )

    def get_model_item_list(
        self, *, namespace: str | None = None,
        name: str,
    ) -> list[DashModel]:
        return [
            DashModel(
                data=data,
            )
            for data in self._call_raw(
                namespace=namespace,
                method='GET',
                path=f'/model/{name}/item/',
            )
        ]

    def get_user(self) -> User:
        return User.model_validate(
            obj=self._call_raw(
                method='GET',
                path=f'/user/',
            ),
        )

    def get_user_session_list(self) -> list[SessionRef]:
        return [
            SessionRef.from_data(
                data,
            )
            for data in self._call_raw(
                method='GET',
                path=f'/batch/user/session/',
            )
        ]

    def post_user_exec(
        self, *, namespace: str | None = None,
        command: str,
        terminal: bool,
    ) -> None:
        return self._call_raw(
            namespace=namespace,
            method='POST',
            path=f'/user/desktop/exec/',
            value=_parse_command(
                raw=command,
                terminal=terminal,
            ),
        )

    def post_user_exec_broadcast(
        self, command: str,
        terminal: bool,
        target_user_names: list[str] | None,
        wait: bool = False,
    ) -> None:
        return self._call_raw(
            method='POST',
            path=f'/batch/user/desktop/exec/broadcast/',
            value=None if target_user_names is None else {
                'command': _parse_command(
                    raw=command,
                    terminal=terminal,
                ),
                'userNames': target_user_names,
                'wait': wait,
            },
        )


def _handle_error(path: str, response: requests.Response) -> Never:
    match response.status_code:
        case 403:
            raise Exception(
                f'Failed to execute {path!r}: Permission Denied')
        case _:
            raise Exception(
                f'Failed to execute {path!r}: status code [{response.status_code}]')


def _parse_command(raw: str, terminal: bool) -> list[str]:
    command = []
    if terminal:
        command += [
            'xfce4-terminal',
            '--disable-server',
            '-x',
        ]
    command += [
        '/usr/bin/env',
        'sh',
        '-c',
        raw,
    ]
    return command
