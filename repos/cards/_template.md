---
schema: 1
repo: example-org/eeg-toolkit
summary:
  en: eeg-toolkit converts EDF recordings into feature tables for offline EEG experiments.
  # zh-Hans: optional Simplified Chinese summary, omitted until you have one
tasks:
  - signal-processing
  - dataset-tooling
modalities:
  - eeg
tags:
  - eeg
  - edf
  - features
status: experimental
version: "0.1.0"
# logo must be an image on github.com, raw.githubusercontent.com,
# camo.githubusercontent.com, avatars.githubusercontent.com, or
# user-images.githubusercontent.com. Example:
# logo: https://raw.githubusercontent.com/example-org/eeg-toolkit/main/logo.png
stack:
  frameworks:
    - name: example-lib
      url: https://example.com/example-lib
      version: "1.0"
  models: []
  datasets: []
  hardware: []
install:
  - label: pip
    command: python -m pip install eeg-toolkit
run:
  demo: https://example.com/eeg-toolkit
limitations:
  - Reads files on the local machine and does not stream from a headset.
blockers:
  - Headset streaming is not implemented in this example.
roadmap:
  - item: Document the CSV columns.
    state: planned
citation:
  cff: false
  bibtex: |
    @software{example_org_eeg_toolkit,
      title = {eeg-toolkit},
      author = {{example-org}},
      year = {2026},
      url = {https://github.com/example-org/eeg-toolkit}
    }
contributing:
  guide: https://github.com/example-org/eeg-toolkit/blob/main/CONTRIBUTING.md
  codeOfConduct: https://github.com/example-org/eeg-toolkit/blob/main/CODE_OF_CONDUCT.md
maintainers:
  - github: example-org
    name: Example Org
    role: maintainer
changelog:
  - version: "0.1.0"
    date: "2026-11-28"
    summary: Initial example card.
seo:
  title: eeg-toolkit offline EEG feature tables
  description: eeg-toolkit converts EDF recordings into feature tables for offline EEG experiments.
---

> Placeholder card for example-org/eeg-toolkit. Replace every section with this repository's own facts.

## Overview

eeg-toolkit converts EDF recordings into feature tables for offline EEG experiments. It runs on the researcher's machine.

## Quick start

Install the package, then convert one recording:

```bash
python -m pip install eeg-toolkit
eeg-toolkit convert subject01.edf features.csv
```

## Technical approach

eeg-toolkit keeps the recording on the local disk and writes a table of band-power features.

## Usage and API

`convert` reads one EDF file and writes one CSV file. Flags are documented in the repository README.

## Examples

```bash
eeg-toolkit convert subject01.edf features.csv
```

## Contributing

Issues and pull requests are welcome at https://github.com/example-org/eeg-toolkit.
