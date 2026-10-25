This repository contains the analysis code for our manuscript ["Listening with your heart: The heartbeat shapes auditory object formation by suppressing the early neural response to sound."](https://doi.org/10.64898/2026.08.17.745255)

Data can be downloaded from _OpenNeuro_ at [this link](https://doi.org/10.18112/openneuro.ds007949.v1.0.0). Once you download the [BIDS-formatted](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electroencephalography.html) directory, you should rename it `bids_dataset`, since that is how all code refers to it. (Or, alternatively, rename it in the code... as long as they match). Please note that ECG data is contained within the EEG files, since they were recorded on the same amplifier.

There are two "environment files" to help you install the necessary software packages into sand-boxed environments using [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html):
* `extract_ffr-env.yml` is for running `extract_ffr.py` and `extract_ffr_fake.py`.
* `analysis-env.yml` is for main analyses.

`extract_ffr.py` and `extract_ffr_fake.py` run EEG preprocessing workflows. If you want to reproduce analyses from beginning to end, you should run `extract_ffr.py` before running `analysis.ipynb` and `extract_ffr_fake.py` before `revisions.ipynb`, since those notebooks use the outputs of the EEG preprocessing scripts.

The main analyses are in the following notebooks:
* `analysis.ipynb` runs the main behavioral and EEG analyses.
* `prevalence.ipynb` uses [prevalence statistics](https://doi.org/10.1038/s44271-025-00190-0) to check whether participants who could not identify what condition they were in (i.e., were effectively blinded) still showed the main behavioral effect.
* `demographics.ipynb` calculates some simple sample demographic.
* `revisions.ipynb` includes any additional analyses that were performed after our initial preprint (i.e., during peer review). I think the most interesting thing in here, to most people, is offline comparison of stimulus presentation times to the ECG waveform.

The `util` subdirectory contains helper functions used in the main scripts/notebooks.

Looking for our sample size calculation? Since that based off effect sizes from our computational model, it is actually found in a [different repository](https://doi.org/10.5281/zenodo.21432897) with the model code.
