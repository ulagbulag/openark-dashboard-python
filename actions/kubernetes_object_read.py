import re
from typing import Any

from jsonpointer import resolve_pointer
import kubernetes as kube

from utils.types import Session, Spec
from utils.widgets import Widgets


async def render(widgets: Widgets, session: Session, name: str, spec: Spec) -> Session:
    # Load resource API
    *group, version = str(spec.get('apiVersion')).split('/')
    plural = spec.get('plural')

    objects = kube.client.CustomObjectsApi().list_cluster_custom_object(
        group='/'.join(group),
        version=version,
        plural=plural,
    )['items']

    filter = spec.get('filter', None)
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
