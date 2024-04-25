import logging

import colorlog
from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
import streamlit as st


@st.cache_resource(ttl=None)
def init_opentelemetry() -> None:
    # exporter = OTLPLogExporter(
    #     insecure=True,
    # )

    # Init logger provider
    logger_provider = LoggerProvider()
    # logger_provider.add_log_record_processor(
    #     log_record_processor=BatchLogRecordProcessor(exporter),
    # )
    set_logger_provider(logger_provider)

    # Configure logger
    logging.basicConfig(
        level=logging.WARNING,
    )
    logger = logging.getLogger()
    while logger.handlers:
        logger.handlers.pop()

    # Set kubegraph logger level as INFO
    local_logger = logging.getLogger('kubegraph')
    local_logger.setLevel(logging.INFO)

    # Attach colored console handler to root logger
    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(colorlog.ColoredFormatter(
        fmt=r'%(thin_black)s%(asctime)s%(reset)s  '
            r'%(log_color)s%(levelname)s%(reset)s '
            r'%(bold_light_white)s%(name)s%(reset)s '
            r'%(message)s',
        datefmt=r'%FT%H:%M:%SZ',
    ))
    logger.addHandler(
        hdlr=console_handler,
    )

    # Attach OTLP handler to root logger
    logger.addHandler(
        hdlr=LoggingHandler(
            level=logging.NOTSET,
            logger_provider=logger_provider,
        ),
    )

    # Init meter provider
    meter_provider = MeterProvider()
    metrics.set_meter_provider(meter_provider)

    # Init tracer provider
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(
        BatchSpanProcessor(ConsoleSpanExporter()),
    )
    trace.set_tracer_provider(tracer_provider)
