# Copies the firmware onto a connected Klever Klox (the CIRCUITPY drive) and
# installs the libraries it needs. Nothing to compile.
#
#   powershell -ExecutionPolicy Bypass -File tools\deploy.ps1
#   powershell -ExecutionPolicy Bypass -File tools\deploy.ps1 -Test test_tft
#
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.

param(
    [string]$Test = ""     # e.g. test_tft: installs tests\hardware\test_tft.py as code.py
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

$vol = Get-Volume | Where-Object { $_.FileSystemLabel -eq "CIRCUITPY" } | Select-Object -First 1
if (-not $vol) { throw "No CIRCUITPY drive found. Is CircuitPython installed and the board plugged in?" }
$drive = "$($vol.DriveLetter):\"
Write-Host "CIRCUITPY is $drive"

Copy-Item -Recurse -Force "$root\src\klever" $drive
if ($Test) {
    Copy-Item -Force "$root\tests\hardware\$Test.py" "$drive\code.py"
    Write-Host "Installed hardware test $Test as code.py"
} else {
    Copy-Item -Force "$root\src\code.py" "$drive\code.py"
    Write-Host "Installed firmware code.py"
}

if (Get-Command circup -ErrorAction SilentlyContinue) {
    circup --path $drive install -r "$root\requirements.txt"
} else {
    Write-Warning "circup not found. Run: pip install circup  - then deploy again to install the libraries."
}
