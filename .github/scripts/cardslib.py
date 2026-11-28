"""Shared project-card checks.

Pull-request bytes are data. Callers must not execute them, import them, or
check out the pull-request head to run them. YAML is loaded with a safe loader
that rejects anchors and aliases.
"""

from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

MAX_CARD_BYTES = 20 * 1024
MAX_SCHEMA_BYTES = 256 * 1024
MAX_PROOF_BYTES = 16 * 1024

SCHEMA_PATH = "repos/cards/card.schema.json"
TEMPLATE_PATH = "repos/cards/_template.md"
README_PATH = "repos/cards/README.md"
DELISTED_PATH = "repos/delisted.json"

ADMIN_PATHS = frozenset(
    {README_PATH, TEMPLATE_PATH, SCHEMA_PATH, DELISTED_PATH}
)

LOGO_HOSTS = frozenset(
    {
        "github.com",
        "raw.githubusercontent.com",
        "camo.githubusercontent.com",
        "avatars.githubusercontent.com",
        "user-images.githubusercontent.com",
    }
)

SLUG_PATTERN = (
    r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}"
    r"/[A-Za-z0-9][A-Za-z0-9._-]{0,99}$"
)
CARD_PATH_RE = re.compile(
    r"^repos/cards/([a-z0-9](?:[a-z0-9]|-(?=[a-z0-9])){0,38})"
    r"/([a-z0-9][a-z0-9._-]{0,99})\.md$"
)
LOOSE_CARD_RE = re.compile(r"^repos/cards/([^/]+)/([^/]+)\.md$", re.IGNORECASE)

BLOCKED_CLAIMS = (
    ("diagnoses", re.compile(r"\bdiagnoses\b", re.IGNORECASE)),
    ("diagnosis", re.compile(r"\bdiagnosis\b", re.IGNORECASE)),
    ("diagnose", re.compile(r"\bdiagnose\b", re.IGNORECASE)),
    ("treats", re.compile(r"\btreats\b", re.IGNORECASE)),
    ("treat", re.compile(r"\btreat\b", re.IGNORECASE)),
    ("cures", re.compile(r"\bcures\b", re.IGNORECASE)),
    ("cure", re.compile(r"\bcure\b", re.IGNORECASE)),
    ("clinically proven", re.compile(r"\bclinically\s+proven\b", re.IGNORECASE)),
    ("medical-grade", re.compile(r"\bmedical-grade\b", re.IGNORECASE)),
    ("FDA-cleared", re.compile(r"\bFDA-cleared\b", re.IGNORECASE)),
    ("FDA-approved", re.compile(r"\bFDA-approved\b", re.IGNORECASE)),
)

WARNED_CLAIMS = (
    ("first", re.compile(r"\bfirst\b", re.IGNORECASE)),
    ("best", re.compile(r"\bbest\b", re.IGNORECASE)),
    ("only", re.compile(r"\bonly\b", re.IGNORECASE)),
    ("#1", re.compile(r"(?<![A-Za-z0-9])#1(?!\d)")),
    ("unleash", re.compile(r"\bunleash\b", re.IGNORECASE)),
    ("empower", re.compile(r"\bempower\b", re.IGNORECASE)),
    ("revolutionize", re.compile(r"\brevolutionize\b", re.IGNORECASE)),
    ("game-changing", re.compile(r"\bgame-changing\b", re.IGNORECASE)),
    ("seamless", re.compile(r"\bseamless\b", re.IGNORECASE)),
    ("delve", re.compile(r"\bdelve\b", re.IGNORECASE)),
    ("cutting-edge", re.compile(r"\bcutting-edge\b", re.IGNORECASE)),
    ("state-of-the-art", re.compile(r"\bstate-of-the-art\b", re.IGNORECASE)),
    ("fostering", re.compile(r"\bfostering\b", re.IGNORECASE)),
)

HEADING_OVERVIEW = re.compile(r"^##\s+Overview\s*$", re.MULTILINE)
HEADING_QUICK_START = re.compile(r"^##\s+Quick start\s*$", re.MULTILINE)

USER_AGENT = "neoxai-cards-check"
GITHUB_API_VERSION = "2022-11-28"


class CardLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects anchors and aliases."""

    def compose_node(self, parent, index):  # type: ignore[no-untyped-def]
        if self.check_event(yaml.events.AliasEvent):
            raise ValueError("YAML aliases are not allowed in card front matter")
        event = self.peek_event()
        if getattr(event, "anchor", None):
            raise ValueError("YAML anchors are not allowed in card front matter")
        return super().compose_node(parent, index)


def _drop_timestamp_resolver(loader: type) -> None:
    resolvers = loader.yaml_implicit_resolvers
    for first, table in list(resolvers.items()):
        resolvers[first] = [
            (tag, regexp)
            for tag, regexp in table
            if tag != "tag:yaml.org,2002:timestamp"
        ]


_drop_timestamp_resolver(CardLoader)


def in_scope(path: str) -> bool:
    return path == DELISTED_PATH or path.startswith("repos/cards/")


def load_catalog(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    index = {}
    for item in data.get("items", []):
        ident = item.get("id")
        if not isinstance(ident, str):
            continue
        prefix, separator, slug = ident.partition(":")
        if prefix.casefold() != "github" or not separator or "/" not in slug:
            continue
        owner, repo = slug.split("/", 1)
        index[slug.casefold()] = {
            "id": ident,
            "owner": owner,
            "repo": repo,
            "slug": slug,
        }
    return index


def load_delisted(path: Path) -> set:
    if not path.is_file():
        raise FileNotFoundError(f"{DELISTED_PATH} is missing")
    data = json.loads(path.read_text(encoding="utf-8"))
    found = set()
    repos = data.get("repos", []) if isinstance(data, dict) else []
    for entry in repos:
        if isinstance(entry, dict) and isinstance(entry.get("repo"), str):
            found.add(entry["repo"].casefold())
    return found


def build_format_checker() -> FormatChecker:
    checker = FormatChecker()

    def check_uri(instance: object) -> bool:
        if not isinstance(instance, str):
            return True
        parsed = urllib.parse.urlparse(instance)
        return parsed.scheme in {"http", "https"} and bool(parsed.hostname)

    checker.checkers["uri"] = (check_uri, ())
    return checker


FORMAT_CHECKER = build_format_checker()


def assert_closed_objects(node: object, path: str = "$") -> None:
    if isinstance(node, dict):
        is_object = node.get("type") == "object" or "properties" in node
        if is_object and node.get("additionalProperties") is not False:
            raise ValueError(f"{path} must set additionalProperties to false")
        for key, value in node.items():
            if key in {"properties", "$defs", "patternProperties"} and isinstance(value, dict):
                for name, child in value.items():
                    assert_closed_objects(child, f"{path}/{key}/{name}")
            elif key in {"items", "contains", "not", "if", "then", "else"} and isinstance(value, dict):
                assert_closed_objects(value, f"{path}/{key}")
            elif key in {"allOf", "anyOf", "oneOf", "prefixItems"} and isinstance(value, list):
                for index, child in enumerate(value):
                    assert_closed_objects(child, f"{path}/{key}/{index}")
    elif isinstance(node, list):
        for index, child in enumerate(node):
            assert_closed_objects(child, f"{path}/{index}")


def validate_schema_document(raw: bytes) -> list:
    if len(raw) > MAX_SCHEMA_BYTES:
        return [f"{SCHEMA_PATH} exceeds {MAX_SCHEMA_BYTES} bytes"]
    try:
        schema = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"{SCHEMA_PATH} is not UTF-8 JSON: {exc}"]
    errors = []
    schema_id = schema.get("$schema", "") if isinstance(schema, dict) else ""
    if "2020-12" not in str(schema_id):
        errors.append(f"{SCHEMA_PATH} must declare JSON Schema draft 2020-12")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        errors.append(f"{SCHEMA_PATH} is not a valid draft 2020-12 schema: {exc.message}")
    try:
        assert_closed_objects(schema)
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def validator_from_bytes(raw: bytes):
    errors = validate_schema_document(raw)
    if errors:
        return None, errors
    schema = json.loads(raw.decode("utf-8"))
    return Draft202012Validator(schema, format_checker=FORMAT_CHECKER), []


DELISTED_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["repos"],
    "properties": {
        "repos": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["repo", "reason", "date"],
                "properties": {
                    "repo": {"type": "string", "pattern": SLUG_PATTERN},
                    "reason": {"type": "string", "minLength": 1},
                    "date": {"type": "string", "minLength": 1},
                },
            },
        }
    },
}
DELISTED_VALIDATOR = Draft202012Validator(DELISTED_SCHEMA)


def validate_delisted_bytes(raw: bytes) -> list:
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"{DELISTED_PATH} is not UTF-8 JSON: {exc}"]
    return [
        f"{DELISTED_PATH} {'.'.join(str(part) for part in err.absolute_path) or 'root'}: {err.message}"
        for err in DELISTED_VALIDATOR.iter_errors(data)
    ]


def split_front_matter(text: str):
    if not text.startswith("---"):
        raise ValueError("card is missing YAML front matter")
    lines = text.splitlines(keepends=True)
    if lines[0].strip() != "---":
        raise ValueError("card front matter must open with ---")
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        raise ValueError("card front matter is not closed with ---")
    raw = "".join(lines[1:end])
    body = "".join(lines[end + 1 :])
    if body.startswith("\n"):
        body = body[1:]
    elif body.startswith("\r\n"):
        body = body[2:]
    try:
        data = yaml.load(raw, Loader=CardLoader)
    except (yaml.YAMLError, ValueError) as exc:
        raise ValueError(f"front matter YAML is not valid: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("card front matter must be a YAML mapping")
    return data, body


def assert_plain_json(value: object, path: str = "front matter") -> None:
    if value is None or isinstance(value, (str, float, bool)):
        return
    if isinstance(value, int) and not isinstance(value, bool):
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            assert_plain_json(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} has a non-string key")
            assert_plain_json(item, f"{path}.{key}")
        return
    raise ValueError(
        f"{path} must be plain YAML data, not {type(value).__name__}. Quote dates and versions."
    )


def schema_messages(validator, instance: dict) -> list:
    messages = []
    for err in validator.iter_errors(instance):
        loc = ".".join(str(part) for part in err.absolute_path) or "root"
        messages.append(f"front matter {loc}: {err.message}")
    return messages


def heading_errors(body: str) -> list:
    errors = []
    if HEADING_OVERVIEW.search(body) is None:
        errors.append("card body must contain a heading line '## Overview'")
    if HEADING_QUICK_START.search(body) is None:
        errors.append("card body must contain a heading line '## Quick start'")
    return errors


def _lint_piece(label: str, text: str):
    errors = []
    warnings = []
    for name, pattern in BLOCKED_CLAIMS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            errors.append(f'blocked claim "{name}" in {label} (line {line})')
    for name, pattern in WARNED_CLAIMS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            warnings.append(
                f'marketing word "{name}" in {label} (line {line}). '
                "This warning does not fail the check."
            )
    return errors, warnings


def claim_findings(front: dict, body: str):
    errors = []
    warnings = []
    summary = front.get("summary")
    if isinstance(summary, dict) and isinstance(summary.get("en"), str):
        found, warned = _lint_piece("summary.en", summary["en"])
        errors.extend(found)
        warnings.extend(warned)
    if isinstance(body, str):
        found, warned = _lint_piece("body", body)
        errors.extend(found)
        warnings.extend(warned)
    return errors, warnings


def logo_errors(front: dict) -> list:
    logo = front.get("logo") if isinstance(front, dict) else None
    if not isinstance(logo, str):
        return []
    parsed = urllib.parse.urlparse(logo)
    host = (parsed.hostname or "").casefold()
    if parsed.username or parsed.password:
        return ["logo URL must not include credentials"]
    if parsed.scheme in {"http", "https"} and host and host not in LOGO_HOSTS:
        return [
            "logo host "
            f"{host} is not allowlisted. Use github.com, raw.githubusercontent.com, "
            "camo.githubusercontent.com, avatars.githubusercontent.com, or "
            "user-images.githubusercontent.com."
        ]
    return []


def author_in_maintainers(front: dict, author: str) -> bool:
    maintainers = front.get("maintainers") if isinstance(front, dict) else None
    if not isinstance(maintainers, list):
        return False
    for item in maintainers:
        if isinstance(item, dict) and isinstance(item.get("github"), str):
            if item["github"].casefold() == author.casefold():
                return True
    return False


def validate_card_content(raw: bytes, validator, *, owner: str, repo: str, author: str | None, require_author: bool):
    """Return front matter, body, errors, warnings. Does not execute the file."""
    errors = []
    warnings = []
    if len(raw) > MAX_CARD_BYTES:
        return None, "", [f"card file is {len(raw)} bytes; the limit is {MAX_CARD_BYTES} bytes (20 KB)"], []
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None, "", ["card file must be UTF-8"], []
    try:
        front, body = split_front_matter(text)
    except ValueError as exc:
        return None, "", [str(exc)], []
    try:
        assert_plain_json(front)
    except ValueError as exc:
        errors.append(str(exc))
    else:
        if validator is not None:
            errors.extend(schema_messages(validator, front))
    if isinstance(front.get("repo"), str) and front["repo"].casefold() != f"{owner}/{repo}".casefold():
        errors.append(
            f"front matter repo '{front['repo']}' must match the path {owner}/{repo} (case-insensitive)"
        )
    errors.extend(heading_errors(body))
    claim_err, claim_warn = claim_findings(front, body)
    errors.extend(claim_err)
    warnings.extend(claim_warn)
    errors.extend(logo_errors(front))
    if require_author and author and not author_in_maintainers(front, author):
        errors.append(f"pull request author {author} must appear in maintainers[].github")
    return front, body, errors, warnings


def validate_template_bytes(raw: bytes, validator):
    errors = []
    warnings = []
    if len(raw) > MAX_CARD_BYTES:
        return [f"{TEMPLATE_PATH} exceeds {MAX_CARD_BYTES} bytes"], []
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return [f"{TEMPLATE_PATH} must be UTF-8"], []
    try:
        front, body = split_front_matter(text)
    except ValueError as exc:
        return [f"{TEMPLATE_PATH}: {exc}"], []
    try:
        assert_plain_json(front)
    except ValueError as exc:
        errors.append(f"{TEMPLATE_PATH}: {exc}")
    else:
        if validator is not None:
            errors.extend(f"{TEMPLATE_PATH}: {message}" for message in schema_messages(validator, front))
    errors.extend(f"{TEMPLATE_PATH}: {message}" for message in heading_errors(body))
    claim_err, claim_warn = claim_findings(front, body)
    errors.extend(f"{TEMPLATE_PATH}: {message}" for message in claim_err)
    warnings.extend(f"{TEMPLATE_PATH}: {message}" for message in claim_warn)
    errors.extend(f"{TEMPLATE_PATH}: {message}" for message in logo_errors(front))
    return errors, warnings


class Classification:
    def __init__(self, kind, card=None, admin_files=None, errors=None):
        self.kind = kind
        self.card = card
        self.admin_files = admin_files or []
        self.errors = errors or []


def classify_files(files: list) -> Classification:
    if not any(in_scope(entry.get("filename", "")) for entry in files):
        return Classification("unrelated")
    cards = []
    admins = []
    extras = []
    for entry in files:
        name = entry.get("filename", "")
        if name in ADMIN_PATHS:
            admins.append(entry)
        elif CARD_PATH_RE.fullmatch(name):
            cards.append(entry)
        else:
            extras.append(entry)
    if cards or extras:
        names = ", ".join(entry.get("filename", "") for entry in files) or "(none)"
        if extras or admins or len(cards) != 1:
            errors = [
                "A card pull request must change exactly one lowercase file "
                "repos/cards/<owner>/<repo>.md and nothing else. "
                f"This pull request changes: {names}"
            ]
            if any(
                LOOSE_CARD_RE.fullmatch(entry.get("filename", ""))
                and not CARD_PATH_RE.fullmatch(entry.get("filename", ""))
                for entry in files
            ):
                errors.append(
                    "Card paths are lowercase. Example: repos/cards/example-org/eeg-toolkit.md"
                )
            return Classification("reject", errors=errors)
        card = cards[0]
        status = card.get("status")
        if status not in {"added", "modified"} or card.get("previous_filename"):
            return Classification(
                "reject",
                errors=[
                    f"{card.get('filename')} must be added or modified. "
                    "Removing a card is a repo-removal issue, not a file delete. "
                    "Renames count as more than one path."
                ],
            )
        return Classification("card", card=card)
    bad = [
        entry
        for entry in admins
        if entry.get("status") not in {"added", "modified"} or entry.get("previous_filename")
    ]
    if bad:
        names = ", ".join(entry.get("filename", "") for entry in bad)
        return Classification(
            "reject",
            errors=[f"Admin files must be added or edited, not deleted or renamed: {names}"],
        )
    return Classification("admin", admin_files=admins)


def evaluate_pull_request(
    files,
    blobs,
    *,
    author,
    is_admin,
    catalog,
    delisted,
    validator,
    maintainer_lookup,
    base_template=None,
    base_schema=None,
):
    """Return log lines. A line that starts with 'ERROR:' fails the check."""
    lines = []
    classification = classify_files(files)
    if classification.kind == "unrelated":
        lines.append(
            "cards-check passed: pull request does not change repos/cards/ or repos/delisted.json."
        )
        return lines
    if classification.kind == "reject":
        return [f"ERROR: {error}" for error in classification.errors]

    if classification.kind == "admin":
        if not is_admin:
            return [
                "ERROR: Changes to repos/cards/README.md, repos/cards/_template.md, "
                "repos/cards/card.schema.json, or repos/delisted.json are allowed only "
                "when the pull request author is neowalter or has admin permission on "
                "this repository. A repository author changes exactly one file, "
                "repos/cards/<owner>/<repo>.md, and nothing else."
            ]
        schema_raw = blobs.get(SCHEMA_PATH, base_schema)
        template_raw = blobs.get(TEMPLATE_PATH, base_template)
        schema_changed = SCHEMA_PATH in blobs
        template_changed = TEMPLATE_PATH in blobs
        active_validator = validator
        if schema_changed:
            if schema_raw is None:
                lines.append(f"ERROR: {SCHEMA_PATH} bytes were not loaded")
            else:
                parsed, schema_errors = validator_from_bytes(schema_raw)
                for error in schema_errors:
                    lines.append(f"ERROR: {error}")
                if parsed is not None:
                    active_validator = parsed
        if (schema_changed or template_changed) and not any(line.startswith("ERROR:") for line in lines):
            if template_raw is None:
                lines.append(f"ERROR: {TEMPLATE_PATH} is missing, so the schema cannot be checked against it")
            elif active_validator is not None:
                template_errors, template_warnings = validate_template_bytes(template_raw, active_validator)
                lines.extend(f"ERROR: {error}" for error in template_errors)
                lines.extend(f"WARNING: {warning}" for warning in template_warnings)
        if DELISTED_PATH in blobs:
            for error in validate_delisted_bytes(blobs[DELISTED_PATH]):
                lines.append(f"ERROR: {error}")
        if any(line.startswith("ERROR:") for line in lines):
            return lines
        lines.append("cards-check passed: admin files validate.")
        return lines

    card = classification.card
    path = card["filename"]
    owner, repo = CARD_PATH_RE.fullmatch(path).groups()
    slug = f"{owner}/{repo}"
    raw = blobs.get(path)
    if raw is None:
        return [f"ERROR: could not read {path} via the GitHub API. The check fails closed."]

    entry = catalog.get(slug.casefold())
    if entry is None:
        lines.append(f"ERROR: {slug} is not in repos/catalog.json items[].id.")
    elif slug.casefold() in delisted:
        lines.append(f"ERROR: {slug} is listed in repos/delisted.json and cannot be published.")
    elif author.casefold() != entry["owner"].casefold():
        logins, note = maintainer_lookup(entry["owner"], entry["repo"])
        if note:
            lines.append(f"NOTE: {note}")
        listed = {login.casefold() for login in logins}
        if author.casefold() not in listed:
            lines.append(
                f"ERROR: pull request author {author} is not the catalog owner "
                f"({entry['owner']}) and is not listed in .neox-ai.yml at the root of "
                f"https://github.com/{entry['owner']}/{entry['repo']}. "
                "A failed fetch is not a pass."
            )

    front, body, content_errors, content_warnings = validate_card_content(
        raw,
        validator,
        owner=owner,
        repo=repo,
        author=author,
        require_author=True,
    )
    lines.extend(f"ERROR: {error}" for error in content_errors)
    lines.extend(f"WARNING: {warning}" for warning in content_warnings)
    if any(line.startswith("ERROR:") for line in lines):
        return lines
    lines.append(f"cards-check passed: {path}")
    return lines


def auto_approve_allowed(paths, author, catalog):
    """Card-directory edits are approved only for the catalog owner."""
    touched = [path for path in paths if path.startswith("repos/cards/")]
    if not touched:
        return True, "Auto-approve allowed: pull request does not change repos/cards/."
    card_paths = [path for path in touched if CARD_PATH_RE.fullmatch(path)]
    if len(card_paths) != len(touched) or not card_paths:
        return (
            False,
            "Skipping auto-approve: pull request touches repos/cards/ and the author "
            "is not the catalog owner of a card file. Approval never replaces cards-check.",
        )
    for path in card_paths:
        owner, repo = CARD_PATH_RE.fullmatch(path).groups()
        entry = catalog.get(f"{owner}/{repo}".casefold())
        if entry is None or entry["owner"].casefold() != author.casefold():
            shown = entry["owner"] if entry else "not in the catalog"
            return (
                False,
                f"Skipping auto-approve: {author} is not the catalog owner of {owner}/{repo} "
                f"({shown}). Approval never replaces cards-check.",
            )
    return (
        True,
        "Auto-approve allowed: "
        f"{author} is the catalog owner of {', '.join(card_paths)}. "
        "Approval never replaces cards-check.",
    )


class SameHostRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        old_host = urllib.parse.urlparse(req.full_url).hostname
        new_host = urllib.parse.urlparse(newurl).hostname
        if old_host != new_host:
            raise urllib.error.HTTPError(
                req.full_url,
                code,
                f"refusing redirect from {old_host} to {new_host}",
                headers,
                fp,
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def http_get(url, token=None, accept=None, timeout=20):
    headers = {"User-Agent": USER_AGENT}
    host = urllib.parse.urlparse(url).hostname
    if token and host == "api.github.com":
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = GITHUB_API_VERSION
    if accept:
        headers["Accept"] = accept
    request = urllib.request.Request(url, headers=headers, method="GET")
    opener = urllib.request.build_opener(SameHostRedirectHandler)
    try:
        with opener.open(request, timeout=timeout) as response:
            return response.status, response.read(), {key.lower(): value for key, value in response.headers.items()}
    except urllib.error.HTTPError as exc:
        body = exc.read() if exc.fp is not None else b""
        header_map = {key.lower(): value for key, value in exc.headers.items()} if exc.headers else {}
        return exc.code, body, header_map
    except urllib.error.URLError as exc:
        raise ConnectionError(getattr(exc, "reason", exc)) from exc


def next_link(headers: dict):
    link = headers.get("link", "")
    for part in link.split(","):
        if 'rel="next"' in part:
            return part.split(";", 1)[0].strip().strip("<>")
    return None


def list_changed_files(repository, base_sha, head_repo, head_ref, head_sha, token, getter=None):
    """List pull-request files with the compare API (contents: read).

    Same-repo pulls compare commit SHAs. Fork pulls compare
    ``base_sha...fork_owner:head_ref``. A truncated 300-file response fails
    closed. File bytes are not executed.
    """
    getter = getter or http_get
    if not repository or not base_sha or not head_sha or not head_repo or not head_ref:
        raise RuntimeError("pull request base or head is missing; failing closed")
    if head_repo == repository:
        basehead = f"{base_sha}...{head_sha}"
    else:
        if "/" not in head_repo:
            raise RuntimeError("pull request head repository is missing; failing closed")
        fork_owner = head_repo.split("/", 1)[0]
        basehead = f"{base_sha}...{fork_owner}:{head_ref}"
    url = (
        f"https://api.github.com/repos/{repository}/compare/"
        f"{urllib.parse.quote(basehead, safe=':./')}"
    )
    status, body, _headers = getter(url, token=token, accept="application/vnd.github+json")
    if status != 200:
        detail = body.decode("utf-8", "replace")[:300]
        raise RuntimeError(
            f"could not compare {basehead} (HTTP {status}). {detail} The check fails closed."
        )
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"compare response was not JSON: {exc}") from exc
    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(files, list):
        raise RuntimeError("compare response did not include a files array. The check fails closed.")
    if len(files) >= 300:
        raise RuntimeError("compare returned 300 files and may be truncated. The check fails closed.")
    return files


def list_pr_files(repository, number, token, getter=None):
    getter = getter or http_get
    url = f"https://api.github.com/repos/{repository}/pulls/{number}/files?per_page=100"
    files = []
    pages = 0
    while url:
        pages += 1
        if pages > 50:
            raise RuntimeError("pull request file list exceeded 50 pages; failing closed")
        status, body, headers = getter(url, token=token, accept="application/vnd.github+json")
        if status != 200:
            detail = body.decode("utf-8", "replace")[:300]
            raise RuntimeError(f"could not list pull request files (HTTP {status}). {detail}")
        batch = json.loads(body.decode("utf-8"))
        if not isinstance(batch, list):
            raise RuntimeError("pull request file list was not a JSON array")
        files.extend(batch)
        url = next_link(headers)
    return files


def _decode_github_body(body: bytes, headers: dict) -> bytes | None:
    content_type = headers.get("content-type", "")
    if "application/json" in content_type or "github+json" in content_type:
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        if isinstance(payload, dict) and payload.get("encoding") == "base64" and isinstance(payload.get("content"), str):
            return base64.b64decode(payload["content"])
        return None
    return body


def fetch_pr_file_bytes(entry, token, head_repo, head_sha, getter=None):
    """Read one pull-request file through the GitHub API. Never executes it."""
    getter = getter or http_get
    if "/" not in head_repo:
        raise RuntimeError("pull request head repository is missing; failing closed")
    owner, repo = head_repo.split("/", 1)
    path = entry["filename"]
    quoted_path = urllib.parse.quote(path, safe="/")
    quoted_sha = urllib.parse.quote(head_sha, safe="")
    urls = []
    contents_url = entry.get("contents_url")
    if isinstance(contents_url, str) and contents_url.startswith("https://api.github.com/"):
        urls.append(contents_url)
    urls.append(
        f"https://api.github.com/repos/{urllib.parse.quote(owner, safe='')}/"
        f"{urllib.parse.quote(repo, safe='')}/contents/{quoted_path}?ref={quoted_sha}"
    )
    errors = []
    for url in urls:
        status, body, headers = getter(url, token=token, accept="application/vnd.github.raw")
        if status in {401, 403, 404} and token:
            public_status, public_body, public_headers = getter(
                url, token=None, accept="application/vnd.github.raw"
            )
            if public_status == 200:
                status, body, headers = public_status, public_body, public_headers
        if status == 200:
            decoded = _decode_github_body(body, headers)
            if decoded is not None:
                return decoded
            errors.append(f"{url} HTTP 200 but body was not file bytes")
            continue
        errors.append(f"{url} HTTP {status}")
    blob_sha = entry.get("sha")
    if isinstance(blob_sha, str) and blob_sha:
        blob_url = (
            f"https://api.github.com/repos/{urllib.parse.quote(owner, safe='')}/"
            f"{urllib.parse.quote(repo, safe='')}/git/blobs/{urllib.parse.quote(blob_sha, safe='')}"
        )
        status, body, headers = getter(blob_url, token=token, accept="application/vnd.github+json")
        if status in {401, 403, 404} and token:
            public_status, public_body, public_headers = getter(
                blob_url, token=None, accept="application/vnd.github+json"
            )
            if public_status == 200:
                status, body, headers = public_status, public_body, public_headers
        if status == 200:
            decoded = _decode_github_body(body, headers)
            if decoded is not None:
                return decoded
        errors.append(f"blob HTTP {status}")
    joined = "; ".join(errors) or "no response"
    raise RuntimeError(f"could not read {path} via the GitHub API ({joined}). The check fails closed.")


def parse_maintainer_yaml(raw: bytes):
    if len(raw) > MAX_PROOF_BYTES:
        return None
    try:
        data = yaml.load(raw.decode("utf-8-sig"), Loader=CardLoader)
    except (UnicodeDecodeError, yaml.YAMLError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    maintainers = data.get("maintainers")
    if not isinstance(maintainers, list):
        return None
    logins = []
    for item in maintainers:
        if not isinstance(item, str) or not item.strip() or item.strip() != item:
            return None
        logins.append(item)
    return logins


def fetch_neox_maintainers(owner, repo, token=None, getter=None):
    """Return (logins, note). A failed fetch yields an empty list and is not a pass."""
    getter = getter or http_get
    attempts = []
    js_url = (
        "https://cdn.jsdelivr.net/gh/"
        f"{urllib.parse.quote(owner, safe='')}/{urllib.parse.quote(repo, safe='')}@HEAD/.neox-ai.yml"
    )
    gh_url = (
        "https://api.github.com/repos/"
        f"{urllib.parse.quote(owner, safe='')}/{urllib.parse.quote(repo, safe='')}/contents/.neox-ai.yml"
    )
    for label, url, accept, use_token in (
        ("jsDelivr", js_url, None, False),
        ("GitHub contents API", gh_url, "application/vnd.github.raw", True),
    ):
        request_token = token if use_token else None
        try:
            status, body, headers = getter(url, token=request_token, accept=accept, timeout=15)
        except TypeError:
            try:
                status, body, headers = getter(url, token=request_token, accept=accept)
            except ConnectionError as exc:
                attempts.append(f"{label} error {exc}")
                continue
        except ConnectionError as exc:
            attempts.append(f"{label} error {exc}")
            continue
        if status in {401, 403} and request_token:
            try:
                public_status, public_body, public_headers = getter(url, token=None, accept=accept, timeout=15)
            except TypeError:
                public_status, public_body, public_headers = getter(url, token=None, accept=accept)
            except ConnectionError as exc:
                attempts.append(f"{label} HTTP {status}; unauthenticated error {exc}")
                continue
            if public_status == 200:
                status, body, headers = public_status, public_body, public_headers
        attempts.append(f"{label} HTTP {status}")
        if status != 200:
            continue
        content_type = headers.get("content-type", "")
        payload = body
        if "application/json" in content_type or "github+json" in content_type:
            decoded = _decode_github_body(body, headers)
            if decoded is None:
                continue
            payload = decoded
        if payload.lstrip().lower().startswith(b"<!doctype") or payload.lstrip().lower().startswith(b"<html"):
            continue
        parsed = parse_maintainer_yaml(payload)
        if parsed is None:
            attempts.append(f"{label} body was not {{ maintainers: [logins] }}")
            continue
        return parsed, ""
    note = (
        f"No usable .neox-ai.yml for https://github.com/{owner}/{repo} "
        f"({'; '.join(attempts)}). A failed fetch is not a pass."
    )
    return [], note


def is_hub_admin(author, repository, token, association="", getter=None):
    if author.casefold() == "neowalter" or association == "OWNER":
        return True
    getter = getter or http_get
    quoted = urllib.parse.quote(author, safe="")
    url = f"https://api.github.com/repos/{repository}/collaborators/{quoted}/permission"
    try:
        status, body, _headers = getter(url, token=token, accept="application/vnd.github+json")
    except ConnectionError as exc:
        print(f"NOTE: admin permission lookup for {author} failed ({exc}). Not an admin.")
        return False
    if status != 200:
        print(f"NOTE: admin permission lookup for {author} returned HTTP {status}. Not an admin.")
        return False
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        print(f"NOTE: admin permission lookup for {author} was not JSON. Not an admin.")
        return False
    return isinstance(payload, dict) and payload.get("permission") == "admin"
