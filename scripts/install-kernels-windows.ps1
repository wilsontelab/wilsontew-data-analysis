<#
Purpose
  Create a dedicated conda env for this repo and register Jupyter kernelspecs
  into the standard USER kernels directory (so VS Code can find them even when
  other projects/environments come and go).

Why this exists
  It's easy to accidentally register kernels that point into some unrelated
  conda env (e.g., another repo). That makes notebooks fragile: kernels "work"
  until that other env changes.

What this script does
  1) Locates conda/mamba/micromamba (or common Miniforge install locations)
  2) Creates/updates the env from environment.yml (name: wilsontew-jupyter-kernels)
  3) Registers kernelspecs into %APPDATA%\jupyter\kernels via --user
     - Python: wilsontew-py
     - R:      wilsontew-r

Usage
  From repo root (PowerShell):
    .\scripts\install-kernels-windows.ps1

Notes
  - You do NOT need to "activate" the env to register kernels; we use `conda run`.
  - If you open the repo via a GitHub virtual workspace (vscode-vfs://...),
    kernel execution may still fail. Clone locally and open the local folder.
#>

[CmdletBinding()]
param(
  # Recreate the environment even if it already exists.
  [switch]$ForceRecreate,

  # Skip env creation and only (re)register kernels.
  [switch]$RegisterOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Section([string]$Text) {
  Write-Host "" 
  Write-Host $Text -ForegroundColor Cyan
}

function Find-CondaExe {
  # Returns an object: @{ Path = <string>; Kind = 'conda'|'mamba'|'micromamba' }
  $candidates = @()

  # Prefer conda/mamba because their CLI shape matches best.
  foreach ($name in @('conda.exe', 'mamba.exe', 'micromamba.exe')) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) {
      $candidates += [PSCustomObject]@{
        Path = $cmd.Source
        Kind = ($name -replace '\.exe$','')
      }
    }
  }

  # Common Miniforge/Miniconda locations
  $home = $env:USERPROFILE
  $candidates += @(
    [PSCustomObject]@{ Path = (Join-Path $home 'miniforge3\Scripts\conda.exe'); Kind = 'conda' },
    [PSCustomObject]@{ Path = (Join-Path $home 'miniconda3\Scripts\conda.exe'); Kind = 'conda' },
    [PSCustomObject]@{ Path = (Join-Path $home 'anaconda3\Scripts\conda.exe'); Kind = 'conda' },
    [PSCustomObject]@{ Path = 'C:\ProgramData\miniforge3\Scripts\conda.exe'; Kind = 'conda' },
    [PSCustomObject]@{ Path = 'C:\ProgramData\Miniconda3\Scripts\conda.exe'; Kind = 'conda' },
    [PSCustomObject]@{ Path = 'C:\ProgramData\Anaconda3\Scripts\conda.exe'; Kind = 'conda' }
  )

  foreach ($c in $candidates | Group-Object Path | ForEach-Object { $_.Group[0] }) {
    if ($c.Path -and (Test-Path $c.Path)) { return $c }
  }

  return $null
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$envFile = Join-Path $repoRoot 'environment.yml'
$envName = 'wilsontew-jupyter-kernels'

Write-Section "wilsontew-data-analysis: install/register Jupyter kernels (Windows)"

if (!(Test-Path $envFile)) {
  throw "environment.yml not found at: $envFile"
}

$frontend = Find-CondaExe
if (-not $frontend) {
  throw @(
    "Could not find conda/mamba/micromamba.",
    "Install Miniforge (recommended) or Anaconda, then re-run this script.",
    "Tip: if conda exists but isn't on PATH, this script expects it at common locations like:",
    "  $env:USERPROFILE\miniforge3\Scripts\conda.exe"
  ) -join "`n"
}

Write-Host "Using:" -NoNewline
Write-Host " $($frontend.Path)" -ForegroundColor Yellow
Write-Host "Frontend:" -NoNewline
Write-Host " $($frontend.Kind)" -ForegroundColor Yellow

function Invoke-EnvList {
  switch ($frontend.Kind) {
    'micromamba' { & $frontend.Path env list }
    default { & $frontend.Path env list }
  }
}

function Invoke-EnvRemove([string]$Name) {
  switch ($frontend.Kind) {
    'micromamba' { & $frontend.Path env remove -n $Name -y | Out-Null }
    default { & $frontend.Path env remove -n $Name -y | Out-Null }
  }
}

function Invoke-EnvCreate([string]$EnvFile) {
  # IMPORTANT: We intentionally do not use a prefix (-p). This uses the default
  # conda envs location on the machine.
  switch ($frontend.Kind) {
    'micromamba' {
      # micromamba uses `create`, not `env create`
      & $frontend.Path create -n $envName -f $EnvFile -y
    }
    default {
      & $frontend.Path env create -f $EnvFile -y
    }
  }
}

function Invoke-EnvUpdate([string]$Name, [string]$EnvFile) {
  switch ($frontend.Kind) {
    'micromamba' { & $frontend.Path update -n $Name -f $EnvFile -y }
    default { & $frontend.Path env update -n $Name -f $EnvFile -y }
  }
}

function Invoke-Run([string]$Name, [string[]]$Args) {
  & $frontend.Path run -n $Name @Args
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function Find-PowerShellExe {
  # VS Code's Jupyter extension spawns argv[0] directly (no shell). In some VS Code
  # contexts, PATH may not include System32, causing `powershell.exe` ENOENT.
  # Return an absolute path that should work on all supported Windows installs.
  $candidates = @()

  # Prefer whatever is on PATH (gives us an absolute .Source)
  $cmd = Get-Command 'powershell.exe' -ErrorAction SilentlyContinue
  if ($cmd -and $cmd.Source) {
    $candidates += $cmd.Source
  }

  # Standard Windows PowerShell 5.1 location
  $candidates += 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'

  foreach ($p in $candidates | Select-Object -Unique) {
    if ($p -and (Test-Path $p)) { return $p }
  }

  # Last resort: let CreateProcess search PATH
  return 'powershell.exe'
}

if (-not $RegisterOnly) {
  Write-Section "1) Create/update conda environment"

  # Decide whether env exists
  $envExists = $false
  try {
    $envList = Invoke-EnvList
    if ($envList -match "\s$envName\s") { $envExists = $true }
  } catch {
    # We'll attempt create anyway
  }

  if ($ForceRecreate -and $envExists) {
    Write-Host "Removing existing env '$envName'..." -ForegroundColor Yellow
    Invoke-EnvRemove -Name $envName
    $envExists = $false
  }

  if (-not $envExists) {
    Write-Host "Creating env '$envName' from environment.yml..." -ForegroundColor Yellow
    Push-Location $repoRoot
    try {
      Invoke-EnvCreate -EnvFile $envFile
    } finally {
      Pop-Location
    }
  } else {
    Write-Host "Env '$envName' already exists; updating from environment.yml..." -ForegroundColor Yellow
    Push-Location $repoRoot
    try {
      Invoke-EnvUpdate -Name $envName -EnvFile $envFile
    } finally {
      Pop-Location
    }
  }
}

Write-Section "2) Register USER kernelspecs (recommended)"
Write-Host "This writes kernels into: $env:APPDATA\jupyter\kernels" -ForegroundColor DarkGray
Write-Host "Environment location: default conda envs directory (no -p prefix used)" -ForegroundColor DarkGray

# Python kernel
Write-Host "Registering Python kernel (wilsontew-py)..." -ForegroundColor Yellow
Invoke-Run -Name $envName -Args @('python','-m','ipykernel','install','--user','--name','wilsontew-py','--display-name','Python (wilsontew)','--replace')

# R kernel
Write-Host "Registering R kernel (wilsontew-r)..." -ForegroundColor Yellow
Invoke-Run -Name $envName -Args @('R','-q','-e',"IRkernel::installspec(user = TRUE, name = 'wilsontew-r', displayname = 'R (wilsontew)', overwrite = TRUE)")

# Harden the wilsontew-r kernelspec so it does NOT depend on conda.exe at runtime.
# Why: VS Code's Jupyter extension launches kernels by spawning argv[0]. If that
# conda.exe path is stale/missing, you get ENOENT and the kernel dies.
# We instead use a small PowerShell wrapper that launches the env's R.exe directly.
try {
  Write-Host "Hardening R kernel launcher (avoid conda.exe at runtime)..." -ForegroundColor Yellow

  $psExe = Find-PowerShellExe

  $envPrefix = (Invoke-Run -Name $envName -Args @('python','-c','import sys; print(sys.prefix)') | Select-Object -Last 1).Trim()
  if (-not $envPrefix) { throw "Could not determine env prefix for '$envName'." }

  $kernelsDir = Join-Path $env:APPDATA 'jupyter\kernels\wilsontew-r'
  $kernelJson = Join-Path $kernelsDir 'kernel.json'
  if (!(Test-Path $kernelsDir)) { throw "Expected kernelspec directory not found: $kernelsDir" }

  $launcher = Join-Path $kernelsDir 'launch-r-kernel.ps1'

  $launcherContent = @(
    '# Auto-generated by scripts/install-kernels-windows.ps1',
    '# Launches IRkernel using the repo conda env WITHOUT calling conda.exe at runtime.',
    '',
    'param(',
    '  [Parameter(Mandatory = $true, Position = 0)]',
    '  [string]$ConnectionFile',
    ')',
    '',
    ('$EnvPrefix = ' + ("'" + $envPrefix.Replace("'","''") + "'")),
    '$RExe = Join-Path $EnvPrefix "Lib\\R\\bin\\x64\\R.exe"',
    '',
    'if (!(Test-Path $RExe)) {',
    '  throw "R.exe not found at expected path: $RExe"',
    '}',
    '',
    '# Ensure conda-provided DLLs can be located (important on Windows).',
    '$extra = @(',
    '  (Join-Path $EnvPrefix "Library\\bin"),',
    '  (Join-Path $EnvPrefix "Library\\usr\\bin"),',
    '  (Join-Path $EnvPrefix "Scripts"),',
    '  $EnvPrefix',
    ') | Where-Object { $_ -and (Test-Path $_) }',
    '',
    '$env:PATH = (($extra -join ";") + ";" + $env:PATH)',
    '',
    '& $RExe --slave -e "IRkernel::main()" --args $ConnectionFile'
  ) -join "`r`n"

  Write-Utf8NoBom -Path $launcher -Content $launcherContent

  $kernelSpec = [ordered]@{
    argv = @(
      $psExe,
      '-NoProfile',
      '-ExecutionPolicy',
      'Bypass',
      '-File',
      $launcher,
      '{connection_file}'
    )
    display_name = 'R (wilsontew)'
    language = 'R'
  }

  $kernelSpecJson = ($kernelSpec | ConvertTo-Json -Depth 10)
  Write-Utf8NoBom -Path $kernelJson -Content $kernelSpecJson
} catch {
  Write-Host "WARNING: Failed to harden wilsontew-r kernelspec. Kernel may still work, but might depend on conda.exe at runtime." -ForegroundColor Yellow
  Write-Host $_.Exception.Message -ForegroundColor DarkYellow
}

Write-Section "3) Verify"
Write-Host "Run: jupyter kernelspec list" -ForegroundColor Yellow
Write-Host "In VS Code, pick kernel: R (wilsontew) for the R notebooks." -ForegroundColor Yellow
