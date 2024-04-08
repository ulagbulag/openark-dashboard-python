import os
from typing import Any, Optional

import inflection
import streamlit as st

from utils.types import Session
from utils.widgets import Widgets


async def render(columns: list[Any]) -> Optional[Session]:
    st.title('Menu')

    widgets = Widgets(
        path=f'{os.environ.get('OPENARK_TEMPLATES_DIR', './templates')}',
    )

    selected_page = st.session_state.get('menu', None)
    for namespace, names in widgets.get_names().items():
        st.divider()
        st.subheader(inflection.titleize(namespace))
        for name, title in names:
            if st.button(title):
                selected_page = namespace, name

    if selected_page is not None:
        namespace, name = st.session_state['menu'] = selected_page
        if columns:
            columns.pop(0).__enter__()
        return await widgets.render(namespace, name, columns)
    return None
