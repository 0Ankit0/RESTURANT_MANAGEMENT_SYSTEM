# Template Release Checklist

Use this checklist when you are turning the boilerplate into a real project and want one last pass before treating it as your team’s base.

## Identity

- Rename `PROJECT_NAME` and `APP_INSTANCE_NAME` in [backend/.env.example](/Users/ankit/Projects/Python/fastapi/fastapi_template/backend/.env.example).
- Set `NEXT_PUBLIC_APP_NAME` in [frontend/.env.local.example](/Users/ankit/Projects/Python/fastapi/fastapi_template/frontend/.env.local.example).
- Set `PROJECT_NAME` in [mobile/.env.example](/Users/ankit/Projects/Python/fastapi/fastapi_template/mobile/.env.example).
- Review package and app identifiers in [backend/pyproject.toml](/Users/ankit/Projects/Python/fastapi/fastapi_template/backend/pyproject.toml), [frontend/package.json](/Users/ankit/Projects/Python/fastapi/fastapi_template/frontend/package.json), and [mobile/pubspec.yaml](/Users/ankit/Projects/Python/fastapi/fastapi_template/mobile/pubspec.yaml).

## Product Shape

- Choose which `FEATURE_*` modules remain enabled.
- Remove routes, pages, and docs for modules your project will never ship.
- Choose your primary providers for email, push, SMS, analytics, maps, and payments.

## Security And Operations

- Move secrets into your deployment secret manager.
- Review trusted hosts, proxy trust, cookies, rate limits, and suspicious-activity thresholds.
- Choose `local` or `s3` storage intentionally and verify media URLs.

## Validation

- Run `make setup`
- Run `make infra-up`
- Run `make backend-migrate`
- Run `make health-check`
- Run `make ci`

## Reading Path

- Read [docs/onboarding/project-orientation.md](/Users/ankit/Projects/Python/fastapi/fastapi_template/docs/onboarding/project-orientation.md)
- Read [docs/onboarding/template-finalization-checklist.md](/Users/ankit/Projects/Python/fastapi/fastapi_template/docs/onboarding/template-finalization-checklist.md)
- Read [docs/infrastructure/production-hardening-checklist.md](/Users/ankit/Projects/Python/fastapi/fastapi_template/docs/infrastructure/production-hardening-checklist.md)
