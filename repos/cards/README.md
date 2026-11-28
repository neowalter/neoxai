# Project cards

One card per repository in [`repos/catalog.json`](../catalog.json). The card file is `repos/cards/<owner-lowercase>/<repo-lowercase>.md`. Maintainers write it. The site renders it.

The placeholder in this guide is `example-org/eeg-toolkit` only. Copy [`_template.md`](./_template.md) and replace it with the repository you maintain.

## Who may change a card

The GitHub owner of the upstream repository may change its card. A login listed in `.neox-ai.yml` at the root of that repository may change it too. The file shape is:

```yaml
maintainers:
  - example-org
  - teammate-login
```

`maintainers` is a list of GitHub logins. The check compares logins case-insensitively. It reads the owner from `items[].id` (`github:Owner/Repo`) in the catalog. It does not use the catalog `author` field. When your login is not that owner, commit `.neox-ai.yml` to the upstream repository first.

Hub admins do not edit card text. An admin delists a repository by appending to [`repos/delisted.json`](../delisted.json). Changes to this guide, `_template.md`, `card.schema.json`, or `repos/delisted.json` are accepted only when the pull request author is `neowalter`, the pull request author association is `OWNER`, or the GitHub permission API returns `admin`. A failed permission lookup is not treated as admin.

## License

Card text in this folder is licensed under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/), the license of this hub. See [`LICENSE`](../../LICENSE). You may share and adapt the card text with attribution.

The card does not relicense the upstream repository. Code, data, and model weights stay under their own terms.

The pull request template asks you to confirm both the license and your authority to edit the card. Unrelated pull requests can ignore that section. The checkbox does not replace the ownership check below.

## Site URLs

English is the site root. Simplified Chinese is `/cn/`. Do not use `/en/`.

| Page | URL |
| --- | --- |
| English card | `https://neox-ai.com/repos/<owner>/<repo>/` |
| Chinese card | `https://neox-ai.com/cn/repos/<owner>/<repo>/` |
| Example | https://neox-ai.com/repos/example-org/eeg-toolkit/ |
| Chinese example | https://neox-ai.com/cn/repos/example-org/eeg-toolkit/ |

Use the lowercase owner and repository name in the path, matching the card file.

## What the site fills in

The site reads public fields from `repos/catalog.json` and builds these itself:

- Repository name, owner, GitHub URL, and homepage
- Programming language
- SPDX license, or "No license detected" when none is recorded
- Stars and forks, shown with the catalog `generatedAt` date
- Last push, from `pushedAt`
- The archived flag from GitHub
- The GitHub description, used as the summary while the card is awaiting an author
- GitHub topics, used as tags when you do not set `tags`
- Task labels derived from topics when you do not set `tasks`, marked as coming from GitHub topics
- A letter avatar when you do not set `logo`
- `git clone`, `gh repo clone`, and an Open in GitHub Codespaces link
- Links to releases and issues
- A generated citation, labeled as generated, when you do not supply one
- Related repositories
- The page URL, the Chinese URL, the badge URL, and the JSON URL

The site does not copy `outreach` or the inferred `author` field onto the card.

## What you write

Required front matter, checked against [`card.schema.json`](./card.schema.json):

| Field | Rule |
| --- | --- |
| `schema` | `1` |
| `repo` | `owner/name`, matching the file path, case-insensitive |
| `summary.en` | 1–140 characters |
| `status` | `experimental`, `alpha`, `beta`, `stable`, `maintenance`, or `deprecated` |
| `maintainers` | At least one person. Your pull request login must be in `maintainers[].github` |

Required headings in the body: `## Overview` and `## Quick start`.

Optional front matter: `summary.zh-Hans`, `tasks` (at most 4), `modalities`, `tags` (at most 12), `version`, `logo`, `stack` (`frameworks`, `models`, `datasets`, `hardware`), `install` (at most 6 commands, each command at most 300 characters), `run` (`colab`, `docker`, `demo`), `limitations` and `blockers` (at most 10 items, 200 characters each), `roadmap` (at most 12 items, 160 characters each; state `planned`, `in-progress`, or `done`), `citation`, `contributing`, `changelog` (at most 20 entries), and `seo` (title at most 60 characters, description at most 160).

