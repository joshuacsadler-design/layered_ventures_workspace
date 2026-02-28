# run_build.ps1
# Deterministic build runner for Infusist Experimental Art Suite (D) Spec v1.0

$ErrorActionPreference = "Stop"

# Config
$OutDir = "out_suite"
$WidthPx = 3000
$HeightPx = 2000

Write-Host "== Infusist ExpArtSuiteD Build =="

# Ensure Python
python --version

# Create venv
if (!(Test-Path ".\.venv")) {
  python -m venv .venv
}

# Activate venv
.\.venv\Scripts\Activate.ps1

# Install pinned deps (deterministic-ish)
python -m pip install --upgrade pip
python -m pip install pillow==10.4.0 numpy==2.0.2 openpyxl==3.1.5

# Run build
python .\build_suite.py --out_dir $OutDir --w $WidthPx --h $HeightPx --zip

Write-Host "`n== Outputs =="
Get-ChildItem -Recurse $OutDir | Select-Object FullName,Length,LastWriteTime

Write-Host "`n== ZIP + SHA256 =="
Get-ChildItem ".\Infusist_ExpArtSuiteD_v1.0_EXPORT.zip",".\Infusist_ExpArtSuiteD_v1.0_EXPORT.zip.sha256" | Select-Object FullName,Length,LastWriteTime
Get-FileHash ".\Infusist_ExpArtSuiteD_v1.0_EXPORT.zip" -Algorithm SHA256 | Format-List