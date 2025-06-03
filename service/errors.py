from typing import ClassVar

from dataclasses import field
from pydantic.dataclasses import dataclass
from fastapi import HTTPException, status


@dataclass
class AuthenticationFailedError(HTTPException):
    status_code: ClassVar[int] = status.HTTP_401_UNAUTHORIZED
    detail: str = 'Not Authenticated'
    headers: dict = field(default_factory=lambda: {"WWW-Authenticate": "Bearer"})


@dataclass
class NotFoundError(HTTPException):
    status_code: ClassVar[int] = status.HTTP_404_NOT_FOUND
    detail: str = 'Not Found'
    headers: dict | None = None


@dataclass
class AlreadyExistsError(HTTPException):
    status_code: ClassVar[int] = status.HTTP_409_CONFLICT
    detail: str = 'Already Exists'
    headers: dict | None = None


@dataclass
class InsufficientPaymentError(HTTPException):
    status_code: ClassVar[int] = status.HTTP_400_BAD_REQUEST
    detail="Insufficient payment amount"
    headers: dict | None = None
