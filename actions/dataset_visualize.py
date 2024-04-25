import folium
import streamlit as st
from streamlit_folium import st_folium

from assets import Assets
from kubegraph.data.graph import NetworkGraph
from utils.types import DataModel, SessionReturn


async def render(
    assets: Assets,
    session: DataModel,
    name: str,
    spec: DataModel,
) -> SessionReturn:
    graph = session.get(
        keys=spec,
        path='/key',
        value_type=NetworkGraph,
    )

    # NOTE: Ordered
    actions = {
        'Summary': _draw_action_summary,
        'Visualize': _draw_action_visualize,
        'Export': _draw_action_export,
    }
    if graph.is_geolocational():
        actions['World Map'] = _draw_action_map_world

    selected_action = st.selectbox(
        key=name,
        label='Choose one of dataset sources',
        options=actions.keys(),
    )
    if selected_action is None:
        return {
            'state': 'Empty',
        }

    actions[selected_action](
        name=f'{name}/{selected_action}',
        graph=graph,
    )
    return {
        'state': 'Ok',
    }


def _draw_action_export(name: str, graph: NetworkGraph) -> None:
    data = graph.dumps()
    st.download_button(
        key=name,
        label='Download your Graph',
        file_name='graph.tar',
        data=data,
    )


def _draw_action_map_world(name: str, graph: NetworkGraph) -> None:
    map = folium.Map(
        crs='EPSG3857',
        tiles='OpenStreetMap',
        zoom_control=False,
    )

    # Add nodes
    for name, *location in graph.nodes.rows_by_key((
        'name',
        'latitude',
        'longitude',
    )):
        map.add_child(
            folium.Marker(
                location,
                popup=name,
                tooltip=name,
            )
        )

    # Fit to bounds
    bounds: list[list[float]] = map.get_bounds()  # type: ignore
    map.fit_bounds(bounds)

    # Render
    st_folium(
        key=name,
        fig=map,
        use_container_width=True,
    )


def _draw_action_summary(name: str, graph: NetworkGraph) -> None:
    st.subheader('Nodes', divider=True)
    st.write(graph.nodes.to_pandas())

    st.subheader('Edges', divider=True)
    st.write(graph.edges.to_pandas())


def _draw_action_visualize(name: str, graph: NetworkGraph) -> None:
    st.subheader('Graph Visualization', divider=True)
    st.graphviz_chart(
        figure_or_dot=graph.to_graphviz(),
        use_container_width=True,
    )
