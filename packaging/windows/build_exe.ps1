# =============================================================================
# AutoDoc — Build do instalador Windows (.exe)
#
# Roda no Windows (local ou CI windows-latest). Gera:
#   dist\autodoc-ctk_<versao>_win64_setup.exe
#
# Requisitos: Python com requirements.txt, PyInstaller, Pillow e Inno Setup 6.
# O Tesseract é baixado via Chocolatey e embutido no pacote (portátil).
# =============================================================================
param(
    [string]$Version = "",
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $Root

if (-not $Version) {
    $Version = (& $Python -c "import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])" | Select-Object -Last 1).Trim()
}

Write-Host "==> AutoDoc $Version (win64)"

Write-Host "==> [1/6] Preparando icone e fonte"
& $Python -c "from PIL import Image; Image.open('icon.png').save('icon.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"

New-Item -ItemType Directory -Force -Path "assets\fonts" | Out-Null
if (-not (Test-Path "assets\fonts\Inter.ttf")) {
    $fontUrl = "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz,wght%5D.ttf"
    Invoke-WebRequest -Uri $fontUrl -OutFile "assets\fonts\Inter.ttf" -UseBasicParsing
}

Write-Host "==> [2/6] Empacotando aplicacao com PyInstaller"
Remove-Item -Recurse -Force "build\pyinstaller-win" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "dist\AutoDoc" -ErrorAction SilentlyContinue

& $Python -m PyInstaller `
    --noconfirm --clean --onedir --windowed `
    --name "AutoDoc" `
    --icon "icon.ico" `
    --paths "src" `
    --add-data "assets;assets" `
    --add-data "icon.png;." `
    --collect-all customtkinter `
    --collect-all ttkbootstrap `
    --distpath "dist" `
    --workpath "build\pyinstaller-win" `
    --specpath "build" `
    "run_ctk.py"

$Dist = Join-Path $Root "dist\AutoDoc"
$Internal = Join-Path $Dist "_internal"

Write-Host "==> [3/6] Embutindo Tesseract + idioma portugues"
$TessSrc = Join-Path ${env:ProgramFiles} "Tesseract-OCR"
if (-not (Test-Path $TessSrc)) {
    $TessSrc = Join-Path ${env:ProgramFiles(x86)} "Tesseract-OCR"
}
if (-not (Test-Path $TessSrc)) {
    throw "Tesseract-OCR nao encontrado. Instale com: choco install tesseract -y"
}

$TessDst = Join-Path $Internal "tesseract"
New-Item -ItemType Directory -Force -Path (Join-Path $TessDst "tessdata") | Out-Null
Copy-Item -Path (Join-Path $TessSrc "*") -Destination $TessDst -Recurse -Force

Get-ChildItem -Path $TessDst -Filter "*.traineddata" -File | Copy-Item -Destination (Join-Path $TessDst "tessdata") -Force -ErrorAction SilentlyContinue
$PorUrl = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/por.traineddata"
Invoke-WebRequest -Uri $PorUrl -OutFile (Join-Path $TessDst "tessdata\por.traineddata") -UseBasicParsing

Get-ChildItem -Path $Internal -Filter "vcruntime*.dll" -File -ErrorAction SilentlyContinue |
    Copy-Item -Destination $TessDst -Force

Write-Host "==> [4/6] Localizando Inno Setup"
$Iscc = Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"
if (-not (Test-Path $Iscc)) {
    $Iscc = Join-Path ${env:ProgramFiles} "Inno Setup 6\ISCC.exe"
}
if (-not (Test-Path $Iscc)) {
    throw "Inno Setup 6 nao encontrado (ISCC.exe)."
}

Write-Host "==> [5/6] Compilando instalador"
& $Iscc "/DAppVersion=$Version" "packaging\windows\autodoc.iss"

Write-Host "==> [6/6] Resultado"
Get-ChildItem -Path "dist" -Filter "*win64_setup.exe" | ForEach-Object {
    Write-Host ("Pacote gerado: " + $_.FullName)
    Write-Host ("Tamanho: {0:N1} MB" -f ($_.Length / 1MB))
}
