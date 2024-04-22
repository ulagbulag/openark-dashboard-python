import streamlit as st

from assets import Assets
from dash.data.session import SessionRef
from utils.types import DataModel, SessionReturn


async def render(assets: Assets, session: DataModel, name: str, spec: DataModel) -> SessionReturn:
    st.divider()

    maybe_sessions = session.get_unchecked(
        keys=spec,
        path='/session',
    )
    if isinstance(maybe_sessions, dict):
        user_names = [
            SessionRef.from_data(maybe_sessions).user_name,
        ]
    elif isinstance(maybe_sessions, list):
        user_names = [
            SessionRef.from_aggrid(session).user_name
            for session in maybe_sessions
        ]
    st.text(f'* 노드 수: {len(user_names)}')

    command = session.get(
        keys=spec,
        path='/command',
        value_type=str,
    )
    st.text(
        '* ' + spec.get(
            path='/labelCheck',
            value_type=str,
            default='Please make sure you are trying to run the code below!',
        ),
    )
    st.code(command)

    terminal = st.checkbox(
        key=f'{name}/terminal',
        label='GUI 모드로 실행',
        value=True,
    )

    wait = st.checkbox(
        key=f'{name}/wait',
        label='끝날 때까지 대기',
        value=True,
    )

    if not st.button(
        key=f'{name}/submit',
        label=spec.get(
            path='/label',
            value_type=str,
            default='Submit',
        ),
    ):
        return {
            'state': 'Cancel',
        }

    with st.spinner('명령 실행 중...' if wait else '명령 전달 중...'):
        assets.dash_client.post_user_exec_broadcast(
            command=command,
            terminal=terminal,
            target_user_names=user_names,
            wait=wait,
        )

    st.info(spec.get(
        path='/labelSuccess',
        value_type=str,
        default='Succeeded!',
    ))

    return {
        'state': 'Ok',
    }
