# social-media-backend-django

Django + Django REST Framework implementation of the shared social-media API. One of two
interchangeable backends — it satisfies the same
[API contract](../social-media-deploy/API_CONTRACT.md) as `social-media-backend-fastapi`.

> For the full-stack local setup, see the **[deploy repo README](../social-media-deploy/README.md)**.
> This file covers running the Django backend on its own.

## Stack
- Django 5 + Django REST Framework
- SimpleJWT (auth) · drf-spectacular (OpenAPI/Swagger) · django-environ (config) · PostgreSQL

## Layout
```
config/                 # split settings (base/local/production), urls, wsgi/asgi
apps/
├── common/             # contract error envelope, pagination, pluggable notifiers, health
├── users/              # custom User, VerificationCode, Follow; auth flow; profile/follow; seed cmd
└── posts/              # Post / Like / Comment; annotated feed ViewSet
```

## Run standalone (outside Docker)
```bash
cp .env.example .env                 # set DATABASE_URL to a reachable Postgres (db: social_django)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed                # demo data — login ada / hunter2x!
python manage.py runserver 0.0.0.0:8000
```

## Common commands
| Command | Purpose |
|---|---|
| `python manage.py makemigrations` | Generate migrations after model changes |
| `python manage.py migrate` | Apply migrations |
| `python manage.py seed` | Seed demo users/posts (idempotent) |
| `python manage.py createsuperuser` | Create an admin user |

## Endpoints
- API under `/api/` (see the [contract](../social-media-deploy/API_CONTRACT.md))
- Swagger UI: `/docs/` · schema: `/schema/`
- Django admin: `/admin/` (seed creates `admin` / `admin`)

## Notes
- `User.is_active` stays `False` until **every** registered contact (email and/or phone) is verified.
- Verification codes are hashed at rest; plaintext is stored only when `ENV=dev` for the dev-only
  `/api/dev/last-code` auto-fill endpoint.
- Code delivery is pluggable via `NOTIFIER` (`console` default → logs; `smtp` / `twilio` optional).
