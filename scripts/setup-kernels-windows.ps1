<#
Purpose
  Helper notes for setting up a multi-language Jupyter environment on Windows.

This script is intentionally conservative:
  - It does NOT install anything automatically.
  - It prints what you should run (so you can choose conda vs mamba vs micromamba).

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

Write-Host "3) Activate it and (re)register Python + R kernels (optional but helps VS Code find them):" -ForegroundColor Yellow
Write-Host "   conda activate wilsontew-jupyter-kernels" 
Write-Host "   python -m ipykernel install --user --name wilsontew-py --display-name \"Python (wilsontew)\"" 
Write-Host "   R -q -e \"IRkernel::installspec(user = TRUE, name = 'wilsontew-r', displayname = 'R (wilsontew)')\"" 
Write-Host "" 

Write-Host "4) Re-check kernels:" -ForegroundColor Yellow
Write-Host "   jupyter kernelspec list" 
Write-Host "" 

Write-Host "VBA note:" -ForegroundColor Yellow
Write-Host "  There is no standard Jupyter VBA kernel; see KERNELS.md for practical alternatives." 
