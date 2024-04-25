import re

from pandas import DataFrame
import streamlit as st

from assets import Assets
from dash.data.session import SessionRef
from utils.types import DataModel, SessionReturn
from widgets import selector


async def render(
    assets: Assets,
    session: DataModel,
    name: str,
    spec: DataModel,
) -> SessionReturn:
    filter = spec.get_optional(
        path='/filter',
        value_type=str,
    )
    if filter is not None:
        return _draw_read_filter(
            assets=assets,
            pattern=filter,
        )

    label = spec.get(
        path='/label',
        value_type=str,
    )

    if spec.get(
        path='/multiple',
        value_type=bool,
        default=False,
    ):
        return _draw_read_multiple(
            assets=assets,
            spec=spec,
            label=label,
        )

    return _draw_read_one(
        assets=assets,
        spec=spec,
        label=label,
    )


def _draw_read_filter(assets: Assets, pattern: str) -> SessionReturn:
    sessions = assets.dash_client.get_user_session_list()

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


def _draw_read_multiple(
    assets: Assets,
    spec: DataModel,
    label: str,
) -> SessionReturn:
    st.subheader(label)

    sessions = DataFrame(
        session.to_aggrid()
        for session in assets.dash_client.get_user_session_list()
    )
    sessions_selected = selector.dataframe(
        df=sessions,
        show_selected=False,
    )

    return {
        'state': 'Ok' if sessions_selected else 'Empty',
        'items': sessions_selected,
    }


def _draw_read_one(
    assets: Assets,
    spec: DataModel,
    label: str,
) -> SessionReturn:
    sessions = assets.dash_client.get_user_session_list()
    selected_session: SessionRef | None = st.selectbox(
        label=label,
        options=sessions,
    )

    return {
        'state': 'Ok' if selected_session is not None else 'Empty',
        **(selected_session.to_dict() if selected_session is not None else {}),
    }
