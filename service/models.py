import datetime

from typing import Sequence, Self, cast, get_args
from decimal import Decimal

from sqlalchemy import ForeignKey, select, Select, and_, \
    Numeric, Index, CHAR, String, Enum, func
from sqlalchemy.sql import ColumnExpressionArgument
from sqlalchemy.sql.operators import eq, asc_op, desc_op, ge, le, OperatorType
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession

from . import schemas
from service.utils import UtcNow, generate_base62uuid


class Base(DeclarativeBase):
    pass


class User(Base):

    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime.datetime] = mapped_column(default=UtcNow())

    @classmethod
    async def create(cls, session: AsyncSession, user: schemas.UserIn, password_hash: str) -> Self:
        db_user = cls(**user.model_dump(exclude={'password'}), password_hash=password_hash)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user

    @classmethod
    async def get_by_username(cls, session: AsyncSession, username: str) -> Self | None:
        return await session.scalar(
            select(cls)
            .where(cls.username == username)
        )


class CheckProduct(Base):

    __tablename__ = "check_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    check_id: Mapped[int] = mapped_column(ForeignKey('checks.id'))
    name: Mapped[str] = mapped_column(String(255))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3))


class Check(Base):

    __tablename__ = "checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(
        CHAR(25), unique=True, index=True,
        default=lambda: f'ch_{generate_base62uuid()}'
    )
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    rest: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime.datetime] = mapped_column(default=UtcNow())

    payment_type: Mapped[schemas.CheckTypeChoices] = mapped_column(Enum(
        *get_args(schemas.CheckTypeChoices),
        name='check_payment_type',
        create_constraint=True,
        validate_string=True
    ))
    payment_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    products: Mapped[list[CheckProduct]] = relationship(lazy='selectin')

    @property
    def payment(self) -> schemas.Payment:
        return schemas.Payment.model_validate(
            {'type': self.payment_type, 'amount': self.payment_amount}
        )

    @payment.setter
    def payment(self, value: dict):
        self.payment_amount = value['amount']
        self.payment_type = value['type']

    @classmethod
    async def create(cls, session: AsyncSession, user_id: int, check: schemas.CheckIn) -> Self:
        db_check = cls(
            **check.model_dump(exclude={'products'}),
            user_id=user_id
        )
        session.add(db_check)
        await session.flush()
        session.add_all(
            CheckProduct(
                check_id=db_check.id,
                name=product.name,
                price=product.price,
                quantity=product.quantity
            )
            for product in check.products
        )
        await session.commit()
        await session.refresh(db_check)
        return db_check

    @classmethod
    async def get_by_id(cls, session: AsyncSession, public_id: str, user_id: int | None = None) -> Self | None:
        stmt = select(cls).where(cls.public_id == public_id)
        if user_id:
            stmt = stmt.where(cls.user_id == user_id)
        return await session.scalar(stmt)

    @classmethod
    async def get_list(
            cls,
            session: AsyncSession,
            user_id: int,
            params: schemas.CheckListParams
    ) -> tuple[Sequence[Self], int | None]:
        init_stmt = select(cls) \
            .where(cls.user_id == user_id)

        page_stmt = cls.ListStmtBuilder(init_stmt=init_stmt, params=params) \
            .add_filters().add_order().add_pagination() \
            .build()

        res = await session.scalars(page_stmt)
        items = res.all()
        total = await session.scalar(
            select(func.count()).select_from(
                page_stmt.order_by(None).limit(None).offset(None)
                .subquery()
            )
        )
        return items, total

    class ListStmtBuilder:

        RANGE_SUFFIXES = {
            '_start': ge,
            '_end': le,
        }

        def __init__(self, init_stmt: Select, params: schemas.CheckListParams):
            self.stmt = init_stmt
            self.params = params

        def _extract_field_and_operator(self, field_name: str) -> tuple[str, OperatorType]:
            for suffix, op in self.RANGE_SUFFIXES.items():
                if field_name.endswith(suffix):
                    return field_name.removesuffix(suffix), op

            return field_name, eq

        def add_filters(self) -> Self:
            filters = self.params.filters

            conditions = [
                getattr(Check, field).operate(op, value)
                for raw_field, value in vars(filters).items()
                if value is not None
                for field, op in [self._extract_field_and_operator(raw_field)]
            ]

            if conditions:
                self.stmt = self.stmt.where(and_(*conditions))
            return self

        def add_order(self) -> Self:
            direction_op = desc_op if self.params.order.startswith('-') else asc_op
            self.stmt = self.stmt.order_by(
                cast(ColumnExpressionArgument, direction_op(
                    getattr(Check, self.params.order.removeprefix('-'))
                ))
            )
            return self

        def add_pagination(self) -> Self:
            offset = (self.params.page - 1) * self.params.page_size
            self.stmt = self.stmt.limit(self.params.page_size).offset(offset)
            return self

        def build(self) -> Select:
            return self.stmt


Index("idx_checks_created_at_desc", Check.created_at.desc())
