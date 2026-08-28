# News archive

Industry and vendor notes that pass the BCI / EEG / large-EEG-model filter. Research preprints go in [`../papers/`](../papers/README.md).

## Files

| Path | Writer | Shape |
| --- | --- | --- |
| `news/YYYY-MM.md` | `neoxlink-cron` (GitHub Git Data API, one commit per run) | Markdown sections |
| `news/YYYY-MM-DD.json` | *not used in v1* | Reserved if a daily JSON dump is ever needed |

Cron caps **≤20 files changed per run** and prefers **one monthly markdown per kind** so a typical run updates `news/YYYY-MM.md` and/or `papers/YYYY-MM.md` only.

## Record fields

| Field | Rule |
| --- | --- |
| title | Feed title, clipped |
| url | Canonical `http(s)` URL (unique) |
| published | ISO-8601 UTC when the feed provides it |
| source | `news_sources.slug` (e.g. `neurosity-blog`) |
| summary | Plain text, **≤400 characters**, never the article body |
| arxiv | Optional `YYYY.NNNNN` when the URL is an arXiv abs/pdf |

## Example

```markdown
# BCI / EEG industry news — 2026-08

Curated by NEOXLINK cron for neoxai. Summaries are ≤400 characters.

### OpenBCI GUI 6.0.0

- url: https://github.com/OpenBCI/OpenBCI_GUI/releases/tag/v6.0.0
- source: github-openbci-gui
- published: 2026-08-01T00:00:00.000Z
- summary: Release notes excerpt…
```

## Editing

Do not paste secrets. Do not attach binaries. Duplicate URLs are skipped on merge. Hand edits of monthly files may be overwritten if the same URL is ingested again with a different summary — prefer fixing the crawler in NEOXLINK.
