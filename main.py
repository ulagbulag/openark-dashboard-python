import asyncio

import dotenv
import streamlit as st
from streamlit.errors import StreamlitAPIException

import widgets.menu
import widgets.profile


async def main():
    # Environment Variable Configuration
    dotenv.load_dotenv()

    # Page Configuration
    try:
        st.set_page_config(layout='wide')
    except StreamlitAPIException:
        pass

    with st.sidebar:
        widgets.profile.render()

    col_menu, *cols = st.columns(2, gap='large')
    with col_menu:
        session = await widgets.menu.render(cols)


if __name__ == '__main__':
    asyncio.run(main())
