import pytest
from decimal import Decimal
from fastapi.encoders import jsonable_encoder

from tests.consts import VIEW_URL, STANDART_CHECK, CHECK_20_WIDTH, CHECK_80_WIDTH
from tests.conftest import fake


class TestUserRegistration:
    async def test_register_user(self, client, user_data, db_session):
        response = await client.post('/users/register', json=user_data)
        assert response.status_code == 201
        resp_data = response.json()
        assert resp_data['username'] == user_data['username']
        assert resp_data['full_name'] == user_data['full_name']

    async def test_short_password(self, client, user_data, db_session):
        user_data['password'] = fake.password(length=4)
        response = await client.post('/users/register', json=user_data)
        assert response.status_code == 422
        assert response.json()['detail'][0]['msg'] == 'Value should have at least 12 items after validation, not 4'

    async def test_register_user_already_exists(self, client, user_data, user):
        response = await client.post('/users/register', json=user_data)
        assert response.status_code == 409
        assert response.json()['detail'] == f"A user with the username '{user_data['username']}' already exists."


class TestUserLogin:
    async def test_login_user(self, client, user_data, user):
        login_data = {'username': user_data['username'], 'password': user_data['password']}
        response = await client.post('/users/login', data=login_data)
        assert response.status_code == 200
        resp_data = response.json()
        assert 'access_token' in resp_data
        assert resp_data['token_type'].lower() == 'bearer'

    async def test_login_user_incorrect_password(self, client, user_data, user):
        login_data = {'username': user_data['username'], 'password': fake.password(length=12)}
        response = await client.post('/users/login', data=login_data)
        assert response.status_code == 401
        assert response.json()['detail'] == 'Incorrect username or password'

    async def test_login_user_not_found(self, client, user_data, db_session):
        login_data = {'username': user_data['username'], 'password': user_data['password']}
        response = await client.post('/users/login', data=login_data)
        assert response.status_code == 401
        assert response.json()['detail'] == 'Incorrect username or password'


class TestCheckCreate:
    async def test_auth_fail(self, client, headers, check_data):
        headers['Authorization'] = f'Bearer {fake.pystr()}'
        payload = {'products': check_data['products'], 'payment': check_data['payment']}
        response = await client.post('/checks/', json=jsonable_encoder(payload), headers=headers)
        assert response.status_code == 401
        assert response.json()['detail'] == 'Not Authenticated'

    async def test_create_check(self, client, headers, check_data):
        payload = {'products': check_data['products'], 'payment': check_data['payment']}
        response = await client.post('/checks/', json=jsonable_encoder(payload), headers=headers)
        assert response.status_code == 201
        resp_data = response.json()
        assert resp_data['total'] == str(check_data['total'])
        assert resp_data['rest'] == str(check_data['rest'])
        assert resp_data['payment']['type'] == check_data['payment']['type']
        assert resp_data['public_url'] == VIEW_URL.format(check_id=resp_data['id'])

    async def test_create_check_insufficient_payment(self, client, headers, check_data):
        payload = {'products': check_data['products'], 'payment': check_data['payment']}
        payload['payment']['amount'] = 1
        response = await client.post('/checks/', json=jsonable_encoder(payload), headers=headers)
        assert response.status_code == 400
        assert response.json()['detail'] == 'Insufficient payment amount'

    async def test_validation_error(self, client, headers, check_data, subtests):
        with subtests.test(msg='test_products_not_found'):
            payload = {'products': [], 'payment': check_data['payment']}
            response = await client.post('/checks/', json=jsonable_encoder(payload), headers=headers)
            print(response.content)
            assert response.status_code == 422
            assert response.json()['detail'][0]['msg'] == 'List should have at least 1 item after validation, not 0'

        with subtests.test(msg='test_wrong_payment_method'):
            payload = {'products': check_data['products'], 'payment': check_data['payment']}
            payload['payment']['type'] = 'wrong'
            response = await client.post('/checks/', json=jsonable_encoder(payload), headers=headers)
            print(response.content)
            assert response.status_code == 422
            assert response.json()['detail'][0]['msg'] == "Input should be 'cash' or 'cashless'"

        with subtests.test(msg='test_payment_missing'):
            payload = {'products': check_data['products'], 'payment': check_data['payment']}
            del payload['payment']
            response = await client.post('/checks/', json=jsonable_encoder(payload), headers=headers)
            print(response.content)
            assert response.status_code == 422
            assert response.json()['detail'][0]['msg'] == "Field required"

        with subtests.test(msg='test_wrong_quantity'):
            payload = {'products': check_data['products'], 'payment': check_data['payment']}
            payload['products'][0]['quantity'] = str('1.0001')
            response = await client.post('/checks/', json=jsonable_encoder(payload), headers=headers)
            print(response.content)
            assert response.status_code == 422
            assert response.json()['detail'][0]['msg'] == "Decimal input should have no more than 3 decimal places"


