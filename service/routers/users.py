import jwt

from datetime import datetime, timedelta, timezone
from typing import Annotated
from asyncpg.exceptions import UniqueViolationError
from sqlalchemy.exc import IntegrityError

from fastapi import APIRouter, Depends, status

from .. import schemas, models
from service.dependencies import DBSession, get_user_from_form
from service.config import settings
from service.utils import get_password_hash
from service.errors import AlreadyExistsError, AuthenticationFailedError


router = APIRouter(
    prefix='/users',
    tags=['users']
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    responses={exc.status_code: {'model': exc} for exc in [AlreadyExistsError]},
    response_model=schemas.UserOut

)
async def register_user(
    user: schemas.UserIn,
    db: DBSession
):
    password_hash = get_password_hash(user.password.get_secret_value())
    try:
        db_user = await models.User.create(session=db, user=user, password_hash=password_hash)
    except IntegrityError as e:
        error_type = getattr(e.orig, '__cause__')
        if isinstance(error_type, UniqueViolationError):
            raise AlreadyExistsError(detail=f"A user with the username '{user.username}' already exists.")
        raise e

    return db_user


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=schemas.Token,
    responses={exc.status_code: {'model': exc} for exc in [AuthenticationFailedError]},
)
async def login_user(
    user: Annotated[models.User, Depends(get_user_from_form)]
):
    payload = {
        'sub': f'username:{user.username}',
        'exp': datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    }
    access_token = jwt.encode(payload, settings.auth_secret_key, settings.jwt_algorithm)
    return {'access_token': access_token}