Optional headings, after the required ones: `## Technical approach`, `## Usage and API`, `## Examples`, and `## Contributing`.

Quote versions and dates. YAML otherwise turns `1.0` into a number and `2026-11-28` into a date, and the schema then rejects them. Task and modality values must be the enums in the schema. Unknown keys are rejected.

`logo`, when you set it, must be an `http` or `https` URL whose host is one of:

- `github.com`
- `raw.githubusercontent.com`
- `camo.githubusercontent.com`
- `avatars.githubusercontent.com`
- `user-images.githubusercontent.com`

The card file must be 20 KB or smaller (20480 bytes).

## Voice

Write the summary in the present tense: "{Name} {verb}s {what} for {context}." Stay within 140 characters. Do not use "I" or "we" in the summary. Do not make a medical or diagnostic claim. Do not use a marketing superlative unless you can point at a citation.

Example summary for `example-org/eeg-toolkit`:

> eeg-toolkit converts EDF recordings into feature tables for offline EEG experiments.

The check fails the pull request when `summary.en` or the body contains these as whole words, case-insensitively: `diagnose`, `diagnoses`, `diagnosis`, `treat`, `treats`, `cure`, `cures`, `clinically proven`, `medical-grade`, `FDA-cleared`, `FDA-approved`.

The check warns, and does not fail, on: `first`, `best`, `only`, `#1`, `unleash`, `empower`, `revolutionize`, `game-changing`, `seamless`, `delve`, `cutting-edge`, `state-of-the-art`, `fostering`. The warning does not look for a citation. If the superlative is true, put the citation in the card anyway.

The scan includes code blocks in the body. Rephrase a command or a sentence that contains a blocked word.

## Card states

- **Awaiting author.** No card file yet. The page uses catalog data, stays `noindex`, and shows that the author has not written the card.
- **Author card.** A merged card file. The page can be indexed. Your text is merged with the catalog facts above.
- **Delisted.** An admin lists the repository in `repos/delisted.json`. The site serves no project-card page. The archived flag is separate: it comes from GitHub.

## Submit a card

1. Fork `neowalter/neoxai`.
2. Add one file: `repos/cards/<owner-lowercase>/<repo-lowercase>.md`.
3. Start from `_template.md`. Set `repo` to the GitHub `owner/name`. Casing in `repo` may follow GitHub. The path is lowercase. They must match, ignoring case.
4. Open a pull request that changes that file and nothing else. A second path fails the check, including edits to this guide, the catalog, or the workflow.
5. Wait for the `cards-check` status check.
6. A maintainer merges the pull request. `cards-compile` then writes [`repos/cards.json`](../cards.json).

This hub does not open issues or pull requests on the upstream repository. The README badge on the site is offered and never required.

## What the check rejects

`cards-check` runs on every pull request. If the pull request does not change `repos/cards/**` or `repos/delisted.json`, the check passes immediately.

Otherwise it fails, with a log line, when any of these is true:

1. The pull request does not change exactly one lowercase `repos/cards/<owner>/<repo>.md` and nothing else. Guide, template, schema, and delist edits are the admin exception above.
2. That `owner/repo` is missing from `repos/catalog.json` `items[].id`, or it is already in `repos/delisted.json`.
3. The pull request author is not the catalog owner, and is not listed in `.neox-ai.yml` on the upstream repository. The check fetches `https://cdn.jsdelivr.net/gh/<owner>/<repo>@HEAD/.neox-ai.yml` and, if that fails, the GitHub contents API. A failed fetch means the author is not listed. It is not a pass.
4. The front matter does not match `card.schema.json`, or the body lacks `## Overview` or `## Quick start`.
5. `summary.en` or the body contains a blocked claim above.
6. The file is over 20 KB, or `logo` uses a host outside the list above.
7. `maintainers[].github` does not include the pull request author.

Warnings for marketing words are logged and do not fail the check.

