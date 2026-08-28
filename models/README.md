# Models

Open **EEG decoding** architectures and **large / foundation** EEG models. Links go to GitHub or Hugging Face. **Weights stay upstream** — do not commit checkpoints here.

| Model / library | Kind | Links | Notes |
| --- | --- | --- | --- |
| EEGNet | Compact CNN for BCI | [arl-eegmodels](https://github.com/vlawhern/arl-eegmodels) | Lawhern et al., *JNE*, 2018 |
| Deep/Shallow ConvNet | CNN baselines | [braindecode](https://github.com/braindecode/braindecode) | Schirrmeister et al., *HBM*, 2017 |
| ATCNet | Attention temporal CNN (MI) | [EEG-ATCNet](https://github.com/Altaheri/EEG-ATCNet) | Altaheri et al. |
| EEG Conformer | CNN + Transformer | [EEG-Conformer](https://github.com/eeyhsong/EEG-Conformer) | Song et al. |
| BENDR | Transformer + contrastive EEG | [SPOClab-ca/BENDR](https://github.com/SPOClab-ca/BENDR) | Kostas et al., 2021 |
| BIOT | Biosignal transformer | [ycq091044/BIOT](https://github.com/ycq091044/BIOT) | Yang et al.; check data licenses |
| LaBraM | Large brain model (EEG tokens) | [935963004/LaBraM](https://github.com/935963004/LaBraM) | Jiang et al., ICLR 2024; TUH-related constraints |
| EEGPT | Pretrained EEG transformer | [BINE022/EEGPT](https://github.com/BINE022/EEGPT) | Wang et al.; read the card |
| CBraMod | Foundation-style EEG | [wjq-learning/CBraMod](https://github.com/wjq-learning/CBraMod) | Wang et al. |
| Neuro-GPT | GPT-style EEG | [wenhui0206/NeuroGPT](https://github.com/wenhui0206/NeuroGPT) | Experimental |
| braindecode | Training library (skorch) | [braindecode](https://github.com/braindecode/braindecode) · [docs](https://braindecode.org) | Wraps many of the CNNs above |
| MOABB | Benchmark harness | [NeuroTechX/moabb](https://github.com/NeuroTechX/moabb) | Compare methods on public sets |
| Hugging Face Hub | Search `eeg`, `bci`, `eeg-foundation` | [huggingface.co](https://huggingface.co/models?search=eeg) | Prefer cards that state training data + license |

## Using large EEG models

1. Confirm **training-data license** (TUH is not “download and ship”).
2. Prefer official cards over anonymous mirrors.
3. For on-device / browser paths, the NEOXLINK product runs DSP in WASM and **does not upload raw EEG**. Foundation-model inference that needs a GPU still happens on the user’s machine or a lab cluster — not as a hidden upload API in this hub.

## How to add a model

PR a row with paper + code/HF URL + one line on data constraints. No `.bin` / `.safetensors` in the PR.
