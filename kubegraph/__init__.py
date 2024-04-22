from typing import Self, Union

import pandas as pd
import polars as pl
from pydantic import BaseModel

from kubegraph.data.series import NetworkGraphSeries as GraphSeries


# class GraphSeries(BaseModel, arbitrary_types_allowed=True):
#     '''ChatGPT용 테스트 클래스'''

#     nodes: Union[pd.DataFrame, pl.DataFrame]
#     edges: Union[pd.DataFrame, pl.DataFrame]
#     timestamp: str
#     step_unit: str

#     def step(self, nstep: int = 1) -> Self:
#         return self
