import streamlit as st
from streamlit.delta_generator import DeltaGenerator


def draw_new_tab(
    *,
    url: str,
    label: str = 'Open link in a new Tab',
) -> DeltaGenerator:
    style = {
        'display': 'inline-block',
        'padding': '12px 20px',
        'background-color': '#4CAF50',
        'color': 'white',
        'text-align': 'center',
        'text-decoration': 'none',
        'font-size': '16px',
        'border-radius': '4px',
    }
    style_css = ' '.join((
        f'{key}: {value};'
        for key, value in style.items()
    ))

    # Action
    return st.markdown(
        body=f'<a href="{url}" style="{style_css}">{label}</a>',
        unsafe_allow_html=True,
    )