Deleting a card file is not how removal works. Open the repo-removal issue instead.

## Removal

Open a GitHub issue with the [repo-removal form](https://github.com/neowalter/neoxai/issues/new?template=repo-removal.yml). The form asks for the repository URL, your GitHub login, and the reason. It does not ask for an email address or a phone number.

The published default response window is 7 days.

To suggest a repository that is not in the index, use the [suggest-repository form](https://github.com/neowalter/neoxai/issues/new?template=suggest-repo.yml). It asks for the GitHub URL and why the repository belongs in a BCI/EEG index. It does not ask for an email address or a phone number.

## Delist file

`repos/delisted.json` starts as `{ "repos": [] }`. An admin appends an object:

```json
{
  "repo": "example-org/eeg-toolkit",
  "reason": "Maintainer requested removal.",
  "date": "2026-11-28"
}
```

`repo` is `owner/name`. `reason` and `date` are strings. Do not add other fields. Delisting hides the project card on the site. It does not delete the upstream GitHub repository. A card file may remain in this folder; the site still hides a delisted id.

## Compiled file

After a card change merges to `main`, `cards-compile` validates the card files again and writes `repos/cards.json`:

```json
{
  "schemaVersion": 1,
  "generatedAt": "2026-11-28T00:00:00Z",
  "cards": [
    {
      "repo": "Example-Org/eeg-toolkit",
      "path": "repos/cards/example-org/eeg-toolkit.md",
      "frontmatter": {},
      "body": "",
      "lastEditor": null,
      "updatedAt": "2026-11-28T00:00:00+00:00",
      "commit": "abc123"
    }
  ]
}
```

`repo` uses the catalog's `Owner/Repo` casing when the id is in the catalog. `updatedAt` and `commit` come from git. `lastEditor` is `null`. The workflow commits only when the card set changed, as `neoxai-bot <neoxai-bot@users.noreply.github.com>`, with the message `Compile project cards into repos/cards.json.` It uses the Actions `GITHUB_TOKEN` only. Zero card files produce `"cards": []`. `_template.md` is not a card.

## How the check avoids executing pull request code

- The workflow triggers on `pull_request` with `permissions: contents: read`. It does not use `pull_request_target`.
- Actions checks out `github.event.pull_request.base.sha` and runs `.github/scripts/cards_check.py` from that tree.
- Changed paths come from the GitHub compare API. File bytes come from the GitHub contents or blob API.
- Those bytes are parsed as data: JSON, or YAML with a safe loader that rejects anchors and aliases. The job does not check out the head branch, does not import the card, and does not run a script from the head.
- The job has no write permission and does not post a comment. It fails the job and prints the reason.

A pull request that replaces `.github/workflows/cards-check.yml` can change the job GitHub runs for that pull request. The ruleset below is what stops a green check from being optional. Review any pull request that edits the workflow file.

## Repository admin setup

Create a ruleset on `main` in GitHub: **Settings → Rules → Rulesets**. Require the status check named `cards-check`. If the picker shows `cards-check / cards-check`, select that check. Allow no bypass.

You cannot create this ruleset from a file in the repository.

Target the ruleset at pull requests. `cards-compile` pushes `repos/cards.json` to `main` with the Actions token. A ruleset that blocks every push to `main` also blocks that compile commit.

Approval never replaces `cards-check`. Auto-approve does not approve a pull request that touches `repos/cards/` unless the author is the catalog owner of each card file in that pull request. A passing review is not a substitute for the status check. Turn the ruleset on before relying on auto-merge: auto-merge waits only for required checks.

## Catalog producer

The catalog producer lives outside this repository. Please stop publishing `outreach` on the public `repos/catalog.json`, and add `firstIndexedAt` to each item. Do not rewrite `repos/catalog.json` in a pull request to strip those fields by hand. The producer should stop emitting them.

## Growth boundaries

Authors complete a card with a pull request in this hub. This repository does not send automated notices, issues, or pull requests to upstream repositories. The site badge is optional. Removal requests use the issue form above. The published default response window is 7 days.
