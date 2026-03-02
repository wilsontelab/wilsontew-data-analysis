# wilsontew-data-analysis
Data analysis for TEW lab

## Running the R notebooks

The notebooks and `.Rmd` files in this repo are written in **R**.

For multi-language Jupyter setup (R/Python/Java/C++ and notes on VBA), see:

- `KERNELS.md`
- `environment.yml` (reproducible conda environment)
- `00_Kernel_Check.ipynb` (quick kernel inventory)

### VS Code + Jupyter (recommended)

1. Install **R** (from CRAN).
2. In R, install the Jupyter kernel:

   - Install packages: `install.packages(c("IRkernel", "tidyverse", "knitr"))`
   - Register the kernel: `IRkernel::installspec(user = TRUE)`

3. In VS Code, install the **Jupyter** extension.
4. Open `MD_PD_Analysis.ipynb` and select the **R / IRkernel** kernel when prompted.

If you don't see an R kernel option, re-run `IRkernel::installspec()` in the same R installation you expect VS Code to use.
