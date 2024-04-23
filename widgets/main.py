from typing import Any, Dict, Optional
import streamlit as st
from streamlit_navigation_bar import st_navbar

from assets import Assets
from utils.widgets import PageTemplate


async def render(assets: Assets) -> Optional[Dict[str, Any]]:
    # Configure page header
    logo_path = assets.asset_path('logo.svg')

    options = {
        # "fix_shadow": True,
        # 'show_menu': False,
        # 'show_sidebar': False,
        'use_padding': True,
    }
    styles = {
        'div': {
            # 'max-width': '32rem',
        },
        'nav': {
            # 'background-color': 'green',
            'justify-content': 'left',
        },
        'img': {
            'padding-right': '24px',
        },
        'span': {
            'border-radius': '0.5rem',
            # 'color': 'white',
            'margin': '0 0.125rem',
            'padding': '0.4375rem 0.625rem',
            # 'width': '80px',
        },
        'active': {
            'background-color': 'rgba(255, 255, 255, 0.25)',
        },
        'hover': {
            'background-color': 'rgba(255, 255, 255, 0.35)',
        },
    }

    # NOTE: Ordered
    pages: Dict[str, Optional[PageTemplate]] = {
        page.title: page
        for page in assets.widgets.get_pages()
    }
    pages['GitHub'] = None
    urls = {
        'GitHub': 'https://github.com/ulagbulag/openark-dashboard-python',
    }

    # Skip appending home page button
    if 'Home' in pages:
        del pages['Home']

    # Show page header (navigation bar)
    selected_page_name: str = st_navbar(
        key='main',
        logo_path=logo_path,
        options=options,  # type: ignore
        pages=list(pages.keys()),
        styles=styles,
        urls=urls,
    )
    st.title(selected_page_name)

    if selected_page_name == 'Home':
        selected_page = assets.widgets.get_home_page()
    else:
        selected_page = pages.get(selected_page_name)
    if selected_page is None:
        return None

    # Show available menus
    if not selected_page.widgets:
        return None
    elif len(selected_page.widgets) == 1:
        selected_menu = selected_page.widgets[0]
    else:
        selected_menu = st.selectbox(
            key='/_page/menu',
            label='Choose one of the menus',
            options=selected_page.widgets,
        )
        if selected_menu is None:
            return None

    # Show selected menu
    return await assets.widgets.render(
        assets=assets,
        namespace=selected_menu.namespace,
        name=selected_menu.name,
        columns=st.columns(2),
    )
