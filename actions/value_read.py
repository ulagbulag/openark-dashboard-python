import datetime
import inflection
import ipaddress
import streamlit as st
from typing import Any
import uuid

from dash.client import DashClient


class ValueField:
    def __init__(self, namespace: str | None, field: dict[str, Any]) -> None:
        self._namespace = namespace
        self._field = field
        self._models = None
        self._value = None

        self._kind = None
        for kind in field.keys():
            kind = inflection.underscore(kind)
            if hasattr(self, f'_update_{kind}'):
                self._kind = kind
                break
        if self._kind is None:
            raise Exception(
                f'Cannot infer field type: {field["name"]}')

    def title(self) -> str:
        return self._field['name']

    def update(self) -> Any:
        self._value = getattr(self, f'_update_{self._kind}')()
        return self._value

    def _get_value(self, default: Any) -> Any:
        if self._value is not None:
            return self._value
        return default

    # BEGIN primitive types

    def _update_none(self) -> None:
        return None

    def _update_boolean(self) -> bool:
        spec = self._field['boolean']
        default = self._get_value(spec.get('default') or False)

        return st.checkbox(
            label=self.title(),
            value=default,
        )

    def _update_integer(self) -> None:
        spec = self._field['integer']
        default = self._get_value(spec.get('default') or 0)
        minimum = self._get_value(spec.get('minimum'))
        maximum = self._get_value(spec.get('maximum'))

        return st.slider(
            label=self.title(),
            value=default,
            min_value=minimum,
            max_value=maximum,
            step=1,
        )

    def _update_number(self) -> None:
        spec = self._field['number']
        default = self._get_value(spec.get('default') or 0.0)
        minimum = self._get_value(spec.get('minimum'))
        maximum = self._get_value(spec.get('maximum'))

        return st.slider(
            label=self.title(),
            value=default,
            min_value=minimum,
            max_value=maximum,
        )

    def _update_string(self, kind: str = 'string') -> str:
        spec = self._field[kind]
        default = self._get_value(spec.get('default') or '')

        return st.text_input(
            label=self.title(),
            value=default,
        )

    def _update_one_of_strings(self) -> str | None:
        spec = self._field['oneOfStrings']
        choices = spec.get('choices') or []
        default = self._get_value(spec.get('default'))

        if default is not None:
            try:
                index = choices.index(default)
            except:
                index = 0
        else:
            index = 0

        return st.selectbox(
            label=self.title(),
            options=choices,
            index=index,
        )

    # BEGIN string formats

    def _update_date_time(self) -> str | None:
        spec = self._field['dateTime']
        default = spec.get('default')

        date = st.date_input(
            label=self.title(),
            value=default,
        )
        if isinstance(date, tuple):
            if len(date) == 0:
                return None
            elif len(date) == 1:
                (date,) = date
            elif len(date) == 2:
                (date, _) = date
        else:
            date = date

        time = st.time_input(
            label=self.title(),
            value=default,
        )
        return datetime.datetime.combine(date, time).isoformat()

    def _update_ip(self) -> str | None:
        try:
            return str(ipaddress.ip_address(self._update_string(kind='ip')))
        except ValueError as e:
            st.warning(e)
            return None

    def _update_uuid(self) -> str | None:
        try:
            return str(uuid.UUID(self._update_string(kind='uuid')))
        except ValueError as e:
            st.warning(e)
            return None

    # BEGIN aggregation types

    def _update_string_array(self) -> None:
        raise Exception('String Array is not supported yet!')

    def _update_object(self) -> None:
        pass

    def _update_object_array(self) -> None:
        raise Exception('Object Array is not supported yet!')

    # BEGIN reference types

    def _update_model(self) -> str | None:
        spec = self._field['model']
        model_name = spec.get('name')

        # Load DASH Client
        client = DashClient()

        # Load models
        if self._models is None:
            self._models = {
                model.title(): model
                for model in client.get_model_item_list(
                    namespace=self._namespace,
                    name=model_name,
                )
            }

        # Get model names
        model_names = sorted((
            model.title()
            for model in self._models
        ))
        default = self._get_value(None)

        if default is not None:
            try:
                index = model_names.index(default)
            except:
                index = 0
        else:
            index = 0

        selected = st.selectbox(
            label=self.title(),
            options=model_names,
            index=index,
        )
        if selected is not None:
            return self._models[selected].name()
        return None
