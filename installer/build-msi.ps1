Param(
    [string]$ProjectDir = "${PSScriptRoot}\..",
    [string]$Output = "${PSScriptRoot}\..\dist"
)

Set-StrictMode -Version Latest
Write-Host "Building MSI for project: $ProjectDir"

if (-not (Test-Path $Output)) { New-Item -ItemType Directory -Path $Output | Out-Null }

# Ensure WiX Toolset is available (expectation: running on Windows runner)
if (-not (Get-Command candle.exe -ErrorAction SilentlyContinue)) {
    Write-Host "WiX not found. Installing via Chocolatey (requires admin)."
    choco install wixtoolset -y
}

$wxs = Join-Path $ProjectDir "installer\installer.wxs"
if (-not (Test-Path $wxs)) { throw "installer.wxs not found: $wxs" }

Push-Location $ProjectDir

Write-Host "Compiling .wxs"
Start-Process -FilePath "candle.exe" -ArgumentList ("-dProjectDir=$ProjectDir","-out","installer.wixobj","$wxs") -NoNewWindow -Wait

Write-Host "Linking MSI"
Start-Process -FilePath "light.exe" -ArgumentList ("-out", (Join-Path $Output "Scratchattach.msi"), "installer.wixobj") -NoNewWindow -Wait

Write-Host "MSI written to: $Output\Scratchattach.msi"
Pop-Location
