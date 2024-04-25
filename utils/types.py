from typing import Any, Iterable, Self

import jsonpointer
from pydantic import BaseModel, Field


SessionReturn = dict[str, Any] | None
Template = dict[str, Any]
Templates = Template | Iterable[Template]


class DataModel(BaseModel):
    data: dict[str, Any] = Field(default={}, frozen=True)

    def cast[T: BaseModel](self, model_type: type[T]) -> T:
        return model_type.model_validate(
            obj=self.data,
            strict=True,
        )

    def get[T](
        self,
        path: str,
        value_type: type[T],
        *,
        default: T | None = None,
        keys: Self | None = None,
    ) -> T:
        value = self.get_optional(
            path=path,
            value_type=value_type,
            default=default,
            keys=keys,
        )
        if value is None:
            raise ValueError(f'Empty value: {path!r}')
        return value

    def get_optional[T](
        self,
        path: str,
        value_type: type[T],
        *,
        default: T | None = None,
        keys: Self | None = None,
    ) -> T | None:
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
        default: Any | None = None,
        keys: Self | None = None,
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
    ) -> Any | None:
        self.data[path] = value
