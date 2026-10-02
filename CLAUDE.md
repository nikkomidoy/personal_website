# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A personal career website built with Django 5.2 and Wagtail 7. All content is edited in the Wagtail admin at `/cms/`. The Django admin is at `/django-admin/`. The site deploys to AWS ECS Fargate through GitHub Actions, and all of the infrastructure is in `deploy/cloudformation.yml`.

## Commands

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py seed_demo          # placeholder content; does nothing if the home page already has experience entries
python manage.py runserver          # uses config.settings.dev by default (manage.py)

ruff check . && ruff format --check .   # lint (line length 120; migrations are excluded)
pytest                                  # all tests (pytest-django; settings come from pyproject.toml)
pytest tests/test_site.py::test_sitemap # one test
python manage.py makemigrations --check --dry-run   # CI fails if migrations are missing

# Check that the production settings import, as CI does:
DJANGO_SECRET_KEY=x DJANGO_ALLOWED_HOSTS=example.com python manage.py check --settings=config.settings.production
cfn-lint deploy/cloudformation.yml      # CI lints the CloudFormation template
docker compose up --build               # production image + Postgres, run locally
```

Locally the database is SQLite. Tests use Postgres when `DATABASE_URL` is set, as it is in CI.

## Architecture

**Settings** (`config/settings/`):
- `base.py` is shared by every environment. It picks the database in this order: `DATABASE_URL`, then the discrete `DB_*` variables (what ECS injects), then SQLite.
- `dev.py` hard-codes `DEBUG` and the secret key, and switches static storage to the plain backend so tests and runserver don't need `collectstatic`.
- `production.py` reads everything from environment variables (the full list is in `.env.example`). It trusts `X-Forwarded-Proto` because TLS terminates at the ALB, and it switches media storage to S3 when `AWS_STORAGE_BUCKET_NAME` is set. S3 credentials come from the ECS task role, never from keys.
- The WSGI entry point defaults to the production settings.

**Health check:** `core.middleware.HealthCheckMiddleware` must stay first in `MIDDLEWARE`. It answers `/health/` before host validation and the SSL redirect, because the ALB calls the task by its private IP.

**Content model:**
- `home.HomePage` is the single site root (`max_count = 1`). Its work history, education and skills are `Orderable` inline models (`Experience`, `Education`, `Skill`) that hang off it through `ParentalKey`.
- Skills are grouped by `category` in `HomePage.get_context`.
- Page nesting is enforced with `parent_page_types` and `subpage_types`: HomePage → StandardPage / BlogIndexPage → BlogPage / ProjectIndexPage → ProjectPage.
- Rich page bodies use the shared `core.blocks.BodyStreamBlock`. Each block's template is in `templates/blocks/`.
- Site-wide identity (name, contact links, résumé document) is the `core.models.SiteProfile` site setting. Every template reads it as `settings.core.SiteProfile` through the Wagtail settings context processor.
- The navigation lists the home page's live children that have `show_in_menus` ticked (`core/templatetags/navigation_tags.py`).
- `home/migrations/0002_create_homepage.py` replaces Wagtail's default "Welcome" page with a `HomePage` and points the default Site at it. It must set `locale` explicitly.

**Templates and static files:** templates live in the top-level `templates/` folder and are named `<app>/<model_snake_case>.html`, following Wagtail's convention. There is one CSS file (`static/css/site.css`) with light and dark tokens. In production, WhiteNoise serves static files out of the image; `collectstatic` runs at Docker build time.

## Deployment flow

- `ci.yml` runs on pull requests and is also called by `cd.yml` (`workflow_call`).
- `cd.yml` runs on pushes to `main`. It has no hard-coded AWS resource names; it reads them from the CloudFormation stack outputs. In order, it:
  1. Assumes `AWS_DEPLOY_ROLE_ARN` through GitHub OIDC. The role only trusts jobs in the `production` GitHub environment.
  2. Pushes the image to ECR tagged `<sha>` and `latest`.
  3. Fetches the latest task definition, swaps the `web` container's image, and registers a new revision.
  4. Runs `manage.py migrate` as a one-off Fargate task and fails the deploy if it exits non-zero.
  5. Runs `update-service` and waits for the service to be stable.
  6. Curls `/health/`.
- CloudFormation owns the task definition (environment variables, secrets, roles). To change runtime configuration, edit the template rather than the workflow. The container must keep the name `web`, because the workflow targets it by name.
- The stack is first created with `DesiredCount=0` because no image exists yet. Later stack updates must pass `DesiredCount=1`, or the service scales down to zero.
- Secrets (the Django key and DB credentials) come from Secrets Manager and are injected as environment variables. RDS password rotation is intentionally not enabled, because running tasks would keep the old password.
