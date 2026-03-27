# wilsontew-data-analysis

Data analysis for TEW lab

## 4C data location in this project

- **Raw 4C input data**: aligned `.sam` files specified in `SAM_SAMPLES` inside `FourC_OneShot_Python_Report.ipynb`.
- **Processed 4C outputs**: written by that notebook to `Outputs/4C_python`.
- **Combined PD+3C+4C notebook behavior**: `PD_3C_4C_Combined_Report.ipynb` reads 4C summary-style CSVs from `WILSONTEW_4C_FOLDER` (default `Outputs/4C_python`) when compatible files are present; otherwise it falls back to a proxy 4C layer.

## Running the R notebooks

The notebooks and `.Rmd` files in this repo are written in **R**.

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
4. Open `MD_PD_Analysis.ipynb` and select the **R / IRkernel** kernel when prompted.

Optional (Windows helper):

- `scripts/install-kernels-windows.ps1` will create/update the repo conda env and register the
   `R (wilsontew)` and `Python (wilsontew)` kernels into your user Jupyter kernels folder.

If VS Code’s Jupyter output mentions `spawn ... conda.exe ENOENT`, run the installer again; it will also harden the `R (wilsontew)` kernelspec so it doesn’t depend on a hard-coded conda path.

If you don't see an R kernel option, re-run `IRkernel::installspec()` in the same R installation you expect VS Code to use.
