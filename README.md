# TRAFIKK Paper Reproducibility Repository

This repository contains the data, configuration files, scripts, and intermediate results required to reproduce the analyses presented in the TRAFIKK paper.

The repository is organized around the two drug-screen datasets used in the study:

* **Sanger-2024**
* **Merck-2016**

At present, the complete TRAFIKK workflow has been prepared and verified for **Sanger-2024**. The corresponding Merck-2016 results and workflow will be added following the same repository structure.

For detailed information about the individual TRAFIKK modules, their parameters, and implementation, please refer to the corresponding module repositories and documentation. This README provides an overview of the paper reproducibility repository, while dataset-specific reproduction instructions are provided separately.

---

## TRAFIKK workflow

The analyses follow the TRAFIKK workflow:

```text
Experimental drug-screen data
        ↓
Data preprocessing
        ↓
01 Celios
        ↓
02 Drexpa
        ↓
03 Gitsbe
        ↓
04 Oris
        ↓
05 Synco
        ↓
06 Siflex
```

Each step generates files that are used directly or indirectly by subsequent stages.

---

## Repository structure

```text
trafikk_paper/
├── config/
│   ├── Sanger-2024/
│   └── Merck-2016/
│
├── data/
│   ├── metadata/
│   ├── kegg/
│   ├── network/
│   ├── nodes/
│   └── omics/
│
├── documentation/
│   ├── Sanger-2024.md
│   └── Merck-2016.md
│
├── results/
│   ├── Sanger-2024/
│   │   ├── 01_celios/
│   │   ├── 02_drexpa/
│   │   ├── 03_gitsbe/
│   │   ├── 04_oris/
│   │   ├── 05_synco/
│   │   ├── 06_siflex/
│   │   └── run_folders/
│   │
│   └── Merck-2016/
│
├── scripts/
│
├── requirements.txt
└── README.md
```

### `data/`

Contains the input files used across the TRAFIKK workflow.

The data are organized by type:

* `metadata/` — drug-screen and cell-line metadata
* `kegg/` — KEGG-related files
* `network/` — network files
* `nodes/` — node dictionaries and related files
* `omics/` — omics datasets used during model calibration

### `config/`

Contains the configuration files used for each TRAFIKK module.

Configurations are separated by dataset:

```text
config/Sanger-2024/
config/Merck-2016/
```

Before running each module, check that the paths and user-defined parameters in the corresponding configuration file match the current dataset.

### `results/`

Contains intermediate and final outputs from each TRAFIKK step.

For Sanger-2024:

```text
results/Sanger-2024/
├── 01_celios/
├── 02_drexpa/
├── 03_gitsbe/
├── 04_oris/
├── 05_synco/
├── 06_siflex/
└── run_folders/
```

The same general organization will be used for Merck-2016.

### `run_folders/`

`results/<dataset>/run_folders/` contains the tissue-specific directories and cell-line subdirectories used during the model-generation workflow.

Its general organization is:

```text
run_folders/
└── tissue/
    └── CELL_LINE/
```

These folders are progressively populated during the first TRAFIKK steps.

* Celios and Drexpa generate cell-line-specific files.
* Additional Gitsbe input files are copied into these folders before model ensemble generation.
* Gitsbe is run independently for each cell line.
* Gitsbe outputs remain inside the corresponding cell-line folders.
* These folders subsequently provide the inputs required by Oris.

### `scripts/`

Contains preprocessing and result-processing notebooks used in the paper analyses.

### `documentation/`

Contains dataset-specific reproduction instructions and additional documentation required for the paper analyses.

---

## Installation

Install the dependencies used for the paper analyses from the repository root:

```bash
pip install -r requirements.txt
```

The `requirements.txt` file contains the TRAFIKK modules and other Python dependencies required by the workflow.

Some TRAFIKK modules may be installed from Python packages, while others may reference their corresponding Git repositories.

Before running the workflow:

1. Install the dependencies.
2. Confirm that the required files are present under `data/`.
3. Check the configuration file for the module being run.
4. Confirm that input and output paths correspond to the selected dataset.

---

## Data preprocessing

Before running TRAFIKK, the original experimental drug-screen data are processed into the formats required by the pipeline.

Separate notebooks are provided for each dataset:

```text
scripts/pre_process_data_S2024.ipynb
scripts/pre_process_data_M2016.ipynb
```

These notebooks prepare the experimental data used by subsequent TRAFIKK steps.

---

## Reproducing the analyses

Dataset-specific reproduction instructions are provided separately:

* **Sanger-2024:** `documentation/Sanger-2024.md`
* **Merck-2016:** `documentation/Merck-2016.md`

These guides describe the commands, configuration requirements, intermediate files, and result-processing steps used to reproduce each analysis.

The Sanger-2024 workflow has been prepared and verified. The corresponding Merck-2016 analysis will be added following the same general repository organization.

---

## Module documentation

This repository intentionally focuses on the information required to reproduce the analyses presented in the paper.

For detailed documentation of individual TRAFIKK modules, including configuration options and implementation details, refer to their corresponding repositories:

* **Celios** — https://github.com/druglogics/celios
* **Drexpa** — https://github.com/druglogics/drexpa
* **Gitsbe** — https://github.com/druglogics/gitsbe
* **Oris** — https://github.com/druglogics/oris
* **Synco** — https://github.com/ViviamSB/SYNCO
* **Siflex** — https://github.com/druglogics/siflex

---

## Citation

If you use TRAFIKK or reproduce analyses from this repository, please cite:

> Fariñas M.§, Bermúdez V.§, Tsirvouli E., Lippestad K., Zobolas J., Aittokallio T., Lehti K., Flobak Å.
> **TRAFIKK: systematic prediction and mechanistic interpretation of anticancer drug synergies.**

§ These authors contributed equally to this work.

Full publication details will be updated when available.
