$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

Write-Host ""
Write-Host "=== CAMPO BURGER POS - CREAR INSTALADOR ===" -ForegroundColor Yellow
Write-Host ""

$iss = Join-Path $ProjectDir "CampoBurgerPOS.iss"
$exe = Join-Path $ProjectDir "dist\CampoBurgerPOS\CampoBurgerPOS.exe"
$ico = Join-Path $ProjectDir "campo_burger.ico"

if (-not (Test-Path $iss)) {
    throw "No se encontro CampoBurgerPOS.iss en la carpeta del proyecto."
}

if (-not (Test-Path $exe)) {
    throw "No se encontro dist\CampoBurgerPOS\CampoBurgerPOS.exe. Ejecuta primero build_campoburger.ps1."
}

if (-not (Test-Path $ico)) {
    throw "No se encontro campo_burger.ico en la carpeta del proyecto."
}

$candidatos = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$iscc = $null

foreach ($ruta in $candidatos) {
    if ($ruta -and (Test-Path $ruta)) {
        $iscc = $ruta
        break
    }
}

if (-not $iscc) {
    $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        $iscc = $cmd.Source
    }
}

if (-not $iscc) {
    Write-Host "Inno Setup no esta instalado o no se encontro." -ForegroundColor Red
    Write-Host ""
    Write-Host "Instalalo con:" -ForegroundColor Cyan
    Write-Host "  winget install JRSoftware.InnoSetup"
    Write-Host ""
    Write-Host "Luego vuelve a ejecutar este script."
    exit 1
}

Write-Host "Inno Setup encontrado:" -ForegroundColor Green
Write-Host "  $iscc"
Write-Host ""
Write-Host "Compilando instalador..." -ForegroundColor Cyan

& $iscc $iss

if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup devolvio codigo de error $LASTEXITCODE."
}

$setup = Join-Path $ProjectDir "installer\CampoBurgerPOS_Setup.exe"

if (-not (Test-Path $setup)) {
    throw "La compilacion termino, pero no se encontro installer\CampoBurgerPOS_Setup.exe."
}

Write-Host ""
Write-Host "INSTALADOR CREADO CORRECTAMENTE" -ForegroundColor Green
Write-Host ""
Write-Host "Archivo:"
Write-Host "  $setup"
Write-Host ""
Write-Host "Siguiente paso:"
Write-Host "  1. Ejecutar CampoBurgerPOS_Setup.exe"
Write-Host "  2. Instalar Campo Burger POS"
Write-Host "  3. Abrirlo desde el acceso directo del escritorio"
Write-Host ""
