import logging
import os
from typing import Dict, List, Optional, override
from pydantic import BaseModel

from PIL import Image
import streamlit as st

from dash.client import DashClient
from kubegraph.data.db.base import NetworkGraphRef
from kubegraph.parser.auto import AutoParser
from kubegraph.parser.base import BaseParser
from utils.widgets import Widgets

_ASSETS_DIR = os.path.dirname(__file__)


class Assets(BaseModel, BaseParser):
    debug: bool = False
    templates_dir: str = './templates/'

    parser: AutoParser = AutoParser()

    _dash_client: Optional[DashClient] = None
    _logger: logging.Logger = logging.getLogger('openark-dashboard')
    _widgets: Optional[Widgets] = None

    @classmethod
    def asset_path(cls, path: str) -> str:
        return f'{_ASSETS_DIR}/{path}'

    @classmethod
    def load_image(cls, path: str) -> Image.Image:
        return Image.open(cls.asset_path(path))

    @property
    def dash_client(self) -> DashClient:
        if self.debug or self._dash_client is None:
            self._dash_client = DashClient()
        return self._dash_client

    @property
    def widgets(self) -> Widgets:
        if self.debug or self._widgets is None:
            self._widgets = Widgets(
                dash_client=self.dash_client,
                templates_dir=self.templates_dir,
            )
        return self._widgets

    @override
    def parse(
        self,
        datasets_annotations: Dict[NetworkGraphRef, List[str]],
        question: str,
    ) -> List[NetworkGraphRef] | None:
        return self.parser.parse(
            datasets_annotations=datasets_annotations,
            question=question,
        )


@st.cache_resource(ttl=None)
def init_assets(debug: bool = False) -> Assets:
    with st.spinner('🔥 Loading Assets...'):
        return Assets(
            debug=debug,
        )
