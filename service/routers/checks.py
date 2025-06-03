from typing import Annotated
from dataclasses import asdict

from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import PlainTextResponse

from .. import schemas, models
from service.dependencies import DBSession, get_user_from_token
from service.errors import NotFoundError, AuthenticationFailedError, InsufficientPaymentError


router = APIRouter(
    prefix='/checks',
    tags=['checks'],
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={exc.status_code: {'model': exc} for exc in [AuthenticationFailedError, InsufficientPaymentError]},
    response_model=schemas.CheckOut,
    response_model_by_alias=True
)
async def create_check(
    check: schemas.CheckIn,
    db: DBSession,
    user: Annotated[models.User, Depends(get_user_from_token)]
):
    if check.rest < 0:
        raise InsufficientPaymentError()

    db_check = await models.Check.create(session=db, user_id=user.id, check=check)
    return db_check


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    responses={exc.status_code: {'model': exc} for exc in [AuthenticationFailedError]},
    response_model=schemas.PageSchema,
    response_model_by_alias=True
)
async def list_checks(
    query_params: Annotated[schemas.CheckListParams, Depends()],
    db: DBSession,
    user: Annotated[models.User, Depends(get_user_from_token)]
):
    items, total = await models.Check.get_list(session=db, user_id=user.id, params=query_params)
    return {
        **asdict(query_params),
        'items': items,
        'total': total
    }


@router.get(
    "/{check_id}",
    status_code=status.HTTP_200_OK,
    responses={exc.status_code: {'model': exc} for exc in [NotFoundError, AuthenticationFailedError]},
    response_model=schemas.CheckOut,
    response_model_by_alias=True
)
async def retrieve_check(
    check_id: str,
    db: DBSession,
    user: Annotated[models.User, Depends(get_user_from_token)]
):
    check = await models.Check.get_by_id(session=db, user_id=user.id, public_id=check_id)
    if not check:
        raise NotFoundError(detail=f"Check with id '{check_id}' not found")
    return check


@router.get(
    "/{check_id}/view",
    status_code=status.HTTP_200_OK,
    responses={exc.status_code: {'model': exc} for exc in [NotFoundError]},
)
async def view_check(
    check_id: str,
    db: DBSession,
    width: int = Query(default=32, ge=20, le=80)
) -> PlainTextResponse:
    check_db = await models.Check.get_by_id(session=db, public_id=check_id)
    if not check_db:
        raise NotFoundError(detail=f"Check with id '{check_id}' not found")

    check = schemas.CheckOut.model_validate(check_db)
    content = f'{check:{width}}'
    return PlainTextResponse(content=content)