class TestCheckRetrieve:
    async def test_retrieve_check(self, client, headers, existing_check, check_data):
        response = await client.get(f'/checks/{existing_check.public_id}', headers=headers)
        assert response.status_code == 200
        resp_data = response.json()
        assert resp_data['id'] == existing_check.public_id
        assert resp_data['total'] == str(existing_check.total)
        assert resp_data['rest'] == str(existing_check.rest)
        assert resp_data['public_url'] == VIEW_URL.format(check_id=resp_data['id'])

    async def test_auth_fail(self, client, headers, existing_check, check_data):
        headers['Authorization'] = f'Bearer {fake.pystr()}'
        response = await client.get(f'/checks/{existing_check.public_id}', headers=headers)
        assert response.status_code == 401
        assert response.json()['detail'] == 'Not Authenticated'

    async def test_retrieve_check_not_found(self, client, headers):
        response = await client.get('/checks/non_existent_id', headers=headers)
        assert response.status_code == 404
        assert response.json()['detail'] == "Check with id 'non_existent_id' not found"


class TestCheckList:
    async def test_list_checks(self, client, headers, checks_collection, checks_collection_data):
        response = await client.get('/checks/', headers=headers)
        assert response.status_code == 200
        resp_data = response.json()
        assert len(resp_data['items']) == len(checks_collection_data)
        assert resp_data['total'] == len(checks_collection_data)

    async def test_auth_fail(self, client, headers, checks_collection, checks_collection_data):
        headers['Authorization'] = f'Bearer {fake.pystr()}'
        response = await client.post('/checks/', headers=headers)
        assert response.status_code == 401
        assert response.json()['detail'] == 'Not Authenticated'

    @pytest.mark.parametrize("direction", ['', '-'])
    async def test_order(self, client, headers, checks_collection, checks_collection_data, direction):
        response = await client.get(f'/checks/?order={direction}total', headers=headers)
        assert response.status_code == 200
        resp_data = response.json()
        items = resp_data['items']
        sorted_items = sorted(checks_collection_data, key=lambda x: x['total'], reverse=bool(direction))
        assert [item['id'] for item in items] == [item['id'] for item in sorted_items]

    async def test_filter(self, client, headers, checks_collection, checks_collection_data, subtests):
        with subtests.test(msg='test_type_filtering'):
            response = await client.get('/checks/?payment_type=cash', headers=headers)
            assert response.status_code == 200
            resp_data = response.json()
            assert len(resp_data['items']) == 1
            for item in resp_data['items']:
                assert item['payment']['type'] == 'cash'

        with subtests.test(msg='test_range_filtering'):
            response = await client.get('/checks/?total_start=100&total_end=2000', headers=headers)
            print(response.content)
            assert response.status_code == 200
            resp_data = response.json()
            assert len(resp_data['items']) == 2
            for item in resp_data['items']:
                assert 100 <= Decimal(item['total']) <= 2000

        with subtests.test(msg='test_range_error'):
            response = await client.get('/checks/?total_start=100&total_end=20', headers=headers)
            print(response.content)
            assert response.status_code == 422
            resp_data = response.json()
            assert response.json()['detail'][0]['msg'] == "'total_start' should be less than or equal to the 'total_end'"

    @pytest.mark.parametrize("page", [1, 2])
    async def test_pagination(self, client, headers, checks_collection, checks_collection_data, page):
        page_size = 2
        response = await client.get(f'/checks/?page_size={page_size}&page={page}', headers=headers)
        assert response.status_code == 200
        resp_data = response.json()
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        assert len(resp_data['items']) == len(checks_collection_data[start_index:end_index])
        assert resp_data['total'] == len(checks_collection_data)
        assert resp_data['page'] == page
        assert resp_data['page_size'] == page_size


class TestCheckView:
    async def test_view_check(self, client, existing_check, subtests):
        with subtests.test('test_standard_view'):
            response = await client.get(f'/checks/{existing_check.public_id}/view')
            assert response.status_code == 200
            assert response.text == STANDART_CHECK.format(
                created_at=existing_check.created_at.strftime('%d.%m.%Y %H:%M')
            )
        with subtests.test('test_20_width_view'):
            response = await client.get(f'/checks/{existing_check.public_id}/view?width=20')
            print(str(response.text))
            assert response.status_code == 200
            assert response.text == CHECK_20_WIDTH.format(
                created_at=existing_check.created_at.strftime('%d.%m.%Y %H:%M')
            )
        with subtests.test('test_80_width_view'):
            response = await client.get(f'/checks/{existing_check.public_id}/view?width=80')
            assert response.status_code == 200
            assert response.text == CHECK_80_WIDTH.format(
                created_at=existing_check.created_at.strftime('%d.%m.%Y %H:%M')
            )

    async def test_view_check_not_found(self, client, db_session):
        response = await client.get('/checks/non_existent_id/view')
        assert response.status_code == 404
        assert response.json()['detail'] == "Check with id 'non_existent_id' not found"
