# Inicia Vibra Deportiva en Windows. Se ejecuta desde la carpeta del proyecto con:
#   powershell -ExecutionPolicy Bypass -File .\iniciar.ps1
# Crea el entorno (.venv) si falta, instala dependencias solo la primera vez y abre la app en modo demo (SQLite).
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creando entorno virtual..."
    py -m venv .venv
}
$python = ".venv\Scripts\python.exe"

if (-not (Test-Path ".venv\.instalado")) {
    Write-Host "Instalando dependencias (puede tardar unos minutos)..."
    & $python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { Write-Host "Falló la instalación. Copiá el error y pedí ayuda."; exit 1 }
    New-Item -Path ".venv\.instalado" -ItemType File | Out-Null
}

if (-not (Test-Path ".env")) { $env:DB_ENGINE = "sqlite" }   # sin .env: modo demo

Write-Host "Abriendo la app en http://localhost:8501  (Ctrl+C para cerrar)"
& $python -m streamlit run app.py
