param(
  [switch]$SkipInstall,
  [switch]$NoZip
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path .\models\mobile_sam_encoder.onnx) -or -not (Test-Path .\models\mobile_sam_decoder.onnx)) {
  throw "The MobileSAM ONNX encoder and decoder are required for the Windows release."
}

if (-not $SkipInstall) {
  & .\setup.ps1 -Build
  if ($LASTEXITCODE -ne 0) { throw "Setup failed with exit code $LASTEXITCODE." }
}

$venvPython = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
  throw "Virtual environment not found. Run .\setup.ps1 -Build first."
}

& $venvPython -m PyInstaller --clean --noconfirm smart-labelimg.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE." }

$exePath = "dist\Smart LabelImg\Smart LabelImg.exe"
if (-not (Test-Path $exePath)) {
  throw "Build finished but $exePath was not created."
}

Write-Host "Build complete: $exePath"

if (-not $NoZip) {
  New-Item -ItemType Directory -Force -Path release | Out-Null
  $arch = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "arm64" } else { "x64" }
  $zipPath = "release\Smart-LabelImg-DirectML-Windows-$arch.zip"
  $hashPath = "release\Smart-LabelImg-DirectML-Windows-$arch.sha256"
  if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
  }
  Compress-Archive -Path "dist\Smart LabelImg" -DestinationPath $zipPath -Force
  $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $zipPath).Hash.ToLowerInvariant()
  Set-Content -LiteralPath $hashPath -Value "$hash  $(Split-Path $zipPath -Leaf)" -Encoding ascii
  Write-Host "Release package: $zipPath"
  Write-Host "SHA-256: $hashPath"
}
