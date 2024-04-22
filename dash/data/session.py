from typing import Any, Optional, Self


class SessionRef:
    def __init__(
        self,
        namespace: Optional[str] = None,
        node_name: Optional[str] = None,
        user_name: Optional[str] = None,
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
        return f'https://mobilex.kr/dashboard/vnc/{kind}.html?host=mobilex.kr/user/{self.user_name}/vnc/&scale=true'

    def to_aggrid(self) -> dict[str, Optional[str]]:
        return {
            'Name': self.user_name,
            'Namespace': self.namespace,
            'NodeName': self.node_name,
        }

    def to_dict(self) -> dict[str, Optional[str]]:
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
