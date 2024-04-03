from typing import Any, Self


class Command:
    def __init__(
        self,
        kind: str,
        namespace: str,
        name: str,
        key: str | None = None,
    ) -> None:
        self.kind = kind
        self.namespace = namespace
        self.name = name
        self.key = key

    @classmethod
    def from_str(cls, s: str) -> Self:
        _, kind, namespace, name, key = s.split('/')
        return cls(
            kind=kind,
            namespace=namespace,
            name=name,
            key=key if key and key != '_' else None,
        )

    @property
    def action(self) -> str:
        return f'/{self.kind}/{self.namespace}/{self.name}/{self.key or "_"}'

    @property
    def search_engine_function_name(self) -> str:
        if self.key:
            return self.key
        return self.name.replace('-', ' ')

    def to_json(self) -> dict[str, Any]:
        return {
            'kind': self.kind,
            'name': self.name,
            'namespace': self.namespace,
            'key': self.key,
        }

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, self.__class__):
            return self.to_json() == other.to_json()
        return False

    def __hash__(self) -> int:
        return hash(repr(self.to_json()))

    def __repr__(self) -> str:
        if self.key:
            return f'[{self.namespace}] {self.key}'
        return f'[{self.namespace}] {self.name.title().replace("-", " ")}'
