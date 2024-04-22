from typing import Any, Dict, Iterable, Optional, Self, Type, TypeVar, Union

import jsonpointer
from pydantic import BaseModel, Field


SessionReturn = Dict[str, Any]
Template = Dict[str, Any]
Templates = Union[Template, Iterable[Template]]


ValueType = TypeVar('ValueType')


class DataModel(BaseModel):
    data: Dict[str, Any] = Field(default={}, frozen=True)

    def get(
        self,
        path: str,
        value_type: Type[ValueType],
        *,
        default: Optional[ValueType] = None,
        keys: Optional[Self] = None,
    ) -> ValueType:
        value = self.get_optional(
            path=path,
            value_type=value_type,
            default=default,
            keys=keys,
        )
        if value is None:
            raise ValueError(f'Empty value: {path!r}')
        return value

    def get_optional(
        self,
        path: str,
        value_type: Type[ValueType],
        *,
        default: Optional[ValueType] = None,
        keys: Optional[Self] = None,
    ) -> Optional[ValueType]:
        value = self.get_unchecked(
            path=path,
            default=default,
            keys=keys,
        )
        if value is None:
            return None
        if not isinstance(value, value_type):
            raise ValueError(
                f'Type mismatch on {path!r}: '
                f'Expected {str(value_type)}, '
                f'but Given {str(type(value))}'
            )
        return value

    def get_unchecked(
        self,
        path: str,
        *,
        default: Optional[Any] = None,
        keys: Optional[Self] = None,
    ) -> Any:
        if keys is None:
            pointer = path
        else:
            pointer = keys.get(
                path=path,
                value_type=str,
            )

        return jsonpointer.resolve_pointer(
            doc=self.data,
            pointer=pointer,
            default=default,
        )

    def insert(
        self,
        path: str,
        value: Any,
    ) -> Optional[Any]:
        self.data[path] = value
