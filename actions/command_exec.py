from typing import Union
import jsonpointer
import streamlit as st

from dash.data.session import SessionRef
from utils.templates import Session, Spec, Templates


async def render(templates: Templates, session: Session, name: str, spec: Spec) -> Session:
    st.divider()

    maybe_sessions: Union[dict[str, str], list[dict[str, str]]] = jsonpointer.resolve_pointer(
        session, spec['session'])
    if isinstance(maybe_sessions, dict):
        user_names = [
            SessionRef.from_data(maybe_sessions).user_name,
        ]
    else:
        user_names = [
            SessionRef.from_aggrid(session).user_name
            for session in maybe_sessions
        ]
    st.text(f'* 실행할 세션 수: {len(user_names)}')

    command: str = jsonpointer.resolve_pointer(session, spec['command'])
    st.text('* ' + spec['labelCheck'])
    st.code(command)

    terminal = st.checkbox(
        key=f'{name}/terminal',
        label='GUI 모드로 실행',
    )

    if not st.button(
        key=f'{name}/submit',
        label=spec['label'],
    ):
        return {
            'state': 'Cancel',
        }

    with st.spinner('명령 전달 중...'):
        templates.dash_client.post_user_exec_broadcast(
            command=command,
            terminal=terminal,
            target_user_names=user_names,
        )

    st.info(spec['labelSuccess'])

    return {
        'state': 'Ok',
    }
