from assets import Assets
from kubegraph.data.graph import NetworkGraph
from utils.types import DataModel, SessionReturn


async def render(assets: Assets, session: DataModel, name: str, spec: DataModel) -> SessionReturn:
    graph = session.get(
        keys=spec,
        path='/key',
        value_type=NetworkGraph,
    )

    return {
        'state': 'Ok',
        'value': graph,
    }
