import logging
import os
from typing import Self, override
from pydantic import BaseModel

from PIL import Image
import streamlit as st

from dash.client import DashClient
from kubegraph.data.db.base import BaseNetworkGraphDB, NetworkGraphRef
from kubegraph.data.db.local import LocalNetworkGraphDB
from kubegraph.parser.auto import AutoParser
from kubegraph.parser.base import BaseParser
from utils.widgets import Widgets

_ASSETS_DIR = os.path.dirname(__file__)


class Assets(BaseModel, BaseParser):
    debug: bool = False
    templates_dir: str = './templates/'

    parser: AutoParser = AutoParser()

    _dash_client: DashClient | None = None
    _db: BaseNetworkGraphDB | None = None
    _logger: logging.Logger = logging.getLogger('openark-dashboard')
    _widgets: Widgets[Self] | None = None

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
    def db(self) -> BaseNetworkGraphDB:
        if self.debug or self._db is None:
            self._db = LocalNetworkGraphDB(
                base_dir=f'{self.templates_dir}/db/',
            )
        return self._db

    @property
    def widgets(self) -> Widgets[Self]:
        if self.debug or self._widgets is None:
            self._widgets = Widgets(
                dash_client=self.dash_client,
                templates_dir=self.templates_dir,
            )
        return self._widgets

    @override
    def parse(
        self,
        datasets_annotations: dict[NetworkGraphRef, list[str]],
        question: str,
    ) -> list[NetworkGraphRef] | None:
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
