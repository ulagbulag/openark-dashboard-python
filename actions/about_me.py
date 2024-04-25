import re
from typing import Any, Callable

import streamlit as st

from assets import Assets
from dash.data.user import User
from utils.types import DataModel, SessionReturn


async def render(assets: Assets, session: DataModel, name: str, spec: DataModel) -> SessionReturn:
    user = assets.dash_client.get_user()

    is_valid = True
    is_updated = False
    with st.form(
        key=f'{name}',
        border=True,
    ):
        st.subheader('About Me')

        _draw_text_input(
            name=f'{name}/name',
            label='Name',
            default=user.name,
            disabled=True,
        )

        is_field_valid, is_field_updated, nickname = _draw_text_input(
            name=f'{name}/nickname',
            label='Nickname',
            default=user.spec.nickname,
            disabled=False,
        )
        is_valid &= is_field_valid
        is_updated |= is_field_updated

        st.subheader('Contacts')

        is_field_valid, is_field_updated, email = _draw_text_input(
            name=f'{name}/email',
            label='E-mail',
            default=user.spec.contact.email,
            disabled=False,
            validator=_validate_text_email,
        )
        is_valid &= is_field_valid
        is_updated |= is_field_updated

        is_field_valid, is_field_updated, tel_office = _draw_text_input(
            name=f'{name}/tel/office',
            label='Tel. Office',
            default=user.spec.contact.tel_office,
            disabled=False,
            validator=_validate_text_tel,
        )
        is_valid &= is_field_valid
        is_updated |= is_field_updated

        is_field_valid, is_field_updated, tel_phone = _draw_text_input(
            name=f'{name}/tel/phone',
            label='Tel. Mobile',
            default=user.spec.contact.tel_phone,
            disabled=False,
            validator=_validate_text_tel,
        )
        is_valid &= is_field_valid
        is_updated |= is_field_updated

        st.subheader('Role')

        col_admin, col_dev, col_ops = st.columns(3)
        with col_admin:
            role_admin = st.checkbox(
                key=f'{name}/role/admin',
                label='Admin',
                value=user.role.is_admin,
            )
            is_updated |= role_admin != user.role.is_admin
        with col_dev:
            role_dev = st.checkbox(
                key=f'{name}/role/dev',
                label='Dev',
                value=user.role.is_dev,
                disabled=role_admin,
            )
            if role_admin:
                role_dev = user.role.is_dev
            is_updated |= role_dev != user.role.is_dev
        with col_ops:
            role_ops = st.checkbox(
                key=f'{name}/role/ops',
                label='Ops',
                value=user.role.is_ops,
                disabled=role_admin,
            )
            if role_admin:
                role_ops = user.role.is_ops
            is_updated |= role_ops != user.role.is_ops

        if st.form_submit_button(
            label='Apply',
            disabled=False,
        ):
            if not is_valid:
                st.warning('One or more fields are invalid', icon='🚨')
            elif not is_updated:
                st.info('Nothing changed')
            else:
                return await _draw_submit(
                    assets=assets,
                    user=user,
                    patch={
                        'role': {
                            'isAdmin': role_admin,
                            'isDev': role_dev,
                            'isOps': role_ops,
                        },
                        'user': {
                            'contact': {
                                'email': email,
                                'telOffice': tel_office,
                                'telPhone': tel_phone,
                            },
                            'name': nickname,
                        },
                    },
                )

    return {
        'state': 'Ok',
        'value': user,
    }


async def _draw_submit(
    assets: Assets,
    user: User,
    patch: dict[str, Any],
) -> SessionReturn:
    with st.spinner('Applying...'):
        # TODO: to be implemented
        import time
        time.sleep(3)

    st.warning('To be implemented!')
    # st.success('Applied!', icon='✅')
    return {
        'state': 'Ok',
        'value': user,
    }


def _draw_text_input(
    name: str,
    label: str,
    default: str | None,
    disabled: bool = False,
    validator: Callable[[str], str | None] | None = None,
) -> tuple[bool, bool, str | None]:
    if not default:
        default = None
    value = st.text_input(
        key=name,
        label=label,
        value=default,
        disabled=disabled,
    )
    if value is None:
        value = default
    else:
        value = value.strip()
    if not value:
        value = None

    if value is not None and validator is not None:
        validated_value = validator(value)
        is_valid = validated_value is not None
    else:
        validated_value = value
        is_valid = True

    if not is_valid and value is None:
        st.warning('Value is required')

    return is_valid, value != default, validated_value


_MAX_LENGTH = 32


def _validate_text_email(value: str) -> str | None:
    if re.fullmatch(
        string=value,
        pattern=rf'(\w{{3,{_MAX_LENGTH}}})@'
        rf'(\w{{2,{_MAX_LENGTH}}}(\.\w{{2,{_MAX_LENGTH}}})+)',
    ) is not None and len(value) < _MAX_LENGTH:
        return value

    st.warning('Invalid e-mail address')
    return None


def _validate_text_tel(value: str) -> str | None:
    if re.fullmatch(
        string=value,
        pattern=r'(\+\d{1,3} )?(\d{1,6}+)(-\d{1,6}+)+',
    ) is not None and len(value) < _MAX_LENGTH:
        return value

    st.warning('Invalid number')
    return None
