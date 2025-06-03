import os
import pytest
import datetime
import jwt

from unittest.mock import patch
from decimal import Decimal

from httpx import ASGITransport, AsyncClient
from pytest_postgresql import factories
from faker import Faker

from tests.consts import ENV_VARS, VIEW_URL


fake = Faker()
postgresql_proc = factories.postgresql_proc(port=ENV_VARS['DATABASE_PORT'], dbname=ENV_VARS['DATABASE_NAME'])
postgresql = factories.postgresql('postgresql_proc', ENV_VARS['DATABASE_NAME'])


with patch.dict(os.environ, ENV_VARS):
    from service.config import db_engine, async_session_factory
    from service.main import app
    from service.models import Base, User, Check, CheckProduct
    from service.utils import get_password_hash


@pytest.fixture
async def init_db(postgresql):
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture
async def db_session(init_db):
    async with async_session_factory() as session:
        yield session


@pytest.fixture(autouse=True)
def anyio_backend():
    return 'asyncio'


@pytest.fixture
async def client():
    async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://"
    ) as ac:
        yield ac


# # @pytest.fixture
# # def identity_headers(account, user):
# #     return {
# #         'X-Account-ID': str(account.id),
# #         'X-User-ID': str(user.id)
# #     }


# # @pytest.fixture
# # async def reseted_payment_method(db_session, account):
# #     account.active_payment = False
# #     await db_session.commit()


@pytest.fixture
def user_data():
    profile = fake.simple_profile()
    return {
        'username': profile['username'],
        'full_name': profile['name'],
        'password': fake.password(length=12)
    }


@pytest.fixture
async def user(db_session, user_data):
    user = User(
        username=user_data['username'],
        full_name=user_data['full_name'],
        password_hash=get_password_hash(user_data['password'])
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user



@pytest.fixture
async def user_token(user):
    payload = {
        'sub': f'username:{user.username}',
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=1)
    }
    access_token = jwt.encode(payload, ENV_VARS['AUTH_SECRET_KEY'], 'HS256')
    return access_token


@pytest.fixture
async def headers(user_token):
    return {'Authorization': f'Bearer {user_token}'}


@pytest.fixture
def check_data():
    check = {
        'id': fake.pystr(prefix='ch_', min_chars=22, max_chars=22),
        'total': Decimal('52.77'),
        'rest': Decimal('47.23'),
        'payment': {
            'amount': Decimal('100.00'),
            'type': 'cash'
         },
        'products': [
            {
                'name': 'олія соняшникова нерафінована холодного віджиму',
                'price': Decimal('7.77'),
                'quantity': Decimal('1.337'),
            },
            {
                'name': 'органічне борошно пшеничне вищого ґатунку',
                'price': Decimal('42.42'),
                'quantity': Decimal('0.999'),
            }
        ]
    }
    return check


async def add_check_to_db(db_session, user, check_data):
    check = Check(
        public_id=check_data['id'],
        user_id=user.id,
        total=check_data['total'],
        rest=check_data['rest'],
        payment_type=check_data['payment']['type'],
        payment_amount=check_data['payment']['amount']
    )
    db_session.add(check)
    await db_session.flush()
    products = (
        CheckProduct(
            check_id=check.id,
            name=product['name'],
            price=product['price'],
            quantity=product['quantity']
        )
        for product in check_data['products']
    )
    db_session.add_all(products)
    return check


@pytest.fixture
async def existing_check(db_session, user, check_data):
    check = await add_check_to_db(db_session, user, check_data)
    await db_session.commit()
    await db_session.refresh(check)
    return check


@pytest.fixture
def checks_collection_data():
    checks = [
        {
            'id': fake.pystr(prefix='ch_', min_chars=22, max_chars=22),
            'total': Decimal('2000.00'),
            'rest': Decimal('00.00'),
            'payment': {
                'amount': Decimal('2000.00'),
                'type': 'cashless'
            },
            'products': [
                {
                    'name': 'apple',
                    'price': Decimal('20.00'),
                    'quantity': Decimal('100.000'),
                }
            ]
        },
        {
            'id': fake.pystr(prefix='ch_', min_chars=22, max_chars=22),
            'total': Decimal('200.00'),
            'rest': Decimal('00.00'),
            'payment': {
                'amount': Decimal('200.00'),
                'type': 'cashless'
            },
            'products': [
                {
                    'name': 'apple',
                    'price': Decimal('20.00'),
                    'quantity': Decimal('10.000'),
                }
            ]
        },
        {
            'id': fake.pystr(prefix='ch_', min_chars=22, max_chars=22),
            'total': Decimal('20.00'),
            'rest': Decimal('00.00'),
            'payment': {
                'amount': Decimal('20.00'),
                'type': 'cash'
            },
            'products': [
                {
                    'name': 'apple',
                    'price': Decimal('20.00'),
                    'quantity': Decimal('1.000'),
                }
            ]
        }
    ]
    for check in checks:
        check['public_url'] = VIEW_URL.format(check_id=check['id'])
    return checks


@pytest.fixture
async def checks_collection(db_session, user, checks_collection_data):
    for check_data in checks_collection_data:
        await add_check_to_db(db_session, user, check_data)
    await db_session.commit()
