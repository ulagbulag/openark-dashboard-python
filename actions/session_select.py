import re
from typing import Optional

from pandas import DataFrame
import streamlit as st

from dash.data.session import SessionRef
from utils.templates import Session, Spec, Templates
from widgets import selector


async def render(templates: Templates, session: Session, name: str, spec: Spec) -> Session:
    if 'filter' in spec:
        drawer = _draw_read_filter
    elif spec.get('multiple', False) == True:
        drawer = _draw_read_multiple
    else:
        drawer = _draw_read_one

    return drawer(
        templates=templates,
        session=session,
        name=name,
        spec=spec,
    )


def _draw_read_filter(templates: Templates, session: Session, name: str, spec: Spec) -> Session:
    sessions = templates.dash_client.get_user_session_list()

    pattern = spec['filter']
    session_filtered = [
        session.to_aggrid()
        for session in sessions
        if re.fullmatch(
            pattern=pattern,
            string=session.user_name,
        ) is not None
    ]

    return {
        'state': 'Ok' if session_filtered else 'Empty',
        'items': session_filtered,
    }


def _draw_read_multiple(templates: Templates, session: Session, name: str, spec: Spec) -> Session:
    st.subheader(spec['label'])

    sessions = DataFrame(
        session.to_aggrid()
        for session in templates.dash_client.get_user_session_list()
    )
    sessions_selected = selector.dataframe(
        df=sessions,
        show_selected=False,
    )

    return {
        'state': 'Ok' if sessions_selected else 'Empty',
        'items': sessions_selected,
    }


def _draw_read_one(templates: Templates, session: Session, name: str, spec: Spec) -> Session:
    sessions = templates.dash_client.get_user_session_list()
    session: Optional[SessionRef] = st.selectbox(
        label=spec['label'],
        options=sessions,
    )

    return {
        'state': 'Ok' if session is not None else 'Empty',
        **(session.to_dict() if session is not None else {}),
    }
