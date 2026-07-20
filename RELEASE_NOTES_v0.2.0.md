# OBS Floating Ball v0.2.0

## Highlights
- Unified Apple-style UI for settings, dialogs, and floating bar
- Chinese-first dialogs (好 / 取消), no mixed system OK/Cancel
- Right-click: open recording folder + hide ball
- Configurable host/port, hotkeys, autostart, auto-rename, hide-while-recording
- Fix: rename dialog no longer requires double confirm (dedupe StopRecord + RecordStateChanged)
- Fix: connection uses saved host/port (OBS default 4455)
- Remove annotation feature
- Package icon + build.ps1; CI workflow for Windows pytest

## Install
1. Download `OBS-Floating-Ball.exe` (or build with `.\build.ps1`)
2. Enable OBS WebSocket (Tools → WebSocket Server Settings), port 4455
3. Run the app and save connection password in settings

## Notes
- Floating bar uses translucent glass and may appear in Display Capture; use hide-while-recording if needed
- Windows only
