$ErrorActionPreference = "Stop"


# ================================================================
# CAMPO BURGER POS
# BUILD DEL CLIENTE WINDOWS
# ================================================================


# Carpeta donde vive este script:
# POS_Hamburgueseria\scripts
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Carpeta principal del proyecto:
# POS_Hamburgueseria
$ProjectDir = Split-Path -Parent $ScriptDir

Set-Location $ProjectDir


Write-Host ""
Write-Host "=== CAMPO BURGER POS - BUILD WINDOWS ===" -ForegroundColor Yellow
Write-Host ""


# ================================================================
# VALIDACIONES
# ================================================================

if (-not (Test-Path ".\main.py")) {
    throw "No se encontro main.py en la raiz del proyecto."
}

if (-not (Test-Path ".\CampoBurgerPOS.spec")) {
    throw "No se encontro CampoBurgerPOS.spec."
}

if (-not (Test-Path ".\campo_burger.ico")) {
    throw "No se encontro campo_burger.ico."
}


# ================================================================
# DEPENDENCIAS DE EMPAQUETADO
# ================================================================

Write-Host "Verificando herramientas de empaquetado..." -ForegroundColor Cyan

python -m pip install --upgrade pyinstaller pywin32


# ================================================================
# LIMPIAR COMPILACIONES ANTERIORES
# ================================================================

Write-Host ""
Write-Host "Limpiando compilaciones anteriores..." -ForegroundColor Cyan

if (Test-Path ".\build") {
    Remove-Item ".\build" -Recurse -Force
}

if (Test-Path ".\dist") {
    Remove-Item ".\dist" -Recurse -Force
}


# ================================================================
# GENERAR CLIENTE
# ================================================================

Write-Host ""
Write-Host "Creando CampoBurgerPOS.exe..." -ForegroundColor Cyan

python -m PyInstaller `
    --noconfirm `
    --clean `
    ".\CampoBurgerPOS.spec"


# ================================================================
# VERIFICAR RESULTADO
# ================================================================

$exe = Join-Path `
    $ProjectDir `
    "dist\CampoBurgerPOS\CampoBurgerPOS.exe"

if (-not (Test-Path $exe)) {
    throw "PyInstaller termino, pero CampoBurgerPOS.exe no fue encontrado."
}


# ================================================================
# VERIFICACION DE SEGURIDAD
# ================================================================

$envCliente = Join-Path `
    $ProjectDir `
    "dist\CampoBurgerPOS\.env"

if (Test-Path $envCliente) {

    throw @"
ERROR DE SEGURIDAD:

Se encontro un archivo .env dentro del cliente compilado.

El build fue detenido.
"@
}


# ================================================================
# RESULTADO
# ================================================================

Write-Host ""
Write-Host "BUILD COMPLETADO CORRECTAMENTE" -ForegroundColor Green
Write-Host ""

Write-Host "Ejecutable:"
Write-Host "  $exe"

Write-Host ""
Write-Host "Seguridad:"
Write-Host "  .env NO incluido en el cliente." -ForegroundColor Green

Write-Host ""
Write-Host "Siguiente paso:"
Write-Host "  .\scripts\crear_instalador.ps1"
Write-Host ""