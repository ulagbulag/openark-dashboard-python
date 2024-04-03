from typing import Any


class ResourceRef:
    def __init__(self, data: dict[str, str]) -> None:
        self.name = data['name']
        self.namespace = data['namespace']

    def to_dict(self) -> dict[str, str]:
        return {
            'name': self.name,
            'namespace': self.namespace,
        }

    def __eq__(self, other: Any) -> bool:
        return repr(self) == repr(other)

    def __hash__(self) -> int:
        return hash(repr(self.to_dict()))

    def __repr__(self) -> str:
        return f'[{self.namespace}] {self.name.title().replace("-", " ")}'
