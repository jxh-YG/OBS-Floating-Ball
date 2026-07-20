param([string]$Python = "py")

$appName = "OBS Floating Ball"
$icon = Join-Path $PSScriptRoot "assets\app.ico"

& $Python -3.11 (Join-Path $PSScriptRoot "tools\generate_icon.py")
if (-not (Test-Path $icon)) {
    throw "Icon not generated: $icon"
}

& $Python -3.11 -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name $appName `
    --icon $icon `
    --paths src `
    main.py
