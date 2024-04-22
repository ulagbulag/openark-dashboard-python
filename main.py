import asyncio

import dotenv
import streamlit as st
from streamlit.errors import StreamlitAPIException

from assets import Assets, init_assets
from utils.otel import init_opentelemetry
import widgets.main


async def main() -> None:
    # Environment Variable Configuration
    dotenv.load_dotenv()

    # Page Configuration
    try:
        st.set_page_config(
            initial_sidebar_state='collapsed',
            layout='wide',
            page_icon=Assets.load_image('logo.png'),
            page_title='OpenARK | Dashboard',
        )
    except StreamlitAPIException:
        pass

    # OpenTelemetry Configuration
    init_opentelemetry()

    # Assets Configuration
    assets = init_assets()

    # Render a Page
    await widgets.main.render(assets)


if __name__ == '__main__':
    asyncio.run(main())
