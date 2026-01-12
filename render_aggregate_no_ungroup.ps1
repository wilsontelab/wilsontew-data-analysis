# Render aggregate_no_ungroup.Rmd using the installed Rscript.exe.
# This avoids needing an interactive R terminal or R on PATH.

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$inputRmd = Join-Path $projectRoot 'aggregate_no_ungroup.Rmd'

if (-not (Test-Path $inputRmd)) {
  throw "Cannot find: $inputRmd"
}

# Find the newest installed R under Program Files.
$rDirs = Get-ChildItem -Path 'C:\Program Files\R' -Directory -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match '^R-\d+' } |
  Sort-Object Name -Descending

if (-not $rDirs -or $rDirs.Count -eq 0) {
  throw 'R does not appear to be installed under C:\Program Files\R'
}

$rscript = Join-Path $rDirs[0].FullName 'bin\Rscript.exe'
if (-not (Test-Path $rscript)) {
  throw "Cannot find Rscript.exe at: $rscript"
}

# Use forward slashes for R on Windows.
$inputRmdR = ($inputRmd -replace '\\', '/')

# Ensure pandoc is available to rmarkdown at render start.
# Prefer Quarto's bundled pandoc if present.
$quartoTools = 'C:\Users\dunnmk\AppData\Local\Programs\Quarto\bin\tools'
if (Test-Path (Join-Path $quartoTools 'pandoc.exe')) {
  $env:RSTUDIO_PANDOC = $quartoTools
}

Write-Host "Using Rscript: $rscript"
Write-Host "Rendering: $inputRmd"

& $rscript -e "rmarkdown::render('$inputRmdR')"

Write-Host "Done. Output should be next to the .Rmd (e.g., aggregate_no_ungroup.html)."