# API Testing Quick Guide

Authenticate with JWT:

```text
POST /api/token/
Content-Type: application/json

{"username": "reader", "password": "Pass12345!"}
```

Use the returned access token as:

```text
Authorization: Bearer <access-token>
```

Useful endpoints:

- GET `/api/articles/`
- GET `/api/articles/subscribed/`
- GET `/api/articles/<id>/`
- POST `/api/articles/` (Journalist)
- PUT `/api/articles/<id>/` (Editor or owning Journalist)
- DELETE `/api/articles/<id>/` (Editor or owning Journalist)
- GET `/api/newsletters/`
- POST `/api/newsletters/` (Journalist)
- GET `/api/publishers/`
- GET `/api/users/`

The internal approval integration uses:

- POST `/api/approved/`
- Header `X-Internal-API-Key`

Automated tests are in `news/tests.py`.
Run them with:

```text
python manage.py test
```
