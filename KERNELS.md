# Jupyter kernels for this repo

This repo primarily uses **R** analysis notebooks, but you can keep a "multi-language capable" Jupyter setup around for future work.

Jupyter notebooks (`.ipynb`) typically run **one kernel per notebook** (R *or* Python *or* Java...). If you want multiple languages in one notebook, see **SoS** below.

## What’s already available on this machine (quick check)

Run this in any terminal:

- `jupyter kernelspec list`

Or open `00_Kernel_Check.ipynb` and run the first code cell.

## Recommended: one reproducible environment (conda)

This repo includes `environment.yml` that installs:

- Python kernel (`python3`)
- R kernel (IRkernel)
- Java kernel (IJava)
- Optional SoS meta-kernel

Create it with **micromamba/mamba/conda** (pick one):

- `mamba env create -f environment.yml`
- `conda env create -f environment.yml`

Then activate it and (re)register kernels if needed:

- `conda activate wilsontew-jupyter-kernels`
- `python -m ipykernel install --user --name wilsontew-py --display-name "Python (wilsontew)"`
- `R -q -e "IRkernel::installspec(user = TRUE, name = 'wilsontew-r', displayname = 'R (wilsontew)', overwrite = TRUE)"`

### Important: keep kernelspecs independent of random project envs

When you run `ipykernel install --user` / `IRkernel::installspec(user = TRUE, ...)`,
the kernelspec is written into your **user Jupyter kernels directory** (on Windows:
`%APPDATA%\jupyter\kernels`). That’s a good thing:

- Your notebooks won’t accidentally depend on some other repo’s conda env.
- VS Code can discover the kernel even if you’re not currently “activated” into the env.

If your `R (wilsontew)` kernel is currently launching via a totally unrelated env,
just re-run the two registration commands above from inside the correct env; it
will overwrite the old kernelspec.

On Windows, there’s also a helper script that automates env creation + registration:

- `scripts/install-kernels-windows.ps1`

### If VS Code says: `spawn ... conda.exe ENOENT`

If the VS Code Jupyter log shows something like:

- `Kernel died Error: spawn C:/Users/<you>/miniforge3/Scripts/conda.exe ENOENT`

that means the `wilsontew-r` kernelspec you selected is trying to launch **via a hard-coded conda.exe path** that doesn’t exist on the machine where the kernel is being started.

Fix (Windows):

1. Re-run: `scripts/install-kernels-windows.ps1`
2. Restart VS Code.
3. Re-select kernel **R (wilsontew)**.

The installer will (re)register `wilsontew-r` and then **rewrite its kernelspec** to launch the environment’s `R.exe` via a small PowerShell wrapper, so it no longer depends on spawning `conda.exe` at runtime.

> Notes
>
> - `ijava` and `xeus-cling` usually self-register kernels during install, but re-registering is harmless.
> - VS Code discovers kernels from the active environment + your user kernelspec directory.

## Language-by-language notes

### R

- Kernel: **IRkernel**
- Install (inside R): `install.packages('IRkernel'); IRkernel::installspec(user = TRUE)`

### Python

- Kernel: **ipykernel**
- Install: `pip install ipykernel` (or conda)

### Java

- Kernel: **IJava**
- Requires a JDK (e.g., OpenJDK). The included `openjdk` + `ijava` handles this in conda.

### C++

- Kernel: **xeus-cling** (recommended)
- Status on Windows: **not reliably available** via conda-forge (you may see solver errors like “package does not exist” on `win-64`).

Practical options:

- **WSL2 (recommended)**: install the C++ kernel inside a Linux distro (Ubuntu) using conda-forge, then use VS Code’s WSL integration.
- **Alternative**: if your goal is “run C++ performance code”, consider calling compiled C++ from Python/R instead of running C++ *as a notebook kernel*.

### VBA (important limitation)

There is **no widely supported, standard Jupyter kernel for VBA** (the language that runs inside Microsoft Office).

Alternatives depending on what you meant:

- If you meant **Visual Basic .NET (VB.NET)**: use **.NET Interactive** (supports C#/F#/PowerShell; VB.NET support varies by version).
- If you truly need **VBA**: the practical approach is usually to run it via Excel itself, and drive it from a notebook using Python (e.g., `xlwings`, `pywin32`) or PowerShell.

## Multi-language in one notebook (optional)

If you want a single notebook to run multiple languages cleanly, use **SoS** (`sos`, `sos-notebook`) and add subkernels. This is optional; for most analysis work, keeping separate notebooks per language is simpler.
