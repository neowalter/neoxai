#!/usr/bin/env python3
"""Allow a PR to change repos/cards/<owner>/<repo>.md only if the PR author
owns that GitHub repository or is listed in its .neox-ai.yml editors list.

This is the hub-side check described at https://neox-ai.com/repos/maintainers/.
The website does not run that check. Admins delist cards; they do not edit
someone else's author file through this workflow.
"""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import quote

CARD_PATH = re.compile(
    r"^repos/cards/([a-z0-9][a-z0-9-]{0,38})/([a-z0-9][a-z0-9._-]{0,99})\.md$"
)
SKIP_PATHS = {
    "repos/cards/README.md",
    "repos/cards/_template.md",
}
API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"


def fail(message: str) -> None:
    print(f"::error::{message}")
    raise SystemExit(message)


def github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "neowalter-neoxai-author-card-check",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def http_json(url: str) -> Any:
    req = urllib.request.Request(url, headers=github_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        fail(f"GitHub API {exc.code} for {url}: {body[:300]}")


def http_text(url: str) -> str | None:
    req = urllib.request.Request(url, headers=github_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        body = exc.read().decode("utf-8", errors="replace")
        fail(f"HTTP {exc.code} for {url}: {body[:300]}")


def changed_files(base: str, head: str) -> list[str]:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", "--diff-filter=ACMRD", f"{base}...{head}"],
        text=True,
    )
    return [line.strip() for line in out.splitlines() if line.strip()]


def unquote_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def frontmatter_repo(path: str) -> str | None:
    """Read only the repo: field. Full schema checks belong to the website."""
    try:
        text = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    for raw in text[3:end].splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line.lower().startswith("repo:"):
            continue
        value = unquote_scalar(line.split(":", 1)[1])
        return value or None
    return None


def editors_from_yml(text: str) -> list[str]:
    """Read editors: from a tiny .neox-ai.yml. The file is only a login list."""
    try:
        import yaml

        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict):
            fail(".neox-ai.yml must be a mapping with an editors list")
        editors = data.get("editors", []) or []
        if not isinstance(editors, list):
            fail(".neox-ai.yml editors must be a list of GitHub logins")
        out: list[str] = []
        for item in editors:
            if not isinstance(item, str) or not item.strip():
                fail(".neox-ai.yml editors must be GitHub login strings")
            out.append(item.strip())
        return out
    except ImportError:
        return editors_from_yml_stdlib(text)


def editors_from_yml_stdlib(text: str) -> list[str]:
    in_editors = False
    out: list[str] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not in_editors:
            if re.match(r"^editors:\s*\[\s*\]\s*$", line):
                return []
            inline = re.match(r"^editors:\s*\[(.*)\]\s*$", line)
            if inline:
                items = [unquote_scalar(part) for part in inline.group(1).split(",")]
                if any(not item for item in items):
                    fail(".neox-ai.yml editors must be GitHub login strings")
                return items
            if re.match(r"^editors:\s*$", line):
                in_editors = True
                continue
            if line.startswith("editors:"):
                fail(".neox-ai.yml editors must be a list of GitHub logins")
            continue
        item = re.match(r"^\s+-\s+(.+)$", line)
        if not item:
            break
        login = unquote_scalar(item.group(1))
        if not login:
            fail(".neox-ai.yml editors must be GitHub login strings")
        out.append(login)
    return out


def repo_info(owner: str, repo: str) -> dict[str, Any]:
    return http_json(f"{API}/repos/{owner}/{repo}")


def load_editors(owner: str, repo: str, default_branch: str) -> list[str]:
    api_url = f"{API}/repos/{owner}/{repo}/contents/.neox-ai.yml?ref={quote(default_branch, safe='')}"
    req = urllib.request.Request(api_url, headers=github_headers())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        if payload.get("encoding") == "base64" and payload.get("content"):
            text = base64.b64decode(payload["content"]).decode("utf-8")
            return editors_from_yml(text)
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            body = exc.read().decode("utf-8", errors="replace")
            fail(
                f"GitHub API {exc.code} reading .neox-ai.yml from {owner}/{repo}: {body[:300]}"
            )
    raw = http_text(f"{RAW}/{owner}/{repo}/{default_branch}/.neox-ai.yml")
    if raw is None:
        return []
    return editors_from_yml(raw)


def allowed(actor: str, owner: str, repo: str) -> tuple[bool, str]:
    info = repo_info(owner, repo)
    api_owner = str(info.get("owner", {}).get("login", ""))
    api_name = str(info.get("name", ""))
    if api_owner.lower() != owner.lower() or api_name.lower() != repo.lower():
        return (
            False,
            f"{owner}/{repo} on GitHub is {api_owner}/{api_name} — the card path must use that lowercase owner/name",
        )
    if api_owner.lower() == actor.lower():
        return True, f"{actor} owns {api_owner}/{api_name}"
    branch = str(info.get("default_branch") or "main")
    editors = load_editors(owner, repo, branch)
    if any(login.lower() == actor.lower() for login in editors):
        return True, f"{actor} is listed in {owner}/{repo} .neox-ai.yml editors"
    return (
        False,
        f"{actor} does not own {owner}/{repo} and is not listed in that repository's .neox-ai.yml editors list",
    )


def check_file(path: str, actor: str) -> None:
    if path in SKIP_PATHS:
        print(f"skip hub file {path}")
        return
    lowered = path.lower()
    if lowered.startswith("repos/cards/") and lowered.endswith(".md") and path not in SKIP_PATHS:
        if path != lowered:
            fail(f"{path}: card paths must be lowercase (repos/cards/owner/repo.md)")
        match = CARD_PATH.fullmatch(path)
        if not match:
            fail(
                f"{path}: author cards must be repos/cards/<owner>/<repo>.md "
                "(lowercase GitHub owner and repo name)"
            )
        owner, repo = match.group(1), match.group(2)
        declared = frontmatter_repo(path)
        if declared:
            if declared.strip().count("/") != 1:
                fail(f"{path}: front matter repo must be owner/repo")
            decl_owner, decl_repo = declared.strip().split("/", 1)
            if decl_owner.lower() != owner or decl_repo.lower() != repo:
                fail(
                    f"{path}: front matter repo: {declared!r} must match the path {owner}/{repo}"
                )
        ok, reason = allowed(actor, owner, repo)
        if not ok:
            fail(f"{path}: {reason}")
        print(f"ok {path}: {reason}")
        return
    if path.startswith("repos/cards/"):
        fail(f"{path}: only author cards, README.md, and _template.md belong under repos/cards/")


def main() -> None:
    actor = os.environ.get("PR_AUTHOR", "").strip()
    base = os.environ.get("BASE_SHA", "").strip()
    head = os.environ.get("HEAD_SHA", "").strip()
    if not actor or not base or not head:
        fail("PR_AUTHOR, BASE_SHA, and HEAD_SHA must be set")
    files = changed_files(base, head)
    card_files = [path for path in files if path.startswith("repos/cards/")]
    if not card_files:
        print("no repos/cards changes")
        return
    print(f"PR author: {actor}")
    for path in card_files:
        check_file(path, actor)
    print("author-card ownership: ok")


if __name__ == "__main__":
    main()
