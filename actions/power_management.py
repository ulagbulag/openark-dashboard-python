import streamlit as st

from assets import Assets
from utils.types import DataModel, SessionReturn


async def render(assets: Assets, session: DataModel, name: str, spec: DataModel) -> SessionReturn:
    boxes = session.get(
        keys=spec,
        path='/key',
        value_type=dict,
    )['items']

    st.subheader(f'🏃 {spec.get(
        path='/labelTitle',
        value_type=str,
        default='Command',
    )}')
    st.text(f'* 노드 수: {len(boxes)}')

    # Show available commands
    commands = {
        'on': spec.get(
            path='/labelPowerOn',
            value_type=str,
            default='Power ON',
        ),
        'off': spec.get(
            path='/labelPowerOff',
            value_type=str,
            default='Power OFF',
        ),
        'reset': spec.get(
            path='/labelReset',
            value_type=str,
            default='Reboot',
        ),
    }

    # Select the command
    command = st.radio(
        key=f'{name}/command',
        label=spec.get(
            path='/label',
            value_type=str,
            default='Please choose one of the commands.',
        ),
        options=commands.keys(),
        format_func=lambda key: commands[key],
    )

    # Ask whether to command forcely
    force = st.checkbox(
        key=f'{name}/force',
        label=spec.get(
            path='/labelForce',
            value_type=str,
            default='Force',
        ),
    )

    # Execute
    execute = st.button(
        key=f'{name}/submit',
        label=spec.get(
            path='/labelSubmit',
            value_type=str,
            default='Submit',
        ),
    )
    if not execute:
        return {
            'state': 'Cancel',
        }

    with st.spinner('명령 실행 중...'):
        assets.widgets.actions.apply_kubernetes(
            name=name,
            namespace='kiss',
            spec=[
                {
                    'box': box,
                    'command': command,
                    'force': force,
                }
                for box in boxes
            ],
        )

    st.info(
        spec.get(
            path='/labelSuccess',
            value_type=str,
            default='Succeeded!',
        ),
    )

    return {
        'state': 'Ok',
    }
