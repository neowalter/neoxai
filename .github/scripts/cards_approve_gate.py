#!/usr/bin/env python3
"""Gate auto-approve for project-card pull requests.

A pull request that changes repos/cards/ is approved only when its author is
the catalog owner of each card file. The catalog is read from the base
checkout. Approval never replaces the cards-check status check.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cardslib


def set_output(name: str, value: str) -> None:
    print(f"{name}={value}")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def main() -> int:
    required = (
        "GITHUB_TOKEN",
        "GITHUB_REPOSITORY",
        "PR_AUTHOR",
        "PR_BASE_SHA",
        "PR_HEAD_SHA",
        "PR_HEAD_REPO",
        "PR_HEAD_REF",
    )
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        print("ERROR: missing pull request context: " + ", ".join(missing))
        set_output("approve", "false")
        return 1
    try:
        files = cardslib.list_changed_files(
            os.environ["GITHUB_REPOSITORY"],
            os.environ["PR_BASE_SHA"],
            os.environ["PR_HEAD_REPO"],
            os.environ["PR_HEAD_REF"],
            os.environ["PR_HEAD_SHA"],
            os.environ["GITHUB_TOKEN"],
        )
        catalog = cardslib.load_catalog(Path("repos/catalog.json"))
    except (RuntimeError, ConnectionError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}. Skipping auto-approve.")
        set_output("approve", "false")
        return 1
    paths = [entry.get("filename", "") for entry in files]
    allowed, reason = cardslib.auto_approve_allowed(paths, os.environ["PR_AUTHOR"], catalog)
    print(reason)
    set_output("approve", "true" if allowed else "false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
