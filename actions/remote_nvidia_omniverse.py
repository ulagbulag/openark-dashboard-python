import socket

import streamlit as st
import streamlit.components.v1 as components

from assets import Assets
from utils.types import DataModel, SessionReturn
from widgets.link import draw_new_tab


async def render(
    assets: Assets,
    session: DataModel,
    name: str,
    spec: DataModel,
) -> SessionReturn:
    # Get metadata
    base_url = spec.get(
        path='/baseUrl',
        value_type=str,
        default='http://www.twin.svc/streaming/webrtc-demo/',
    )
    server = spec.get(
        path='/server',
        value_type=str,
        default='webrtc.twin.svc',
    )

    # Parse URL
    server_ip = socket.gethostbyname(server)
    url = f'{base_url}?server={server_ip}'

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
                url=url,
            )

    return {
        'state': 'Ok',
    }


def _draw_page_show(*, url: str) -> None:
    # Action
    components.iframe(
        src=url,
        height=830,
    )


def _draw_page_open(*, url: str) -> None:
    # Action
    draw_new_tab(
        url=url,
    )
