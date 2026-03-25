#!/usr/bin/env python3
"""Validate template documentation completeness and minimum quality."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs"

REQUIRED_README_HEADINGS = [
    "Documentation Structure",
    "Key Features",
    "Getting Started",
    "Documentation Status",
]

REQUIRED_FILES = {
    "requirements": ["requirements.md", "user-stories.md"],
    "analysis": [
        "use-case-diagram.md",
        "use-case-descriptions.md",
        "system-context-diagram.md",
        "activity-diagrams.md",
        "swimlane-diagrams.md",
        "data-dictionary.md",
        "business-rules.md",
        "event-catalog.md",
    ],
    "high-level-design": [
        "system-sequence-diagrams.md",
        "domain-model.md",
        "data-flow-diagrams.md",
        "architecture-diagram.md",
        "c4-diagrams.md",
    ],
    "detailed-design": [
        "class-diagrams.md",
        "sequence-diagrams.md",
        "state-machine-diagrams.md",
        "erd-database-schema.md",
        "component-diagrams.md",
        "api-design.md",
        "c4-component-diagram.md",
    ],
    "infrastructure": [
        "deployment-diagram.md",
        "network-infrastructure.md",
        "cloud-architecture.md",
        "environment-configuration.md",
        "ci-cd.md",
        "production-hardening-checklist.md",
    ],
    "edge-cases": [
        "README.md",
        "authentication-and-sessions.md",
        "multi-tenancy.md",
        "notifications.md",
        "payments.md",
        "websockets.md",
        "api-and-ui.md",
        "security-and-compliance.md",
        "operations.md",
    ],
    "implementation": [
        "working-principles.md",
        "implementation-guidelines.md",
        "communications-provider-matrix.md",
        "c4-code-diagram.md",
        "implementation-playbook.md",
        "test-strategy.md",
        "release-checklist.md",
    ],
    "onboarding": [
        "local-setup.md",
        "provider-configuration.md",
        "configuration-management.md",
        "environment-profiles.md",
        "deployment.md",
        "project-orientation.md",
        "start-a-new-project.md",
        "modifying-the-template.md",
        "template-finalization-checklist.md",
    ],
}

REQUIRED_DOC_HEADINGS = {
    "docs/onboarding/project-orientation.md": [
        "What This Template Is",
        "The Configuration Flow",
        "Recommended Reading Order",
    ],
    "docs/onboarding/local-setup.md": [
        "Bootstrap Workflow",
        "Run The Applications",
        "Validate The Starter",
    ],
    "docs/onboarding/template-finalization-checklist.md": [
        "Before You Rename Anything",
        "Configuration Review",
        "Production Readiness Review",
    ],
    "docs/infrastructure/production-hardening-checklist.md": [
        "Secrets",
        "Network and Proxy Trust",
        "Providers and Callbacks",
    ],
}


def is_empty(path: Path) -> bool:
    return not path.exists() or not path.read_text(encoding="utf-8").strip()


def main() -> int:
    errors: list[str] = []

    readme = DOCS_ROOT / "README.md"
    if is_empty(readme):
        errors.append("Missing or empty docs/README.md")
    else:
        readme_text = readme.read_text(encoding="utf-8")
        for heading in REQUIRED_README_HEADINGS:
            if f"## {heading}" not in readme_text:
                errors.append(f"docs/README.md missing heading: {heading}")

    for directory, filenames in REQUIRED_FILES.items():
        dir_path = DOCS_ROOT / directory
        if not dir_path.exists():
            errors.append(f"Missing directory: docs/{directory}")
            continue
        for filename in filenames:
            path = dir_path / filename
            if is_empty(path):
                errors.append(f"Missing or empty file: docs/{directory}/{filename}")
            if "diagram" in filename or filename.startswith("c4-"):
                if path.exists() and "```mermaid" not in path.read_text(encoding="utf-8"):
                    errors.append(f"Diagram file missing Mermaid content: docs/{directory}/{filename}")

    for relative_path, headings in REQUIRED_DOC_HEADINGS.items():
        path = REPO_ROOT / relative_path
        if not path.exists():
            errors.append(f"Missing file required for heading validation: {relative_path}")
            continue
        text = path.read_text(encoding="utf-8")
        for heading in headings:
            if f"## {heading}" not in text:
                errors.append(f"{relative_path} missing heading: {heading}")

    if errors:
        print("Documentation validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Documentation validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
