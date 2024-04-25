from pydantic import BaseModel


class ResourceRef(BaseModel, frozen=True):
    name: str
    namespace: str = 'default'

    def __repr__(self) -> str:
        return f'[{self.namespace}] {self.name.title().replace("-", " ")}'
