from typing import Optional
import streamlit as st

from dash.data.session import SessionRef
from utils.templates import Session, Spec, Templates


async def render(templates: Templates, session: Session, spec: Spec) -> Session:
    sessions = templates.dash_client.get_user_session_list()
    session: Optional[SessionRef] = st.selectbox(
        label=spec['label'],
        options=sessions,
    )

    return {
        'state': 'Ok' if session is not None else 'Empty',
        **(session.to_dict() if session is not None else {}),
    }
