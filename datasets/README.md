# Datasets

Selected **open or research-accessible** EEG / BCI / MEG corpora. This folder is a **link list**. We do **not** host recordings, BIDS trees, or Git-LFS objects.

Always re-read the upstream license before download or publication. Several corpora require a signed DUA, an application form, or PhysioNet login. “Listed here” ≠ “redistributable.”

| Dataset | What it is | Official access | License / access | Cite (start here) |
| --- | --- | --- | --- | --- |
| EEG Motor Movement/Imagery (EEGMMI) | 64-ch BCI2000 MI / movement | [PhysioNet eegmmidb](https://physionet.org/content/eegmmidb/1.0.0/) | PhysioNet open access | Schalk et al., *IEEE TBME*, 2004; Goldberger et al., *Circulation*, 2000 |
| CHB-MIT Scalp EEG | Pediatric seizure scalp EEG | [PhysioNet chbmit](https://physionet.org/content/chbmit/1.0.0/) | PhysioNet open access | Shoeb, MIT PhD, 2009; PhysioNet |
| Sleep-EDF | Sleep polysomnography (EEG/EOG/EMG) | [PhysioNet sleep-edfx](https://physionet.org/content/sleep-edfx/1.0.0/) | PhysioNet open access | Kemp et al.; PhysioNet |
| BCI Competition IV | Classic MI / P300 / motor benchmarks | [bbci.de/competition/iv](https://www.bbci.de/competition/iv/) | Competition terms (research) | Tangermann et al., *Front. Neurosci.*, 2012 |
| BNCI Horizon 2020 | Many organized BCI sets (2a, 2b, …) | [BNCI database](http://bnci-horizon-2020.eu/database/data-sets) | Per-dataset | Original competition / paper per set |
| MOABB | Unified Python access to many BCI sets | [NeuroTechX/moabb](https://github.com/NeuroTechX/moabb) | BSD-3 (library); data licenses vary | Jayaram & Barachant, *JMLR*, 2018 |
| High-Gamma Dataset | High-γ / motor EEG, ConvNet paper | [robintibor/high-gamma-dataset](https://github.com/robintibor/high-gamma-dataset) | See repo | Schirrmeister et al., *HBM*, 2017 |
| TUH EEG (TUEG) and subsets | Large clinical EEG (used by several foundation models) | [TUH EEG](https://isip.piconepress.com/projects/nedc/html/tuh_eeg/) | **Registration + research DUA; not a public dump** | Obeid & Picone, *Front. Neurosci.*, 2016 |
| ERP CORE | Optimized ERP experiments | [erpinfo.org/erp-core](https://erpinfo.org/erp-core) | CC-BY (confirm on page) | Kappenman et al., *NeuroImage*, 2021 |
| Things-EEG / Things-EEG2 | RSVP / visual decoding EEG | [Things-EEG2 (OSF)](https://osf.io/3jk45/) | OSF terms / CC as stated on OSF | Gifford et al.; see OSF wiki |
| DEAP | Emotion (EEG + peripheral) | [DEAP](https://www.eecs.qmul.ac.uk/mmv/datasets/deap/) | **Application required** | Koelstra et al., *IEEE Trans. Affect. Comput.*, 2012 |
| SEED / SEED-IV / SEED-V | Emotion EEG (SJTU BCMI) | [BCMI SEED](https://bcmi.sjtu.edu.cn/home/seed/) | **Application required** | Zheng & Lu and follow-ups |
| OpenNeuro EEG/MEG | BIDS-formatted public scans | [openneuro.org](https://openneuro.org) (filter EEG/MEG) | Per-dataset (often CC0 / CC-BY) | Dataset accession + paper |
| MNE-Python sample | Tiny FIF for tutorials | [mne.datasets.sample](https://mne.tools/stable/documentation/datasets.html) | MNE sample license | Gramfort et al., *Front. Neurosci.*, 2013 |
| Helsinki neonatal EEG | Term-infant scalp EEG | [zenodo 1250690](https://zenodo.org/records/1250690) (confirm current DOI) | CC as on Zenodo | Stevenson et al. |
| ZuCo | EEG + eye tracking while reading | [OSF ZuCo](https://osf.io/q3zws/) | OSF / paper terms | Hollenstein et al. |
| Grasp-and-Lift EEG | Kaggle motor EEG | [Kaggle grasp-and-lift](https://www.kaggle.com/c/grasp-and-lift-eeg-detection/data) | Kaggle + original DUA | Luciw et al. / contest page |

## How to add a dataset

PR a new row: short name, one-line description, **canonical** URL (not a random mirror), license/access, citation. Reject rows that only point at a personal Google Drive of copied PhysioNet files.

## Related

- Models trained on TUH/TUEG often **cannot** ship weights that include the data. Read the model card.
- For decoding baselines in Python, start with [MOABB](https://github.com/NeuroTechX/moabb) + [braindecode](https://github.com/braindecode/braindecode) rather than ad-hoc CSV dumps.
