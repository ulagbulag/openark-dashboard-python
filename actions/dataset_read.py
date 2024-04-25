import streamlit as st

from assets import Assets
from kubegraph.data.db.base import BaseNetworkGraphDB, NetworkGraphRef
from kubegraph.data.graph import NetworkGraph
from utils.types import DataModel, SessionReturn


async def render(assets: Assets, session: DataModel, name: str, spec: DataModel) -> SessionReturn:
    dataset_type = spec.get(
        path='/type',
        value_type=str,
    )
    match dataset_type:
        case 'Graph':
            return await _load_dataset(
                assets=assets,
                name=name,
                spec=spec,
            )
        case _:
            raise ValueError(f'Unsupported dataset type: {dataset_type}')


async def _load_dataset(assets: Assets, name: str, spec: DataModel) -> SessionReturn:
    # NOTE: Ordered
    sources = {
        'Search': _load_dataset_from_search,
        'Upload': _load_dataset_from_upload,
        'DB': _load_dataset_from_db,
    }
    selected_source = st.selectbox(
        label='Choose one of dataset sources',
        options=sources.keys(),
    )
    if selected_source is None:
        return st.stop()

    graph = await sources[selected_source](
        assets=assets,
        name=f'{name}/{selected_source}',
        spec=spec,
    )

    return {
        'state': 'Ok' if graph is not None else 'Empty',
        'value': graph,
    }


async def _load_dataset_from_db(assets: Assets, name: str, spec: DataModel) -> NetworkGraph | None:
    options = _load_dataset_list_from_db(assets.db)
    if not options:
        return None

    selected_sample = st.selectbox(
        key=f'{name}/sample',
        label='Choose one of dataset sources',
        options=options,
    )
    if selected_sample is None:
        return None

    return _load_dataset_from_db_unattended(
        _db=assets.db,
        dataset=selected_sample,
    )


# @st.cache_data(ttl=60)
def _load_dataset_from_db_unattended(
    _db: BaseNetworkGraphDB,
    dataset: NetworkGraphRef,
) -> NetworkGraph | None:
    return _db.load(
        kind=dataset.kind,
        namespace=dataset.namespace,
    )


# @st.cache_data(ttl=60)
def _load_dataset_list_from_db(_db: BaseNetworkGraphDB, /) -> list[NetworkGraphRef]:
    with st.spinner('🔥 Loading Datasets ...'):
        return _db.list()


async def _load_dataset_from_search(assets: Assets, name: str, spec: DataModel) -> NetworkGraph | None:
    question = st.text_input(
        key=f'{name}/prompt',
        label='Please search here :)',
        placeholder='How will the cloud change in three years?',
        value='warehouse traffic i/o status',
    ).strip()
    if not question:
        return None

    # @st.cache_data
    def _load(_assets: Assets, question: str) -> NetworkGraphRef | None:
        datasets = _load_dataset_list_from_db(_assets.db)
        datasets_annotations = {
            option: [
                f'Dataset {
                    index}: Import and export status of logistics warehouse',
            ]
            for index, option in enumerate(datasets)
        }
        if not datasets:
            st.warning('🤖 You have no datasets :(')
            return None

        selected_datasets = _assets.parse(
            datasets_annotations=datasets_annotations,
            question=question,
        )
        if not selected_datasets:
            st.warning('🤖 You have no proper datasets :(')
            return None

        # TODO: implement multiple dataset selection (deep dataset aggregation) support
        return selected_datasets[0]

    with st.spinner('🔥 Analyzing...'):
        selected_dataset = _load(
            _assets=assets,
            question=question,
        )
        if selected_dataset is None:
            return None

    st.selectbox(
        key=f'{name}/selected',
        label='Selected dataset',
        options=[
            selected_dataset,
        ],
        disabled=True,
    )

    return _load_dataset_from_db_unattended(
        _db=assets.db,
        dataset=selected_dataset,
    )


async def _load_dataset_from_upload(assets: Assets, name: str, spec: DataModel) -> NetworkGraph | None:
    uploaded_file = st.file_uploader(
        key=f'{name}/upload',
        label='Please upload a graph file',
        type='.tar',
    )
    if uploaded_file is None:
        return None

    return NetworkGraph.load(uploaded_file)
