# Instalador de vd0 para Windows (PowerShell 5.1+ / PowerShell 7).
#   Usuario normal:  .\install.ps1                 -> %LOCALAPPDATA%\vd0 (PATH de usuario)
#   Administrador:   PowerShell como admin         -> %ProgramFiles%\vd0 (PATH del sistema)
#
# Desde GitHub (sin clonar):
#   irm https://raw.githubusercontent.com/TU_USUARIO/vd0/main/install.ps1 | iex

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/TU_USUARIO/vd0.git"

function Say($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }

# Origen: carpeta local si existe pyproject.toml, de lo contrario GitHub
$Source = "git+$RepoUrl"
if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot "pyproject.toml"))) {
    $Source = $PSScriptRoot
}

# Administrador o usuario normal
$IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
           ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($IsAdmin) {
    $InstallDir = Join-Path $env:ProgramFiles "vd0"
    $PathScope  = "Machine"
} else {
    $InstallDir = Join-Path $env:LOCALAPPDATA "vd0"
    $PathScope  = "User"
}

# Buscar Python 3.8+
$PyCmd = $null
foreach ($candidate in @(@("py", "-3"), @("python"), @("python3"))) {
    try {
        $exe  = $candidate[0]
        $rest = @()
        if ($candidate.Count -gt 1) { $rest = $candidate[1..($candidate.Count - 1)] }
        & $exe @rest -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { $PyCmd = $candidate; break }
    } catch { }
}
if (-not $PyCmd) {
    throw "Se requiere Python 3.8 o superior. Instalalo con: winget install Python.Python.3.12"
}
$PyExe  = $PyCmd[0]
$PyArgs = @()
if ($PyCmd.Count -gt 1) { $PyArgs = $PyCmd[1..($PyCmd.Count - 1)] }

# Entorno virtual propio
Say "Creando entorno en $InstallDir"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
& $PyExe @PyArgs -m venv (Join-Path $InstallDir "venv")
if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el entorno virtual." }

$VenvPy = Join-Path $InstallDir "venv\Scripts\python.exe"

Say "Instalando vd0 y dependencias"
& $VenvPy -m pip install --quiet --upgrade pip
& $VenvPy -m pip install --quiet --upgrade $Source
if ($LASTEXITCODE -ne 0) { throw "Fallo la instalacion de vd0." }

# Comando global: vd0.cmd (funciona en PowerShell y CMD)
$BinDir = Join-Path $InstallDir "bin"
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
$Shim = "@echo off`r`n`"%~dp0..\venv\Scripts\vd0.exe`" %*`r`n"
Set-Content -Path (Join-Path $BinDir "vd0.cmd") -Value $Shim -Encoding ASCII

# Agregar al PATH (persistente) y a la sesion actual
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", $PathScope)
if (-not $CurrentPath) { $CurrentPath = "" }
if (($CurrentPath -split ";") -notcontains $BinDir) {
    $NewPath = ($CurrentPath.TrimEnd(";") + ";" + $BinDir).TrimStart(";")
    [Environment]::SetEnvironmentVariable("Path", $NewPath, $PathScope)
    Say "Se agrego $BinDir al PATH ($PathScope)."
}
$env:Path = $env:Path.TrimEnd(";") + ";" + $BinDir

Say "Listo. Ejecuta:  vd0   (si no lo reconoce, abre una terminal nueva)"
