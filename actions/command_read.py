import httpx
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import streamlit as st

from assets import Assets
from utils.types import DataModel, SessionReturn


async def render(assets: Assets, session: DataModel, name: str, spec: DataModel) -> SessionReturn:
    # Parse type
    type_ = spec.get(
        path='/type',
        value_type=str,
        default='CommandLine',
    )
    match type_:
        case 'CommandLine':
            reader = _draw_read_raw
        case 'ChatGPT':
            reader = _draw_read_chatgpt
        case _:
            st.error(f'Cannot infer command type: {type_}')
            return {
                'state': 'Err',
            }

    # Read a command line
    command = await reader(
        name=name,
        label=spec.get(
            path='/label',
            value_type=str,
            default='💲 Please enter the command.',
        ),
    )

    # Check command line
    command = _check_command(command)

    return {
        'state': 'Ok' if command is not None else 'Empty',
        'value': command,
    }


def _check_command(command: str | None) -> str | None:
    if command is None:
        return None

    command = command.strip()
    if not command:
        return None

    return command


async def _draw_read_chatgpt(name: str, label: str) -> str | None:
    input_context = _check_command(st.text_input(
        key=f'{name}.llm',
        label=label,
    ))
    if not input_context:
        return None

    with st.spinner('Running `ChatGPT`.'):
        command = _execute_chatgpt(input_context)
    if command is None:
        return None

    # Varify the response
    PROMPT = '$ '
    if not command.startswith(PROMPT):
        st.warning(command)
        return None
    return command[len(PROMPT):]


async def _draw_read_raw(name: str, label: str) -> str:
    return st.text_input(
        key=f'{name}.raw',
        label=label,
    )


@st.cache_data
def _execute_chatgpt(input_context: str) -> str | None:
    # Create a prompt template
    prompt = ChatPromptTemplate.from_messages([
        (
            'user',
            '[analyze: false, desktop-environment: xfce4, missing-variables: force-fill-default, os: linux, permanent: false, type: one-line shell command, write-with-prompt: $] {input_context}',
        ),
    ])
    chain = prompt

    # Connect a LLM model
    timeout = httpx.Timeout(
        1.0,
        connect=1.0,
    )
    llm = ChatOpenAI(
        http_async_client=httpx.AsyncClient(
            timeout=timeout,
        ),
        http_client=httpx.Client(
            timeout=timeout,
        ),
        # model='gpt-3.5-turbo',
        model='gpt-4-turbo-preview',
        streaming=True,
        temperature=0.1,
        timeout=1.0,
    )
    chain |= llm

    # Attach an output parser
    output_parser = StrOutputParser()
    chain |= output_parser

    # Execute the LLM chain with given context
    return chain.invoke({
        'input_context': input_context,
    }).replace('\n', ' ').strip()
