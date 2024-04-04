import asyncio
import os

import dotenv
import streamlit as st
from streamlit.errors import StreamlitAPIException

import widgets.menu
import widgets.profile
import utils.templates


async def main():
    # Environment Variable Configuration
    dotenv.load_dotenv()

    # Page Configuration
    try:
        st.set_page_config(layout='wide')
    except StreamlitAPIException:
        pass

    templates = utils.templates.Templates(
        path=os.environ.get('OPENARK_TEMPLATES_DIR', './templates'),
    )
    with st.sidebar:
        widgets.profile.render()

    col_menu, *cols = st.columns(2, gap='large')
    with col_menu:
        session = await widgets.menu.render(templates, cols)


if __name__ == '__main__':
    asyncio.run(main())
