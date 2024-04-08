import jsonpointer
import streamlit as st
import streamlit.components.v1 as components

from dash.data.session import SessionRef
from utils.types import Session, Spec
from utils.widgets import Widgets


async def render(widgets: Widgets, session: Session, name: str, spec: Spec) -> Session:
    # Get metadata
    session = SessionRef.from_data(
        jsonpointer.resolve_pointer(session, spec['key']),
    )

    # Show available commands
    commands = {
        'Show': _draw_page_show,
        'Open with a new Tab': _draw_page_open,
    }
    for (tab, draw) in zip(
        st.tabs([command.title() for command in commands]),
        commands.values(),
    ):
        with tab:
            draw(
                session=session,
            )

    return {
        'state': 'Ok',
    }


def _draw_page_show(
    *, session: SessionRef,
) -> None:
    # Action
    components.iframe(
        src=session.novnc_lite_url,
        height=830,
    )


def _draw_page_open(
    *, session: SessionRef,
) -> None:
    # Action
    st.markdown(
        body=f'<a href="{session.novnc_full_url}" style="display: inline-block; padding: 12px 20px; background-color: #4CAF50; color: white; text-align: center; text-decoration: none; font-size: 16px; border-radius: 4px;">Open link in a new Tab</a>',
        unsafe_allow_html=True,
    )
