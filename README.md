# wilsontew-data-analysis

Data analysis for TEW lab

## Running notebooks in order (PD → 3C → 4C)

Run these notebooks from the repository root in this order:

1. `notebooks/full_analysis_notebooks/PD_OneShot_Report.ipynb`
2. `notebooks/full_analysis_notebooks/ThreeC_OneShot_Report.ipynb`
3. `notebooks/full_analysis_notebooks/FourC_OneShot_Python_Report.ipynb`

> Optional integration notebook after all three are complete:
> `notebooks/full_analysis_notebooks/PD_3C_4C_Combined_Report.ipynb`

### 1) PD notebook

- **Notebook**: `notebooks/full_analysis_notebooks/PD_OneShot_Report.ipynb`
- **Kernel**: R (`R (wilsontew)` / IRkernel)
- **Data processed (relative in-repo path)**:
  - Primary input folder: `data/raw/Input_Data/PD_data`
  - Fallback local folder (if using env var defaults): `PD_Data`
- **What it writes**:
  - Notebook-local artifacts: `notebooks/full_analysis_notebooks/Outputs/PD`

### 2) 3C notebook

- **Notebook**: `notebooks/full_analysis_notebooks/ThreeC_OneShot_Report.ipynb`
- **Kernel**: R (`R (wilsontew)` / IRkernel)
- **Data processed (relative in-repo path)**:
  - Primary input folder: `data/raw/Input_Data/3C`
  - Fallback local folder (if using env var defaults): `ThreeC_Data`
  - Primer/DSB metadata used by mapping steps: `data/raw/Insertion_Primers_for_Locations_of_DSBs.csv`
- **What it writes**:
  - Notebook-local artifacts: `notebooks/full_analysis_notebooks/Outputs/3C`
  - Main exported summaries/figures: `Outputs/3C`

### 3) 4C notebook

- **Notebook**: `notebooks/full_analysis_notebooks/FourC_OneShot_Python_Report.ipynb`
- **Kernel**: Python (`Python (wilsontew)`)
- **Data processed (relative in-repo path)**:
  - Raw SAM inputs are configured in `SAM_SAMPLES` and resolved from:
    - `data/raw/Input_Data/4C/old_filtering_attempts`
    - `data/raw/Input_Data/4C/joey_filtered_final`
  - DSB metadata: `data/raw/Insertion_Primers_for_Locations_of_DSBs.csv`
- **What it writes**:
  - Main 4C outputs: `Outputs/4C_python`

### Optional: combined PD + 3C + 4C notebook

- **Notebook**: `notebooks/full_analysis_notebooks/PD_3C_4C_Combined_Report.ipynb`
- **Data it reads (relative in-repo defaults)**:
  - PD: `PD_Data` (or `WILSONTEW_PD_FOLDER`)
  - 3C: `ThreeC_Data` (or `WILSONTEW_3C_FOLDER`)
  - 4C summaries: `Outputs/4C_python` (or `WILSONTEW_4C_FOLDER`)
- **What it writes**:
  - Combined outputs: `Outputs/PD_3C_4C`

## Notebook environment setup

Most notebooks and `.Rmd` files in this repo are written in **R**; the 4C one-shot notebook is **Python**.

For multi-language Jupyter setup (R/Python/Java/C++ and notes on VBA), see:

- `KERNELS.md`
- `environment.yml` (reproducible conda environment)

### VS Code + Jupyter (recommended)

> Note on **GitHub virtual workspaces** (e.g., opening the repo via the VS Code
> **GitHub Repositories** extension so paths look like `vscode-vfs://...`):
> notebook execution is not always supported there. If kernels won’t start,
> **clone the repo locally** and open the local folder in VS Code.

1. Install **R** (from CRAN).
2. In R, install the Jupyter kernel:

   - Install packages: `install.packages(c("IRkernel", "tidyverse", "knitr"))`
   - Register the kernel: `IRkernel::installspec(user = TRUE)`

3. In VS Code, install the **Jupyter** extension.
4. Open the notebook you want to run and select the matching kernel:
   - PD / 3C / combined notebooks: **R / IRkernel**
   - 4C one-shot notebook: **Python**

Optional (Windows helper):

- `scripts/install-kernels-windows.ps1` will create/update the repo conda env and register the
   `R (wilsontew)` and `Python (wilsontew)` kernels into your user Jupyter kernels folder.

If VS Code’s Jupyter output mentions `spawn ... conda.exe ENOENT`, run the installer again; it will also harden the `R (wilsontew)` kernelspec so it doesn’t depend on a hard-coded conda path.

If you don't see an R kernel option, re-run `IRkernel::installspec()` in the same R installation you expect VS Code to use.
