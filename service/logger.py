import click
import logging

from contextvars import ContextVar

from fastapi import Request
from uvicorn.logging import AccessFormatter, ColourizedFormatter


ctx_request: ContextVar[Request] = ContextVar('request')


class UvicornAccessFormatter(AccessFormatter):

    def formatMessage(self, record: logging.LogRecord) -> str:
        InjectingFormatter.inject_request_data(record)
        return super().formatMessage(record)


class InjectingFormatter(ColourizedFormatter):

    @staticmethod
    def format_bind_params(params: dict) -> str:
        return ' '.join(f'[{key!r}: {value!r}]' for key, value in params.items())

    @classmethod
    def get_request_data(cls, request: Request | None) -> dict[str, str]:
        return {
            'request_id': click.style(request.state.id, italic=True) if request else 'N/A',
            'method': request.method if request else '',
            'path': request.scope['path'] if request else '',
            'bind_params': cls.format_bind_params(request.state.logger_bind_params) if request else ''
        }

    @classmethod
    def inject_request_data(cls, record: logging.LogRecord):
        request = ctx_request.get(None)
        request_data = cls.get_request_data(request)
        for key, value in request_data.items():
            setattr(record, key, value)
        record.message = click.style(record.message, bold=True)

    def formatMessage(self, record: logging.LogRecord) -> str:
        self.inject_request_data(record)
        return super().formatMessage(record)


logger = logging.getLogger('service')
