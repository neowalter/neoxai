# Methods

Preprocessing, libraries, and **local-first** notes for EEG / BCI. Again: **links and short notes**, not vendored source trees.

## Core toolkits

| Tool | Role | Link |
| --- | --- | --- |
| MNE-Python | Load FIF/EDF, filters, ICA, viz, stats | [mne.tools](https://mne.tools) · [mne-tools/mne-python](https://github.com/mne-tools/mne-python) |
| MNE-BIDS | BIDS read/write | [mne.tools/mne-bids](https://mne.tools/mne-bids) |
| EEGLAB | MATLAB GUI + plugins | [sccn.ucsd.edu/eeglab](https://sccn.ucsd.edu/eeglab) |
| FieldTrip | MATLAB MEG/EEG | [fieldtriptoolbox.org](https://www.fieldtriptoolbox.org) |
| Brainstorm | GUI MEG/EEG | [neuroimage.usc.edu/brainstorm](https://neuroimage.usc.edu/brainstorm) |
| PREP pipeline | Standardized preprocessing | [VisLab/eeg-clean-tools](https://github.com/VisLab/eeg-clean-tools) · Bigdely-Shamlo et al., *Front. Neuroinform.*, 2015 |
| Autoreject | Automated bad epoch/channel | [autoreject.github.io](https://autoreject.github.io) |
| PyPREP | PREP in Python | [sappelhoff/pyprep](https://github.com/sappelhoff/pyprep) |
| braindecode | Deep learning on EEG | [braindecode.org](https://braindecode.org) |
| MOABB | Cross-dataset benchmarks | [github.com/NeuroTechX/moabb](https://github.com/NeuroTechX/moabb) |

## Practical order (typical offline study)

1. **Ethics / license** — you may not have the right to share derivatives.
2. **BIDS** if you can (`eeg_bids` / MNE-BIDS).
3. **Filter + resample** (document cutoff and causal vs acausal).
4. **Bad channels / reconnection** (PREP / PyPREP / autoreject).
5. **ICA or SSP** only if you understand what you remove.
6. **Keep a YAML/JSON of every parameter** next to the script.

This list is not a SOP for clinical EEG.

## WASM / local-first (NEOXLINK)

The companion site is built so **raw EEG time series are not uploaded**. Filtering, resampling, and spectra are intended to run **in the browser (WASM)** or on the researcher’s own machine.

Implications for this hub:

- Prefer methods that work on **local files** (MNE, EEGLAB, FieldTrip).
- Do not send `.edf` / `.fif` to a random “free cloud decoder.”
- Large foundation models that need a GPU still belong in a lab job or a user-owned runtime — not in the website database and not as binaries in `neoxai`.

See NEOXLINK architecture notes: edge WASM offloading; no EEG upload API.

## How to add a method

PR a row with docs URL + paper (if any) + whether it runs fully offline.
