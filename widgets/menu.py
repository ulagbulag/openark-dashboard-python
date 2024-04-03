from typing import Optional
import inflection
import streamlit as st

from utils.templates import Session, Templates


async def render(templates: Templates, columns) -> Optional[Session]:
    st.title('Menu')

    selected_page = st.session_state.get('menu', None)
    for namespace, names in templates.get_names().items():
        st.divider()
        st.subheader(inflection.titleize(namespace))
        for name, title in names:
            if st.button(title):
                selected_page = namespace, name

    if selected_page is not None:
        namespace, name = st.session_state['menu'] = selected_page
        if columns:
            columns.pop(0).__enter__()
        return await templates.render(namespace, name, columns)
    return None
