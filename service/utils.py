import uuid

from typing import Any
from dataclasses import is_dataclass
from baseconv import base62
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.routing import run_endpoint_function as original_run_endpoint_function
from fastapi.dependencies.models import Dependant
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from sqlalchemy.sql import expression
from sqlalchemy.types import DateTime
from sqlalchemy.ext.compiler import compiles
from pydantic import SerializerFunctionWrapHandler, BaseModel
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from service.logger import ctx_request, logger


password_hasher = PasswordHash(hashers=[Argon2Hasher()])


def get_password_hash(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password, password_hash) -> bool:
    return password_hasher.verify(password, password_hash)


def quantize_money(value: Decimal | int) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_base62uuid() -> str:
    uuid4_as_hex = str(uuid.uuid4()).replace('-', '')
    uuid4_as_int = int(uuid4_as_hex, 16)
    base62_str = base62.encode(uuid4_as_int)
    return base62_str.rjust(22, '0')


def generate_check_id() -> str:
    return f'ch_{generate_base62uuid()}'


def wrap_datetime(v: Any, nxt: SerializerFunctionWrapHandler) -> str:
    return f'{nxt(v)}Z'


class UtcNow(expression.FunctionElement):
    type = DateTime()
    inherit_cache = True


@compiles(UtcNow, 'postgresql')
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


class LogRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        request.state.id = request_id
        request.state.logger_bind_params = {}
        ctx_request.set(request)
        response = await call_next(request)
        return response


async def http_exception_logger(request: Request, exc: HTTPException) -> JSONResponse:
    logger.warning('HTTP Exception: %s', exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={'detail': exc.detail},
        headers=exc.headers
    )


async def request_response_logger(
        *,
        dependant: Dependant,
        values: dict[str, Any],
        is_coroutine: bool,
    ) -> Any:
        request = ctx_request.get(None)
        if request:
            log_values = {
                key: value for key, value in values.items()
                if isinstance(value, BaseModel) or is_dataclass(value)
            }
            request.state.logger_bind_params.update(log_values)
            logger.info('New Request Received')

        return await original_run_endpoint_function(
            dependant=dependant, values=values, is_coroutine=is_coroutine
        )
