$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== CAMPO BURGER POS - BUILD WINDOWS ===" -ForegroundColor Yellow
Write-Host ""

if (-not (Test-Path ".\main.py")) {
    throw "Ejecuta este script desde la carpeta principal del proyecto."
}

if (-not (Test-Path ".\campo_burger.ico")) {
    throw "Falta campo_burger.ico en la carpeta del proyecto."
}

Write-Host "Instalando/actualizando dependencias de empaquetado..." -ForegroundColor Cyan
python -m pip install --upgrade pyinstaller pywin32

Write-Host "Limpiando compilaciones anteriores..." -ForegroundColor Cyan
if (Test-Path ".\build") { Remove-Item ".\build" -Recurse -Force }
if (Test-Path ".\dist") { Remove-Item ".\dist" -Recurse -Force }

Write-Host "Creando CampoBurgerPOS.exe..." -ForegroundColor Cyan

pyinstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name "CampoBurgerPOS" `
    --icon ".\campo_burger.ico" `
    --add-data ".\campo_burger.ico;." `
    --hidden-import "win32print" `
    --hidden-import "pywintypes" `
    ".\main.py"

if (Test-Path ".\.env") {
    Copy-Item ".\.env" ".\dist\CampoBurgerPOS\.env" -Force
    Write-Host ".env copiado a la distribución." -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "BUILD COMPLETADO" -ForegroundColor Green
Write-Host "Ejecutable:"
Write-Host "  .\dist\CampoBurgerPOS\CampoBurgerPOS.exe"
Write-Host ""
Write-Host "Siguiente paso: compilar CampoBurgerPOS.iss con Inno Setup."
