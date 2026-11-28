#!/usr/bin/env python3
"""Required pull-request check for maintainer-owned project cards.

The workflow checks out the base SHA and runs this file from that tree.
Changed paths come from the compare API. File bytes come from the GitHub
contents or blob API and are parsed as data. This script does not check out
the pull-request head and does not execute anything from it.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cardslib


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
        print("ERROR: missing environment: " + ", ".join(missing) + ". Refusing to pass.")
        return 1

    token = os.environ["GITHUB_TOKEN"]
    repository = os.environ["GITHUB_REPOSITORY"]
    author = os.environ["PR_AUTHOR"]
    base_sha = os.environ["PR_BASE_SHA"]
    head_sha = os.environ["PR_HEAD_SHA"]
    head_repo = os.environ["PR_HEAD_REPO"]
    head_ref = os.environ["PR_HEAD_REF"]
    root = Path(os.environ.get("CARD_ROOT", "."))

    try:
        files = cardslib.list_changed_files(
            repository, base_sha, head_repo, head_ref, head_sha, token
        )
    except (RuntimeError, ConnectionError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1

    classification = cardslib.classify_files(files)
    if classification.kind == "unrelated":
        print(
            "cards-check passed: pull request does not change repos/cards/ or repos/delisted.json."
        )
        return 0
    if classification.kind == "reject":
        for error in classification.errors:
            print(f"ERROR: {error}")
        return 1

    is_admin = False
    if classification.kind == "admin":
        is_admin = cardslib.is_hub_admin(
            author,
            repository,
            token,
            association=os.environ.get("PR_AUTHOR_ASSOCIATION", ""),
        )

    blobs = {}
    if classification.kind == "card" or (classification.kind == "admin" and is_admin):
        needed = [classification.card] if classification.kind == "card" else classification.admin_files
        for entry in needed:
            try:
                blobs[entry["filename"]] = cardslib.fetch_pr_file_bytes(
                    entry, token, head_repo, head_sha
                )
            except (RuntimeError, ConnectionError, KeyError, ValueError) as exc:
                print(f"ERROR: {exc}")
                return 1

    try:
        catalog = cardslib.load_catalog(root / "repos" / "catalog.json")
        delisted = cardslib.load_delisted(root / "repos" / "delisted.json")
        base_schema = (root / "repos" / "cards" / "card.schema.json").read_bytes()
        template_path = root / "repos" / "cards" / "_template.md"
        base_template = template_path.read_bytes() if template_path.is_file() else None
    except (OSError, ValueError) as exc:
        print(f"ERROR: could not read base card files: {exc}")
        return 1

    validator, schema_errors = cardslib.validator_from_bytes(base_schema)
    if validator is None:
        for error in schema_errors:
            print(f"ERROR: base schema: {error}")
        return 1

    def lookup(owner: str, repo: str):
        return cardslib.fetch_neox_maintainers(owner, repo, token=token)

    lines = cardslib.evaluate_pull_request(
        files,
        blobs,
        author=author,
        is_admin=is_admin,
        catalog=catalog,
        delisted=delisted,
        validator=validator,
        maintainer_lookup=lookup,
        base_template=base_template,
        base_schema=base_schema,
    )
    for line in lines:
        print(line)
    return 1 if any(line.startswith("ERROR:") for line in lines) else 0


if __name__ == "__main__":
    sys.exit(main())
