# Checkbox Take Home

> Version 0.1.0

## Path Table

| Method | Path | Description |
| --- | --- | --- |
| POST | [/users/register](#postusersregister) | Register User |
| POST | [/users/login](#postuserslogin) | Login User |
| POST | [/checks/](#postchecks) | Create Check |
| GET | [/checks/](#getchecks) | List Checks |
| GET | [/checks/{check_id}](#getcheckscheck_id) | Retrieve Check |
| GET | [/checks/{check_id}/view](#getcheckscheck_idview) | View Check |

## Reference Table

| Name | Path | Description |
| --- | --- | --- |
| AlreadyExistsError | [#/components/schemas/AlreadyExistsError](#componentsschemasalreadyexistserror) |  |
| AuthenticationFailedError | [#/components/schemas/AuthenticationFailedError](#componentsschemasauthenticationfailederror) |  |
| Body_login_user_users_login_post | [#/components/schemas/Body_login_user_users_login_post](#componentsschemasbody_login_user_users_login_post) |  |
| CheckIn | [#/components/schemas/CheckIn](#componentsschemascheckin) |  |
| CheckOut | [#/components/schemas/CheckOut](#componentsschemascheckout) |  |
| HTTPValidationError | [#/components/schemas/HTTPValidationError](#componentsschemashttpvalidationerror) |  |
| InsufficientPaymentError | [#/components/schemas/InsufficientPaymentError](#componentsschemasinsufficientpaymenterror) |  |
| NotFoundError | [#/components/schemas/NotFoundError](#componentsschemasnotfounderror) |  |
| PageSchema | [#/components/schemas/PageSchema](#componentsschemaspageschema) |  |
| Payment-Input | [#/components/schemas/Payment-Input](#componentsschemaspayment-input) |  |
| Payment-Output | [#/components/schemas/Payment-Output](#componentsschemaspayment-output) |  |
| Product-Input | [#/components/schemas/Product-Input](#componentsschemasproduct-input) |  |
| Product-Output | [#/components/schemas/Product-Output](#componentsschemasproduct-output) |  |
| Token | [#/components/schemas/Token](#componentsschemastoken) |  |
| UserIn | [#/components/schemas/UserIn](#componentsschemasuserin) |  |
| UserOut | [#/components/schemas/UserOut](#componentsschemasuserout) |  |
| ValidationError | [#/components/schemas/ValidationError](#componentsschemasvalidationerror) |  |
| OAuth2PasswordBearer | [#/components/securitySchemes/OAuth2PasswordBearer](#componentssecurityschemesoauth2passwordbearer) |  |

## Path Details

***

### [POST]/users/register

- Summary  
Register User

#### RequestBody

- application/json

```ts
{
  full_name: string
  username: string
  password: string
}
```

#### Responses

- 201 Successful Response

`application/json`

```ts
{
  full_name: string
  username: string
  created_at: string
}
```

- 409 Conflict

`application/json`

```ts
{
  detail?: string //default: Already Exists
  headers?: Partial({
   }) & Partial(null)
}
```

- 422 Validation Error

`application/json`

```ts
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

***

### [POST]/users/login

- Summary  
Login User

#### RequestBody

- application/x-www-form-urlencoded

```ts
{
  grant_type?: Partial(string) & Partial(null)
  username: string
  password: string
  scope?: string
  client_id?: Partial(string) & Partial(null)
  client_secret?: Partial(string) & Partial(null)
}
```

#### Responses

- 200 Successful Response

`application/json`

```ts
{
  access_token: string
  token_type?: string //default: bearer
}
```

- 401 Unauthorized

`application/json`

```ts
{
  detail?: string //default: Not Authenticated
  headers: {
  }
}
```

- 422 Validation Error

`application/json`

```ts
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

***

### [POST]/checks/

- Summary  
Create Check

- Security  
OAuth2PasswordBearer  

#### RequestBody

- application/json

```ts
{
  products: {
    name: string
    price: Partial(number) & Partial(string)
    quantity: Partial(number) & Partial(string)
  }[]
  payment: {
    type: enum[cash, cashless]
    amount: Partial(number) & Partial(string)
  }
}
```

#### Responses

- 201 Successful Response

`application/json`

```ts
{
  products: {
    name: string
    price: string
    quantity: string
    total: string
  }[]
  payment: {
    type: enum[cash, cashless]
    amount: string
  }
  id: string
  created_at: string
  total: string
  rest: string
  public_url: string
}
```

- 400 Bad Request

`application/json`

```ts
{
  headers?: Partial({
   }) & Partial(null)
}
```

- 401 Unauthorized

`application/json`

```ts
{
  detail?: string //default: Not Authenticated
  headers: {
  }
}
```

- 422 Validation Error

`application/json`

```ts
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

***

### [GET]/checks/

- Summary  
List Checks

- Security  
OAuth2PasswordBearer  

#### Parameters(Query)

```ts
order?: enum[created_at, -created_at, total, -total] //default: -created_at
```

```ts
page?: integer //default: 1
```

```ts
page_size?: integer //default: 25
```

```ts
payment_type?: Partial(string) & Partial(null)
```

```ts
created_at_start?: Partial(string) & Partial(string) & Partial(null)
```

```ts
created_at_end?: Partial(string) & Partial(string) & Partial(null)
```

```ts
total_start?: Partial(number) & Partial(string) & Partial(null)
```

```ts
total_end?: Partial(number) & Partial(string) & Partial(null)
```

#### Responses

- 200 Successful Response

`application/json`

```ts
{
  items: {
    products: {
      name: string
      price: string
      quantity: string
      total: string
    }[]
    payment: {
      type: enum[cash, cashless]
      amount: string
    }
    id: string
    created_at: string
    total: string
    rest: string
    public_url: string
  }[]
  page: integer
  page_size: integer
  total: integer
  has_next: boolean
  has_prev: boolean
}
```

- 401 Unauthorized

`application/json`

```ts
{
  detail?: string //default: Not Authenticated
  headers: {
  }
}
```

- 422 Validation Error

`application/json`

```ts
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

***

### [GET]/checks/{check_id}

- Summary  
Retrieve Check

- Security  
OAuth2PasswordBearer  

#### Responses

- 200 Successful Response

`application/json`

```ts
{
  products: {
    name: string
    price: string
    quantity: string
    total: string
  }[]
  payment: {
    type: enum[cash, cashless]
    amount: string
  }
  id: string
  created_at: string
  total: string
  rest: string
  public_url: string
}
```

- 401 Unauthorized

`application/json`

```ts
{
  detail?: string //default: Not Authenticated
  headers: {
  }
}
```

- 404 Not Found

`application/json`

```ts
{
  detail?: string //default: Not Found
  headers?: Partial({
   }) & Partial(null)
}
```

- 422 Validation Error

`application/json`

```ts
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

***

### [GET]/checks/{check_id}/view

- Summary  
View Check

#### Parameters(Query)

```ts
width?: integer //default: 32
```

#### Responses

- 200 Successful Response

`application/json`

```ts
{}
```

- 404 Not Found

`application/json`

```ts
{
  detail?: string //default: Not Found
  headers?: Partial({
   }) & Partial(null)
}
```

- 422 Validation Error

`application/json`

```ts
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

## References

### #/components/schemas/AlreadyExistsError

```ts
{
  detail?: string //default: Already Exists
  headers?: Partial({
   }) & Partial(null)
}
```

### #/components/schemas/AuthenticationFailedError

```ts
{
  detail?: string //default: Not Authenticated
  headers: {
  }
}
```

### #/components/schemas/Body_login_user_users_login_post

```ts
{
  grant_type?: Partial(string) & Partial(null)
  username: string
  password: string
  scope?: string
  client_id?: Partial(string) & Partial(null)
  client_secret?: Partial(string) & Partial(null)
}
```

### #/components/schemas/CheckIn

```ts
{
  products: {
    name: string
    price: Partial(number) & Partial(string)
    quantity: Partial(number) & Partial(string)
  }[]
  payment: {
    type: enum[cash, cashless]
    amount: Partial(number) & Partial(string)
  }
}
```

### #/components/schemas/CheckOut

```ts
{
  products: {
    name: string
    price: string
    quantity: string
    total: string
  }[]
  payment: {
    type: enum[cash, cashless]
    amount: string
  }
  id: string
  created_at: string
  total: string
  rest: string
  public_url: string
}
```

### #/components/schemas/HTTPValidationError

```ts
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

### #/components/schemas/InsufficientPaymentError

```ts
{
  headers?: Partial({
   }) & Partial(null)
}
```

### #/components/schemas/NotFoundError

```ts
{
  detail?: string //default: Not Found
  headers?: Partial({
   }) & Partial(null)
}
```

### #/components/schemas/PageSchema

```ts
{
  items: {
    products: {
      name: string
      price: string
      quantity: string
      total: string
    }[]
    payment: {
      type: enum[cash, cashless]
      amount: string
    }
    id: string
    created_at: string
    total: string
    rest: string
    public_url: string
  }[]
  page: integer
  page_size: integer
  total: integer
  has_next: boolean
  has_prev: boolean
}
```

### #/components/schemas/Payment-Input

```ts
{
  type: enum[cash, cashless]
  amount: Partial(number) & Partial(string)
}
```

### #/components/schemas/Payment-Output

```ts
{
  type: enum[cash, cashless]
  amount: string
}
```

### #/components/schemas/Product-Input

```ts
{
  name: string
  price: Partial(number) & Partial(string)
  quantity: Partial(number) & Partial(string)
}
```

### #/components/schemas/Product-Output

```ts
{
  name: string
  price: string
  quantity: string
  total: string
}
```

### #/components/schemas/Token

```ts
{
  access_token: string
  token_type?: string //default: bearer
}
```

### #/components/schemas/UserIn

```ts
{
  full_name: string
  username: string
  password: string
}
```

### #/components/schemas/UserOut

```ts
{
  full_name: string
  username: string
  created_at: string
}
```

### #/components/schemas/ValidationError

```ts
{
  loc?: Partial(string) & Partial(integer)[]
  msg: string
  type: string
}
```

### #/components/securitySchemes/OAuth2PasswordBearer

```ts
{
  "type": "oauth2",
  "flows": {
    "password": {
      "scopes": {},
      "tokenUrl": "users/login"
    }
  }
}
```