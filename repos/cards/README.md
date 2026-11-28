# Author project cards

This folder holds the author-completed cards shown on [neox-ai.com/repos](https://neox-ai.com/repos/). Auto-generated listings stay “Awaiting author” until the matching file here is merged.

## Add or edit your card

1. Copy [`_template.md`](./_template.md) to `repos/cards/<owner>/<repo>.md`.
2. Use lowercase `owner` and `repo` that match your GitHub repository, for example `repos/cards/octocat/hello-world.md`.
3. Fill in the YAML front matter. Required fields are `schema`, `repo`, `summary.en`, `status`, and `maintainers`. The published shape is [neox-ai author card v1](https://neox-ai.com/api/repos/card.schema.json).
4. Open a pull request against this repository.

Card text is published under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).

## Who can change a card

A workflow checks the GitHub login on the pull request. The login must **own** the repository, or be listed in that repository’s `.neox-ai.yml`. This site’s pages do not run that check.

Place `.neox-ai.yml` at the root of *your* repository (not in this hub), on the default branch:

```yaml
# GitHub logins that may add or update repos/cards/<owner>/<repo>.md here
editors:
  - your-github-login
```

This is required when the repository is owned by an organization, because the owner login is the organization name.

The hub owner may [request removal](https://github.com/neowalter/neoxai/issues/new?template=repo-removal.yml) or otherwise delist a card. They do not silently edit someone else’s author file.

Guide: [English](https://neox-ai.com/repos/maintainers/) · [中文](https://neox-ai.com/cn/repos/maintainers/)

## Share your card

The template includes a badge you can paste into your README. It links to your card on neox-ai.com. Completing a card (and keeping a detected license plus an English summary, on a repository that is not archived or delisted) is also what makes a project eligible for the unpaid, rules-based featured-this-week list.
