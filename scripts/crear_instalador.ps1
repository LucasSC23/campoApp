$ErrorActionPreference = "Stop"


# ================================================================
# CAMPO BURGER POS
# CREACION DEL INSTALADOR WINDOWS
# ================================================================


$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

Set-Location $ProjectDir


Write-Host ""
Write-Host "=== CAMPO BURGER POS - CREAR INSTALADOR ===" -ForegroundColor Yellow
Write-Host ""


# ================================================================
# ARCHIVOS NECESARIOS
# ================================================================

$iss = Join-Path `
    $ProjectDir `
    "installer\CampoBurgerPOS.iss"

$exe = Join-Path `
    $ProjectDir `
    "dist\CampoBurgerPOS\CampoBurgerPOS.exe"

$ico = Join-Path `
    $ProjectDir `
    "campo_burger.ico"


# ================================================================
# VALIDACIONES
# ================================================================

if (-not (Test-Path $iss)) {
    throw "No se encontro installer\CampoBurgerPOS.iss."
}

if (-not (Test-Path $exe)) {

    throw @"
No se encontro:

dist\CampoBurgerPOS\CampoBurgerPOS.exe

Ejecuta primero:

.\scripts\build_campoburger.ps1
"@
}

if (-not (Test-Path $ico)) {
    throw "No se encontro campo_burger.ico."
}


# ================================================================
# SEGURIDAD
# ================================================================

$envCliente = Join-Path `
    $ProjectDir `
    "dist\CampoBurgerPOS\.env"

if (Test-Path $envCliente) {

    throw @"
ERROR DE SEGURIDAD:

Existe un archivo .env dentro del cliente.

El instalador NO sera generado.
"@
}


# ================================================================
# BUSCAR INNO SETUP
# ================================================================

$candidatos = @(

    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",

    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",

    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)


$iscc = $null


foreach ($ruta in $candidatos) {

    if (
        $ruta -and
        (Test-Path $ruta)
    ) {

        $iscc = $ruta
        break
    }
}


if (-not $iscc) {

    $cmd = Get-Command `
        ISCC.exe `
        -ErrorAction SilentlyContinue

    if ($cmd) {
        $iscc = $cmd.Source
    }
}


if (-not $iscc) {

    Write-Host ""
    Write-Host "Inno Setup no esta instalado." -ForegroundColor Red
    Write-Host ""

    Write-Host "Instalalo con:" -ForegroundColor Cyan
    Write-Host ""

    Write-Host "winget install JRSoftware.InnoSetup"

    Write-Host ""

    exit 1
}


# ================================================================
# COMPILAR INSTALADOR
# ================================================================

Write-Host "Inno Setup encontrado:" -ForegroundColor Green
Write-Host "  $iscc"
Write-Host ""

Write-Host "Compilando instalador..." -ForegroundColor Cyan

& $iscc $iss


if ($LASTEXITCODE -ne 0) {

    throw "Inno Setup devolvio codigo de error $LASTEXITCODE."
}


# ================================================================
# VERIFICAR RESULTADO
# ================================================================

$setup = Join-Path `
    $ProjectDir `
    "installer\CampoBurgerPOS_Setup.exe"


if (-not (Test-Path $setup)) {

    throw "No se encontro installer\CampoBurgerPOS_Setup.exe."
}


# ================================================================
# RESULTADO
# ================================================================

Write-Host ""
Write-Host "INSTALADOR CREADO CORRECTAMENTE" -ForegroundColor Green
Write-Host ""

Write-Host "Archivo:"
Write-Host "  $setup"

Write-Host ""