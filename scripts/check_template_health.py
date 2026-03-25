#!/usr/bin/env python3
"""Verify that the template starter is operational after bootstrap."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


@dataclass(frozen=True)
class HealthCheck:
    path: str
    expected_keys: tuple[str, ...]


CHECKS = (
    HealthCheck("/api/v1/system/health/", ("status",)),
    HealthCheck("/api/v1/system/ready/", ("ready", "project")),
    HealthCheck("/api/v1/system/capabilities/", ("modules", "active_providers")),
    HealthCheck("/api/v1/system/providers/", ("providers",)),
    HealthCheck("/api/v1/system/general-settings/", tuple()),
)


def fetch_json(url: str) -> object:
    with urlopen(url, timeout=5) as response:  # noqa: S310 - local operator health check
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    errors: list[str] = []

    for check in CHECKS:
        try:
            payload = fetch_json(f"{base_url}{check.path}")
        except HTTPError as exc:
            errors.append(f"{check.path} returned HTTP {exc.code}")
            continue
        except URLError as exc:
            errors.append(f"{check.path} could not be reached: {exc.reason}")
            continue

        if not isinstance(payload, dict) and check.expected_keys:
            errors.append(f"{check.path} returned an unexpected payload shape")
            continue
        if isinstance(payload, dict):
            missing = [key for key in check.expected_keys if key not in payload]
            if missing:
                errors.append(f"{check.path} missing keys: {', '.join(missing)}")
        elif check.path.endswith("/general-settings/") and not isinstance(payload, list):
            errors.append(f"{check.path} should return a list")

    if errors:
        print("Template health check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Template health check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
