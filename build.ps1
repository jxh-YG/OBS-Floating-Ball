param([string]$Python = "py")

$appName = "OBS Floating Ball"

& $Python -3.11 -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name $appName `
    --paths src `
    main.py
