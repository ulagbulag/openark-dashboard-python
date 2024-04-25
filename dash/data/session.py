from typing import Any, Self


class SessionRef:
    def __init__(
        self,
        namespace: str | None = None,
        node_name: str | None = None,
        user_name: str | None = None,
    ) -> None:
        self.namespace = namespace
        self.node_name = node_name
        self._user_name = user_name

    @classmethod
    def from_aggrid(cls, data: dict[str, str]) -> Self:
        return cls(
            namespace=data['Namespace'],
            node_name=data['NodeName'],
            user_name=data['Name'],
        )

    @classmethod
    def from_data(cls, data: dict[str, str]) -> Self:
        return cls(
            namespace=data['namespace'],
            node_name=data['nodeName'],
            user_name=data['userName'],
        )

    @property
    def user_name(self) -> str:
        if self._user_name is None:
            raise ValueError('Empty user name')
        return self._user_name

    @property
    def novnc_full_url(self) -> str:
        return self._novnc_url(kind='vnc')

    @property
    def novnc_lite_url(self) -> str:
        return self._novnc_url(kind='vnc_lite')

    def _novnc_url(self, kind: str) -> str:
        base_host = 'mobilex.kr'
        base_url = f'https://{base_host}/dashboard/vnc'
        vnc_host = f'{base_host}/user/{self.user_name}/vnc/&scale=true'
        return f'{base_url}/{kind}.html?host={vnc_host}'

    def to_aggrid(self) -> dict[str, str | None]:
        return {
            'Name': self.user_name,
            'Namespace': self.namespace,
            'NodeName': self.node_name,
        }

    def to_dict(self) -> dict[str, str | None]:
        return {
            'namespace': self.namespace,
            'nodeName': self.node_name,
            'userName': self._user_name,
        }

    def __eq__(self, other: Any) -> bool:
        return repr(self) == repr(other)

    def __hash__(self) -> int:
        return hash(repr(self.to_dict()))

    def __repr__(self) -> str:
        return self.user_name
