from typing import Any, Dict, Iterable, Optional, Self, Type, TypeVar, Union

import jsonpointer
from pydantic import BaseModel, Field


SessionReturn = Optional[Dict[str, Any]]
Template = Dict[str, Any]
Templates = Union[Template, Iterable[Template]]


ModelType = TypeVar('ModelType', bound=BaseModel)
ValueType = TypeVar('ValueType')


class DataModel(BaseModel):
    data: Dict[str, Any] = Field(default={}, frozen=True)

    def cast(self, model_type: Type[ModelType]) -> ModelType:
        return model_type.model_validate(
            obj=self.data,
            strict=True,
        )

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
            if (
                isinstance(value, BaseModel)
                and issubclass(value_type, BaseModel)
            ):
                # Try to convert type
                return value_type.model_validate(value.model_dump())

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
