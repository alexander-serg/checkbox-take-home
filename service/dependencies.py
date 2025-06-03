import jwt

from jwt.exceptions import InvalidTokenError

from typing import Annotated, AsyncIterator

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from . import models
from service.config import async_session_factory
from service.utils import verify_password
from service.config import settings
from service.errors import AuthenticationFailedError


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login", auto_error=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session


DBSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_user_from_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DBSession
) -> models.User:
    user = await models.User.get_by_username(session=db, username=form_data.username)
    if user and verify_password(form_data.password, user.password_hash):
        return user

    raise AuthenticationFailedError(detail='Incorrect username or password')


async def validate_access_token(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)]
) -> str:
    token = await oauth2_scheme(request)
    if not token:
        raise AuthenticationFailedError()

    try:
        payload = jwt.decode(token, settings.auth_secret_key, algorithms=[settings.jwt_algorithm])
    except InvalidTokenError:
        raise AuthenticationFailedError()

    if sub := payload.get('sub'):
        if sub.startswith('username:'):
            return sub.removeprefix('username:')

    raise AuthenticationFailedError()


async def get_user_from_token(
    username: Annotated[str, Depends(validate_access_token)],
    db: DBSession
) -> models.User:
    user = await models.User.get_by_username(session=db, username=username)
    if user:
        return user

    raise AuthenticationFailedError()
