#!/usr/bin/env python3
"""Compile maintainer card files into repos/cards.json.

This is the trusted post-merge step. It reads the checkout it is given
(main, or the branch selected for workflow_dispatch). It does not read a
pull-request head.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cardslib


def git_meta(root: Path, rel: str):
    try:
        output = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI%x00%H", "--", rel],
            cwd=str(root),
            text=True,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"git log failed for {rel}: {exc.output}") from exc
    text = output.strip("\n")
    if "\0" not in text:
        raise RuntimeError(f"no git commit for {rel}")
    updated_at, sha = text.split("\0", 1)
    updated_at = updated_at.strip()
    sha = sha.strip()
    if not updated_at or not sha:
        raise RuntimeError(f"no git commit for {rel}")
    return updated_at, sha


def compile_cards(root: Path) -> int:
    root = root.resolve()
    cards_dir = root / "repos" / "cards"
    schema_path = cards_dir / "card.schema.json"
    catalog_path = root / "repos" / "catalog.json"
    out_path = root / "repos" / "cards.json"
    discovered = []
    errors = []
    if cards_dir.is_dir():
        for path in sorted(cards_dir.glob("*/*")):
            if not path.is_file() or path.name == "_template.md":
                continue
            rel = path.relative_to(root).as_posix()
            if path.suffix != ".md" or cardslib.CARD_PATH_RE.fullmatch(rel) is None:
                errors.append(f"{rel} is not a lowercase repos/cards/<owner>/<repo>.md path")
                continue
            discovered.append((path, rel))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print("cards-compile failed. repos/cards.json was not updated.")
        return 1

    validator = None
    catalog = {}
    if discovered:
        if not schema_path.is_file():
            print(f"ERROR: {cardslib.SCHEMA_PATH} is missing.")
            return 1
        validator, schema_errors = cardslib.validator_from_bytes(schema_path.read_bytes())
        if validator is None:
            for error in schema_errors:
                print(f"ERROR: {error}")
            return 1
        try:
            catalog = cardslib.load_catalog(catalog_path)
        except (OSError, ValueError) as exc:
            print(f"ERROR: could not read repos/catalog.json: {exc}")
            return 1

    cards = []
    warnings = []
    for path, rel in discovered:
        match = cardslib.CARD_PATH_RE.fullmatch(rel)
        owner, repo = match.groups()
        front, body, content_errors, content_warnings = cardslib.validate_card_content(
            path.read_bytes(),
            validator,
            owner=owner,
            repo=repo,
            author=None,
            require_author=False,
        )
        for warning in content_warnings:
            warnings.append(f"{rel}: {warning}")
        if content_errors or front is None:
            for error in content_errors:
                errors.append(f"{rel}: {error}")
            continue
        entry = catalog.get(f"{owner}/{repo}".casefold())
        if entry is None:
            warnings.append(
                f"{rel} is not in repos/catalog.json. The compiled repo field uses the front matter."
            )
            repo_field = front.get("repo") if isinstance(front.get("repo"), str) else f"{owner}/{repo}"
        else:
            repo_field = entry["slug"]
        try:
            updated_at, sha = git_meta(root, rel)
        except RuntimeError as exc:
            errors.append(str(exc))
            continue
        cards.append(
            {
                "repo": repo_field,
                "path": rel,
                "frontmatter": front,
                "body": body,
                "lastEditor": None,
                "updatedAt": updated_at,
                "commit": sha,
            }
        )

    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print("cards-compile failed. repos/cards.json was not updated.")
        return 1

    cards.sort(key=lambda item: item["path"])
    if out_path.is_file():
        try:
            current = json.loads(out_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            current = None
        if isinstance(current, dict) and current.get("schemaVersion") == 1 and current.get("cards") == cards:
            print(f"repos/cards.json card set is unchanged ({len(cards)} cards).")
            return 0

    document = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cards": cards,
    }
    payload = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(payload.encode("utf-8"))
    noun = "card" if len(cards) == 1 else "cards"
    print(f"Wrote repos/cards.json ({len(cards)} {noun}).")
    return 0


def main() -> int:
    return compile_cards(Path("."))


if __name__ == "__main__":
    sys.exit(main())
