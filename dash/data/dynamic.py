from copy import deepcopy
import csv
import io
from typing import Any, Self

from jsonpointer import resolve_pointer, set_pointer
import pandas as pd

from data.object import DashObject


class DynamicObject(DashObject):
    def __init__(self, fields: list[dict[str, Any]]) -> None:
        super().__init__({})
        self._fields = fields
        self._values = {}

    def fields(self) -> list[dict[str, Any]]:
        return self._fields

    def set(self, key: str, value: Any):
        if value is None:
            return
        self._values[key] = value

        key = key[:-1]
        pointer = key.split('/')
        for index in range(1, len(pointer)):
            sub_pointer = pointer[:index + 1]
            sub_key = '/'.join(sub_pointer)
            if resolve_pointer(self.data, sub_key, None) is None:
                set_pointer(self.data, sub_key, {}, inplace=True)
        set_pointer(self.data, key, value, inplace=True)

    def to_csv(self) -> str:
        record = self.to_record(default='')

        buf = io.StringIO()
        writer = csv.DictWriter(
            f=buf,
            fieldnames=record.keys(),
            delimiter=',',
        )
        writer.writeheader()
        writer.writerow(record)
        return buf.getvalue()

    def to_dataframe(self) -> pd.DataFrame:
        record = self.to_record()
        return pd.DataFrame.from_records([record], index=[0])

    def to_record(self, default: Any = None) -> dict[str, Any]:
        return {
            field['name'][1:-1].replace('/', '_'):
                self._values.get(field['name'], default)
            for field in self._fields
        }

    def from_csv(self, data: bytes) -> list[Self]:
        buf = io.StringIO(data.decode('utf-8'))
        return [
            self.from_dict(row)
            for row in csv.DictReader(
                f=buf,
                delimiter=',',
            )
        ]

    def from_dict(self, data: dict[str, Any]) -> Self:
        value = deepcopy(self)
        for field in self._fields:
            key = field['name'][1:-1].replace('/', '_')
            if key:
                value.set(field['name'], data.get(key, None))
        return value

    @classmethod
    def collect_to_csv(cls, rows: list[Self]) -> str:
        records = [
            row.to_record()
            for row in rows
        ]

        buf = io.StringIO()
        writer = csv.DictWriter(
            f=buf,
            fieldnames=records[0].keys(),
            delimiter=',',
        )
        writer.writeheader()
        writer.writerows(records)
        return buf.getvalue()

    @classmethod
    def collect_to_dataframe(cls, rows: list[Self]) -> pd.DataFrame:
        records = [
            row.to_record()
            for row in rows
        ]
        return pd.DataFrame.from_records(records)
