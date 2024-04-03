from typing import Any, Hashable


class User:
    def __init__(self, data: dict[Hashable, Any]) -> None:
        self.data = data

    @property
    def box_name(self) -> str | None:
        return self.data.get('boxName')

    @property
    def email(self) -> str:
        return str(self.data['user']['contact']['email'] or '')

    @property
    def image(self) -> str:
        return ''

    @property
    def name(self) -> str:
        return str(self.data['userName'] or '')

    @property
    def namespace(self) -> str:
        return str(self.data['namespace'] or '')

    @property
    def nickname(self) -> str:
        return str(self.data['user']['name'] or '')

    @property
    def role_admin(self) -> bool:
        return bool(self.data['role']['isAdmin'])

    @property
    def role_dev(self) -> bool:
        return bool(self.data['role']['isDev'])

    @property
    def role_ops(self) -> bool:
        return bool(self.data['role']['isOps'])

    @property
    def tel_office(self) -> str:
        return str(self.data['user']['contact']['telOffice'] or '')

    @property
    def tel_phone(self) -> str:
        return str(self.data['user']['contact']['telPhone'] or '')
