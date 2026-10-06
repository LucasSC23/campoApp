$ErrorActionPreference = "Stop"

# ================================================================
# CAMPO BURGER POS
# BUILD DEL CLIENTE WINDOWS
# ================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
Set-Location $ProjectDir

Write-Host ""
Write-Host "=== CAMPO BURGER POS - BUILD WINDOWS ===" -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path ".\client\main.py")) {
    throw "No se encontro client\main.py."
}

if (-not (Test-Path ".\CampoBurgerPOS.spec")) {
    throw "No se encontro CampoBurgerPOS.spec."
}

if (-not (Test-Path ".\campo_burger.ico")) {
    throw "No se encontro campo_burger.ico."
}

if (-not (Test-Path ".\requirements-dev.txt")) {
    throw "No se encontro requirements-dev.txt."
}

Write-Host "Verificando dependencias fijadas..." -ForegroundColor Cyan
python -m pip install -r ".\requirements-dev.txt"

if ($LASTEXITCODE -ne 0) {
    throw "No se pudieron instalar/verificar las dependencias de build."
}

Write-Host ""
Write-Host "Limpiando compilaciones anteriores..." -ForegroundColor Cyan

if (Test-Path ".\build") {
    Remove-Item ".\build" -Recurse -Force
}

if (Test-Path ".\dist") {
    Remove-Item ".\dist" -Recurse -Force
}

Write-Host ""
Write-Host "Creando CampoBurgerPOS.exe..." -ForegroundColor Cyan

python -m PyInstaller --noconfirm --clean ".\CampoBurgerPOS.spec"

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller devolvio codigo de error $LASTEXITCODE."
}

$distDir = Join-Path $ProjectDir "dist\CampoBurgerPOS"
$exe = Join-Path $distDir "CampoBurgerPOS.exe"

if (-not (Test-Path $exe)) {
    throw "PyInstaller termino, pero CampoBurgerPOS.exe no fue encontrado."
}

$archivosEnv = Get-ChildItem -Path $distDir -Recurse -Force -File |
    Where-Object { $_.Name -eq ".env" -or $_.Name -like ".env.*" }

if ($archivosEnv) {
    $rutas = ($archivosEnv | ForEach-Object { $_.FullName }) -join [Environment]::NewLine
    throw @"
ERROR DE SEGURIDAD:

Se encontraron archivos .env dentro del cliente compilado:

$rutas

El build fue detenido.
"@
}

$servidorEmpaquetado = Join-Path $distDir "server"
if (Test-Path $servidorEmpaquetado) {
    throw "ERROR DE SEGURIDAD: se encontro la carpeta server dentro del cliente compilado."
}

Write-Host ""
Write-Host "BUILD COMPLETADO CORRECTAMENTE" -ForegroundColor Green
Write-Host ""
Write-Host "Ejecutable:"
Write-Host "  $exe"
Write-Host ""
Write-Host "Seguridad:"
Write-Host "  .env NO incluido en el cliente." -ForegroundColor Green
Write-Host "  server/ NO incluido como carpeta distribuida." -ForegroundColor Green
Write-Host ""
Write-Host "Siguiente paso:"
Write-Host "  .\scripts\crear_instalador.ps1"
Write-Host ""
