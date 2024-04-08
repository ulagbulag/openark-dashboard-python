import jsonpointer
import streamlit as st

from utils.types import Session, Spec
from utils.widgets import Widgets


async def render(widgets: Widgets, session: Session, name: str, spec: Spec) -> Session:
    # Get metadata
    boxes = jsonpointer.resolve_pointer(session, spec['key'])['items']

    st.subheader(f'🏃 {spec.get('labelTitle', 'Command')}')
    st.text(f'* 노드 수: {len(boxes)}')

    # Show available commands
    commands = {
        'on': spec.get('labelPowerOn', 'Power ON'),
        'off': spec.get('labelPowerOff', 'Power OFF'),
        'reset': spec.get('labelReset', 'Reboot'),
    }

    # Select the command
    command = st.radio(
        key=f'{name}/command',
        label=spec.get('label', 'Please choose one of the commands.'),
        options=commands.keys(),
        format_func=lambda key: commands[key],
    )

    # Ask whether to command forcely
    force = st.checkbox(
        key=f'{name}/force',
        label=spec.get('labelForce', 'Force'),
    )

    # Execute
    execute = st.button(
        key=f'{name}/submit',
        label=spec.get('labelSubmit', 'Submit'),
    )
    if not execute:
        return {
            'state': 'Cancel',
        }

    with st.spinner('명령 실행 중...'):
        widgets.actions.apply_kubernetes(
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

    st.info(spec.get('labelSuccess', 'Succeeded!'))

    return {
        'state': 'Ok',
    }
