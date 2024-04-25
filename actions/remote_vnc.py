import streamlit as st
import streamlit.components.v1 as components

from assets import Assets
from dash.data.session import SessionRef
from utils.types import DataModel, SessionReturn
from widgets.link import draw_new_tab


async def render(
    assets: Assets,
    session: DataModel,
    name: str,
    spec: DataModel,
) -> SessionReturn:
    # Get metadata
    session_ref = SessionRef.from_data(session.get(
        keys=spec,
        path='/key',
        value_type=dict,
    ))

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
                session=session_ref,
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
    draw_new_tab(
        url=session.novnc_full_url,
    )
