#Requires -Version 5.1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "==> Stage files"
git add .gitignore README.md build.ps1 pyproject.toml main.py requirements-dev.txt
git add .github/workflows/ci.yml assets/app.ico tools/generate_icon.py
git add src/obs_floating_controller tests
git add -f src/obs_floating_controller/__init__.py
# do not commit build logs
git status --short

Write-Host "==> Commit v0.2.0"
$msg = @"
release: v0.2.0 floating ball polish and reliability fixes

Ship the v0.2.0 controller with unified Chinese UI, settings/hotkeys
improvements, rename dialog dedupe, and packaging/CI updates. Drop the
unused annotation path and keep Windows + local OBS WebSocket focus.
"@
git commit -m $msg

Write-Host "==> Ensure on main lineage and push"
# Prefer updating origin/main from current HEAD
git push -u origin HEAD:main

Write-Host "==> Tag and push"
git tag -a v0.2.0 -m "OBS Floating Ball v0.2.0"
git push origin v0.2.0

$exe = Join-Path $PSScriptRoot "dist\OBS Floating Ball.exe"
if (Test-Path $exe) {
    Write-Host "==> Create GitHub release with exe"
    gh release create v0.2.0 `
        --title "v0.2.0" `
        --notes-file "RELEASE_NOTES_v0.2.0.md" `
        "$exe#OBS-Floating-Ball.exe"
} else {
    Write-Host "==> Create GitHub release (no local exe found)"
    gh release create v0.2.0 --title "v0.2.0" --notes-file "RELEASE_NOTES_v0.2.0.md"
}

Write-Host "Done."
