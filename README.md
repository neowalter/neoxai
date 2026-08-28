# neoxai

**Curated open resources for brain–computer interfaces (BCI), EEG analysis, and large-scale EEG models.**

This public hub is the long-lived archive next to [neox-ai.com](https://neox-ai.com) (code: [NEOXLINK](https://github.com/neowalter/NEOXLINK)). The website database stays small: it only keeps a short rolling window of headlines. **Full news and paper metadata live here as compact Git files**, not in Cloudflare KV/R2 and not as unbounded Supabase rows.

中文：本仓是脑机接口 / EEG 分析 / 大规模脑电模型的**精选链接与资讯归档**。不托管 GB 级数据文件；站点数据库只留最近条目，完整归档由定时任务写入本仓。

## Scope

**In**

- Open **datasets** useful for EEG / MEG / related neural interfaces (links + license + citation)
- Open **models** for EEG decoding and EEG foundation / large-scale pretraining (Hugging Face / GitHub)
- **Methods** and tooling (MNE, PREP, BIDS, local-first / WASM notes)
- **Industry news** and **research papers** on BCI, EEG data analysis, and large-scale EEG models (archived by cron)

**Out**

- Generic tech news (no Solidot-style firehose)
- Unrelated GitHub releases
- Google Scholar (it is not RSS; cron uses the [arXiv API](https://info.arxiv.org/help/api/index.html) plus category Atom feeds)
- Gigabyte `.edf` / `.fif` / weight dumps — **do not Git-LFS them into this repo**
- Clinical advice or medical-device claims

Raw EEG in the companion product never leaves the browser. This repo is documentation and metadata only.

## Layout

```
README.md              this file
LICENSE                CC-BY-4.0 for *our* docs and archive metadata
CITATION.cff           how to cite the hub
datasets/README.md     selected EEG/BCI datasets (links, not files)
models/README.md       decoding / foundation models
methods/README.md      preprocessing, MNE, local-first notes
news/README.md         industry-news archive format
news/YYYY-MM.md        monthly news (written by cron)
papers/README.md       paper archive format
papers/YYYY-MM.md      monthly papers (arXiv / bioRxiv / medRxiv / journals)
```

No Git LFS. No binary datasets. If a PR adds a large blob, it will be rejected.

## How the cron archive works

[NEOXLINK](https://github.com/neowalter/NEOXLINK) runs **one** Cloudflare Cron Trigger on Worker `neoxlink-cron`:

| | |
| --- | --- |
| Schedule | `23 */6 * * *` (UTC), every six hours |
| Feeds | Allowlisted RSS/Atom only (arXiv API + `cs.HC`/`q-bio.NC`/`eess.SP`, bioRxiv/medRxiv, Frontiers Neuroprosthetics, OpenBCI forum, Neurosity blog, OpenBCI_GUI releases) |
| Filter | Title + abstract must match BCI / EEG / MEG / neural-interface / EEG-foundation keywords (vendor/community sources already on-theme may pass). Mismatches are dropped. |
| Write | GitHub **Git Data API**, **one commit per run**, ≤20 file updates. Author: `neoxai-bot`. |
| Site DB | After a successful commit, Supabase `news_items` keeps a **thin pointer** (`url` + `github_path`) for the rolling window only: **last 30 days ∩ last 50 rows**. Older rows are deleted. |

Example record in `news/2026-08.md` or `papers/2026-08.md`:

```markdown
### EEG foundation models for motor imagery BCI

- url: https://arxiv.org/abs/2608.24887
- source: arxiv-api-bci
- published: 2026-08-28T02:28:20.000Z
- arxiv: 2608.24887
- summary: Plain-text excerpt, truncated to 400 characters.
```

Cron **does not** store article HTML, PDFs, or feed secrets. Commits never contain tokens.

If you are reading a monthly file: treat it as a bibliography of links, not a republication of the paper.

## How to cite

**This hub** (the curation and archive files we authored):

> neowalter. (2026). *neoxai: curated BCI/EEG datasets, models, methods, and news archives*. GitHub. https://github.com/neowalter/neoxai CC-BY-4.0

See [`CITATION.cff`](./CITATION.cff).

**Each dataset, model, or paper** must be cited under **its own** license and preferred citation (usually a data descriptor or the original article). Copying a row from `datasets/README.md` is not a substitute for the upstream citation.

## License

| Material | License |
| --- | --- |
| README files, curated tables, cron archive metadata in `news/` and `papers/` | [CC-BY-4.0](./LICENSE) |
| Linked datasets, weights, code, PDFs | **Original licenses only** — we do not relicense them |

## How to contribute

1. **Datasets / models / methods** — open a PR that adds a row to the relevant README: name, official URL, license (or “application required”), and a citation (DOI or paper). Prefer sources that are actually obtainable (PhysioNet, OpenNeuro, MOABB, Hugging Face, GitHub).
2. **Do not** attach data files, checkpoints, or `git-lfs` pointers.
3. **News/papers** — do not hand-edit monthly files to “fix” cron output unless a URL is wrong; the next run appends by URL. To change *what* is ingested, propose a feed change in NEOXLINK (`packages/db/supabase/seeds/070_news_sources.sql` and the cron topic filter).
4. Keep summaries factual. No medical claims.

Issues and PRs are welcome. This is a curated list, not a mirror of the entire internet.

## See also

- Site: [neox-ai.com](https://neox-ai.com)
- Code: [neowalter/NEOXLINK](https://github.com/neowalter/NEOXLINK) (private application monorepo)
- Open hub page on the site: `/open/` (links here)
