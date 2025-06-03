from typing import cast

from fastapi import FastAPI, HTTPException
import fastapi.routing

from starlette.types import ExceptionHandler

from service.utils import LogRequestMiddleware, http_exception_logger, request_response_logger
from service.routers import users, checks


fastapi.routing.run_endpoint_function = request_response_logger

app = FastAPI(title='Checkbox Take Home')
app.include_router(users.router)
app.include_router(checks.router)
app.add_middleware(LogRequestMiddleware)  # type: ignore
app.add_exception_handler(HTTPException, cast(ExceptionHandler, http_exception_logger))
