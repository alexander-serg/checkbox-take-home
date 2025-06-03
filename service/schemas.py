import textwrap

from datetime import datetime, time, date
from typing import Annotated, Literal, Self
from decimal import Decimal
from math import ceil

from pydantic import BaseModel, Field, StringConstraints, WrapSerializer, \
    computed_field, AnyUrl, SecretStr, model_validator, AfterValidator
from pydantic.dataclasses import dataclass
from fastapi.exceptions import RequestValidationError
from fastapi import Query, Depends

from service.utils import wrap_datetime, quantize_money
from service.config import settings


TrimmedStr = Annotated[str, StringConstraints(strip_whitespace=True)]

CheckTypeChoices = Literal['cash', 'cashless']

CheckTypeUkrMap: dict[CheckTypeChoices, str] = {
    'cash': 'готівка',
    'cashless': 'картка',
}
STORE_NAME = 'ФОП Джонсонюк Борис'
THANK_YOU_MSG = 'Дякуємо за покупку!'

OrderChoices = Literal[
    'created_at', '-created_at',
    'total', '-total'
]


class UserBase(BaseModel):
    full_name: Annotated[TrimmedStr, Field(min_length=1, max_length=255)]
    username: Annotated[TrimmedStr, Field(min_length=3, max_length=50)]


class UserIn(UserBase, extra='forbid'):
    password: Annotated[SecretStr, Field(min_length=12, max_length=128)]


class UserOut(UserBase, from_attributes=True):
    created_at: Annotated[datetime, WrapSerializer(wrap_datetime, return_type=str, when_used='json')]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Product(BaseModel, from_attributes=True, extra='forbid'):
    name: Annotated[TrimmedStr, Field(min_length=1, max_length=255)]
    price: Annotated[Decimal, Field(ge=0.00, decimal_places=2)]
    quantity: Annotated[Decimal, Field(ge=0, decimal_places=3)]

    @computed_field
    @property
    def total(self) -> Decimal:
        return quantize_money(self.price * self.quantity)

    def __format__(self, format_spec: str) -> str:
            width = int(format_spec) if format_spec else 40
            qty_price = f'{self.quantity:.3f} x {self.price:,.2f}'.ljust(width).rstrip()

            name_lines = textwrap.wrap(self.name.capitalize(), width=width)
            total_str = f'{self.total:,.2f}'

            last_name = name_lines[-1]
            space_remaining = width - len(last_name)
            if space_remaining > len(total_str):
                name_lines[-1] = f'{last_name}{total_str.rjust(space_remaining)}'
            else:
                name_lines.append(total_str.rjust(width))
            return "\n".join([qty_price, *name_lines])


class Payment(BaseModel, extra='forbid'):
    type: CheckTypeChoices
    amount: Annotated[Decimal, Field(ge=0.00, decimal_places=2)]

    def __format__(self, format_spec: str) -> str:
        width = int(format_spec) if format_spec else 40
        right = lambda label, val: f'{label}{val.rjust(width - len(label))}'
        return right(CheckTypeUkrMap[self.type].capitalize(), f'{self.amount:,.2f}')


class CheckBase(BaseModel):
    products: Annotated[list[Product], Field(min_length=1)]
    payment: Payment


class CheckIn(CheckBase, extra='forbid'):
    @computed_field
    @property
    def total(self) -> Decimal:
        total = sum(product.total for product in self.products)
        return quantize_money(total) if total else Decimal('0.00')

    @computed_field
    @property
    def rest(self) -> Decimal:
        return quantize_money(self.payment.amount - self.total)


class CheckOut(CheckBase, from_attributes=True):
    public_id: Annotated[str, Field(serialization_alias='id')]
    created_at: Annotated[datetime, WrapSerializer(wrap_datetime, return_type=str, when_used='json')]
    total: Annotated[Decimal, Field(ge=0.00, decimal_places=2)]
    rest: Annotated[Decimal, Field(ge=0.00, decimal_places=2)]

    @computed_field
    @property
    def public_url(self) -> AnyUrl:
        return AnyUrl.build(
            scheme=settings.host_url.scheme,
            host=settings.host_url.host,  # type: ignore
            port=settings.host_port,
            path=f'checks/{self.public_id}/view'
        )

    def __format__(self, format_spec: str) -> str:
            width = int(format_spec) if format_spec else 40
            bold_delim = '=' * width
            delim = '-' * width
            center = lambda s: s.center(width).rstrip()
            right = lambda label, val: f'{label}{val.rjust(width - len(label))}'
            lines = [
                center(STORE_NAME),
                bold_delim,
                f'\n{delim}\n'.join(
                    f'{product:{format_spec}}'
                    for product in self.products
                ),
                bold_delim,
                right('СУМА', f'{self.total:,.2f}'),
                f'{self.payment:{format_spec}}',
                right('Решта', f'{self.rest:,.2f}'),
                bold_delim,
                center(self.created_at.strftime('%d.%m.%Y %H:%M')),
                center(THANK_YOU_MSG),
            ]
            return '\n'.join(lines)


@dataclass
class CheckListFilters:
    payment_type: Annotated[CheckTypeChoices | None, Query()] = None
    created_at_start: Annotated[
        Annotated[
            date,
            AfterValidator(lambda date: datetime.combine(date, time.min))
        ] | datetime | None, Query()
    ] = None
    created_at_end: Annotated[
        Annotated[
            date,
            AfterValidator(lambda date: datetime.combine(date, time.max))
        ] | datetime | None, Query()
    ] = None
    total_start: Annotated[Decimal | None, Query(ge=0.00, decimal_places=2)] = None
    total_end: Annotated[Decimal | None, Query(ge=0.00, decimal_places=2)] = None

    @model_validator(mode='after')
    def validate_ranges(self) -> Self:
        errors = []

        self.check_range(self.created_at_start, self.created_at_end, 'created_at', errors)
        self.check_range(self.total_start, self.total_end, 'total', errors)

        if errors:
            raise RequestValidationError(errors)
        return self

    @staticmethod
    def make_error(loc: tuple[str, str], msg: str):
        return {
            'type': 'value_error',
            'loc': loc,
            'msg': msg,
            'input': None,
        }

    def check_range(self, start, end, field_name, errors):
        if start is not None and end is not None and start > end:
            msg = f"'{field_name}_start' should be less than or equal to the '{field_name}_end'"
            errors.append(self.make_error(('query', field_name), msg))


@dataclass
class CheckListParams:
    filters: CheckListFilters = Depends()
    order: Annotated[OrderChoices, Query()] = '-created_at'
    page: Annotated[int, Query(ge=1)] = 1
    page_size: Annotated[int, Query(ge=1, le=100)] = 25


class PageSchema(BaseModel):
    items: list[CheckOut]
    page: int
    page_size: int
    total: int

    @property
    def pages(self) -> int:
        if self.total == 0 or self.total is None:
            return 0
        return ceil(self.total / self.page_size)

    @computed_field
    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @computed_field
    @property
    def has_prev(self) -> bool:
        return self.page > 1
