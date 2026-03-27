<#
Purpose
  Helper notes for setting up a multi-language Jupyter environment on Windows.

This script is intentionally conservative:
  - It does NOT install anything automatically.
  - It prints what you should run (so you can choose conda vs mamba vs micromamba).

If you want an automated installer that creates the env and registers kernels
into the user kernelspec folder, see:
  .\scripts\install-kernels-windows.ps1

Usage
  Open PowerShell in the repo root and run:
    .\scripts\setup-kernels-windows.ps1
#>

Write-Host "Jupyter kernels setup for wilsontew-data-analysis" -ForegroundColor Cyan
Write-Host "" 

Write-Host "1) Confirm current kernels:" -ForegroundColor Yellow
Write-Host "   jupyter kernelspec list" 
Write-Host "" 

Write-Host "2) Recommended: create the conda environment from environment.yml:" -ForegroundColor Yellow
Write-Host "   # Choose ONE" 
Write-Host "   mamba env create -f environment.yml" 
Write-Host "   conda env create -f environment.yml" 
Write-Host "" 

Write-Host "   If conda isn't on PATH (common on Windows), you can call it directly, e.g.:" -ForegroundColor DarkGray
Write-Host "   C:\Users\<you>\miniforge3\Scripts\conda.exe env create -f environment.yml" -ForegroundColor DarkGray
Write-Host "" 

Write-Host "3) Activate it and (re)register Python + R kernels (optional but helps VS Code find them):" -ForegroundColor Yellow
Write-Host "   conda activate wilsontew-jupyter-kernels" 
Write-Host "   python -m ipykernel install --user --name wilsontew-py --display-name \"Python (wilsontew)\"" 
Write-Host "   R -q -e \"IRkernel::installspec(user = TRUE, name = 'wilsontew-r', displayname = 'R (wilsontew)', overwrite = TRUE)\"" 
Write-Host "" 

Write-Host "   Why --user? It installs kernelspecs into %APPDATA%\\jupyter\\kernels, so they're not tied" -ForegroundColor DarkGray
Write-Host "   to some unrelated project environment (and VS Code can discover them reliably)." -ForegroundColor DarkGray
Write-Host "" 

Write-Host "4) Re-check kernels:" -ForegroundColor Yellow
Write-Host "   jupyter kernelspec list" 
Write-Host "" 

Write-Host "VBA note:" -ForegroundColor Yellow
Write-Host "  There is no standard Jupyter VBA kernel; see KERNELS.md for practical alternatives." 
