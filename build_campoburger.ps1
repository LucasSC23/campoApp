$ErrorActionPreference = "Stop"


# ================================================================
# CAMPO BURGER POS
# BUILD DEL CLIENTE WINDOWS
# ================================================================

Write-Host ""
Write-Host "=== CAMPO BURGER POS - BUILD WINDOWS ===" -ForegroundColor Yellow
Write-Host ""


# ================================================================
# VERIFICAR QUE ESTAMOS EN LA RAIZ DEL PROYECTO
# ================================================================

if (-not (Test-Path ".\main.py")) {
    throw "Ejecuta este script desde la carpeta principal del proyecto."
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

Write-Host "Verificando PyInstaller..." -ForegroundColor Cyan

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
# GENERAR EJECUTABLE
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

$exe = ".\dist\CampoBurgerPOS\CampoBurgerPOS.exe"

if (-not (Test-Path $exe)) {
    throw "PyInstaller termino, pero no se encontro CampoBurgerPOS.exe."
}


# ================================================================
# IMPORTANTE
# ================================================================
#
# NO copiamos .env al cliente.
#
# El cliente POS no debe contener:
#
# DB_HOST
# DB_USER
# DB_PASSWORD
#
# Las credenciales pertenecen exclusivamente al backend.
# ================================================================


Write-Host ""
Write-Host "BUILD COMPLETADO CORRECTAMENTE" -ForegroundColor Green
Write-Host ""
Write-Host "Ejecutable:"
Write-Host "  $exe"
Write-Host ""
Write-Host "Siguiente paso:"
Write-Host "  Ejecutar crear_instalador.ps1"
Write-Host ""