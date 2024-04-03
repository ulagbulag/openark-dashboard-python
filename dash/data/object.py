from jsonpointer import resolve_pointer
from typing import Any, Hashable


class DashObject:
    def __init__(self, data: dict[Hashable, Any]) -> None:
        self.data = data

    def __eq__(self, value: object) -> bool:
        return isinstance(value, DashObject) \
            and type(self) is type(value) \
            and self.name() == value.name() \
            and self.namespace() == value.namespace()

    def __hash__(self) -> int:
        return hash(repr(self.data))

    def name(self) -> str:
        data = resolve_pointer(self.data, '/metadata/name', None)
        if isinstance(data, str) and data:
            return data
        raise Exception('cannot get the name of the object')

    def namespace(self) -> str:
        data = resolve_pointer(self.data, '/metadata/namespace', None)
        if isinstance(data, str) and data:
            return data
        raise Exception('cannot get the namespace of the object')

    def title(self) -> str:
        return self.title_raw().title().replace('-', ' ')

    def title_raw(self) -> str:
        name = '???'
        for pointer in [
            '/metadata/labels/dash.ulagbulag.io~1alias',
            '/metadata/name',
        ]:
            data = resolve_pointer(self.data, pointer, None)
            if isinstance(data, str) and data:
                name = data
                break

        return name
