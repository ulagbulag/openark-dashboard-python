import re
from typing import Any

from jsonpointer import resolve_pointer
import kubernetes as kube

from assets import Assets
from utils.types import DataModel, SessionReturn


async def render(assets: Assets, session: DataModel, name: str, spec: DataModel) -> SessionReturn:
    # Load resource API
    *group, version = spec.get(
        path='/apiVersion',
        value_type=str,
    ).split('/')
    plural = spec.get(
        path='/plural',
        value_type=str,
    )

    objects = kube.client.CustomObjectsApi().list_cluster_custom_object(
        group='/'.join(group),
        version=version,
        plural=plural,
    )['items']

    filter = spec.get_optional(
        path='/filter',
        value_type=str,
    )
    if filter:
        objects = [
            object
            for object in objects
            if _filter_object(filter, object)
        ]

    return {
        'state': 'Ok' if objects else 'Empty',
        'items': objects,
    }


def _filter_object(pattern: str, object: dict[str, Any]) -> bool:
    return any(
        re.fullmatch(
            pattern=pattern,
            string=name,
        ) is not None
        for name in
        (
            resolve_pointer(object, pointer)
            for pointer in [
                '/metadata/labels/dash.ulagbulag.io~1alias',
                '/metadata/name',
            ]
        )
        if isinstance(name, str) and name
    )
