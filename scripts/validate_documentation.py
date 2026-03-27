#!/usr/bin/env python3
"""Validate restaurant system documentation completeness and minimum quality."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = REPO_ROOT / "docs" / "system-design"

REQUIRED_README_HEADINGS = [
    "Documentation Structure",
    "Key Features",
    "Getting Started",
    "Documentation Status",
]

REQUIRED_FILES = {
    "requirements": ["requirements-document.md", "user-stories.md"],
    "analysis": [
        "use-case-diagram.md",
        "use-case-descriptions.md",
        "system-context-diagram.md",
        "activity-diagram.md",
        "bpmn-swimlane-diagram.md",
        "data-dictionary.md",
        "business-rules.md",
        "event-catalog.md",
    ],
    "high-level-design": [
        "system-sequence-diagram.md",
        "domain-model.md",
        "data-flow-diagram.md",
        "architecture-diagram.md",
        "c4-context-container.md",
    ],
    "detailed-design": [
        "class-diagram.md",
        "sequence-diagram.md",
        "state-machine-diagram.md",
        "erd-database-schema.md",
        "component-diagram.md",
        "api-design.md",
        "c4-component.md",
    ],
    "infrastructure": [
        "deployment-diagram.md",
        "network-infrastructure.md",
        "cloud-architecture.md",
        "docker-vps-release-runbook.md",
        "backup-restore-operations.md",
    ],
    "edge-cases": [
        "README.md",
        "table-service-and-ordering.md",
        "kitchen-and-preparation.md",
        "inventory-and-procurement.md",
        "billing-and-accounting.md",
        "delivery-and-channel-integration.md",
        "api-and-ui.md",
        "security-and-compliance.md",
        "operations.md",
    ],
    "implementation": [
        "code-guidelines.md",
        "c4-code-diagram.md",
        "implementation-playbook.md",
        "restaurant-implementation-summary.md",
        "restaurant-delivery-phases.md",
        "missing-implementation-checklist.md",
    ],
}


def is_empty(path: Path) -> bool:
    return not path.exists() or not path.read_text(encoding="utf-8").strip()


def main() -> int:
    errors: list[str] = []

    readme = DOCS_ROOT / "README.md"
    if is_empty(readme):
        errors.append("Missing or empty docs/system-design/README.md")
    else:
        readme_text = readme.read_text(encoding="utf-8")
        for heading in REQUIRED_README_HEADINGS:
            if f"## {heading}" not in readme_text:
                errors.append(f"docs/system-design/README.md missing heading: {heading}")

    for directory, filenames in REQUIRED_FILES.items():
        dir_path = DOCS_ROOT / directory
        if not dir_path.exists():
            errors.append(f"Missing directory: docs/system-design/{directory}")
            continue

        for filename in filenames:
            path = dir_path / filename
            if is_empty(path):
                errors.append(f"Missing or empty file: docs/system-design/{directory}/{filename}")

            if ("diagram" in filename or filename.startswith("c4-")) and path.exists():
                if "```mermaid" not in path.read_text(encoding="utf-8"):
                    errors.append(f"Diagram file missing Mermaid content: docs/system-design/{directory}/{filename}")

    if errors:
        print("Documentation validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Documentation validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
