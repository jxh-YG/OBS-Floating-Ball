"""Small runtime translation catalog for the two supported interface languages."""

from __future__ import annotations


CHINESE = "zh_CN"
ENGLISH = "en_US"
SUPPORTED_LANGUAGES = (CHINESE, ENGLISH)

_TEXT = {
    "app_name": {CHINESE: "OBS Floating Ball", ENGLISH: "OBS Floating Ball"},
    "already_running": {CHINESE: "程序已在运行", ENGLISH: "Already running"},
    "already_running_detail": {CHINESE: "OBS Floating Ball 已在运行，请勿重复启动。", ENGLISH: "OBS Floating Ball is already running."},
    "not_connected": {CHINESE: "未连接 OBS", ENGLISH: "OBS not connected"},
    "connecting": {CHINESE: "正在连接 OBS…", ENGLISH: "Connecting to OBS…"},
    "connected": {CHINESE: "已连接 OBS", ENGLISH: "Connected to OBS"},
    "connection_refused": {CHINESE: "无法连接 OBS（请确认 OBS 已运行且 WebSocket 服务已启用）", ENGLISH: "Cannot connect to OBS. Check that OBS and its WebSocket server are running."},
    "connection_error": {CHINESE: "OBS 连接错误：{error}", ENGLISH: "OBS connection error: {error}"},
    "connection_lost": {CHINESE: "OBS 连接已断开", ENGLISH: "OBS connection was lost"},
    "auth_failed": {CHINESE: "OBS 密码错误或认证被拒绝", ENGLISH: "OBS password is incorrect or authentication was rejected"},
    "invalid_payload": {CHINESE: "OBS 返回了无法识别的数据", ENGLISH: "OBS returned unrecognized data"},
    "retry": {CHINESE: "{message}，将在 {seconds} 秒后重试", ENGLISH: "{message}; retrying in {seconds} seconds"},
    "request_failed": {CHINESE: "{request}失败：{comment}（代码 {code}）", ENGLISH: "{request} failed: {comment} (code {code})"},
    "operation_unavailable": {CHINESE: "OBS 未连接，无法执行操作", ENGLISH: "OBS is not connected; the action is unavailable"},
    "unknown_error": {CHINESE: "未知错误", ENGLISH: "Unknown error"},
    "timer_disconnected": {CHINESE: "未\n连接", ENGLISH: "Not\nconnected"},
    "timer_connecting": {CHINESE: "连接\n中", ENGLISH: "Connecting"},
    "timer_offline": {CHINESE: "OBS\n离线", ENGLISH: "OBS\noffline"},
    "timer_auth_failed": {CHINESE: "密码\n错误", ENGLISH: "Bad\npassword"},
    "start_recording": {CHINESE: "开始录制", ENGLISH: "Start recording"},
    "pause_recording": {CHINESE: "暂停录制", ENGLISH: "Pause recording"},
    "resume_recording": {CHINESE: "继续录制", ENGLISH: "Resume recording"},
    "stop_recording": {CHINESE: "停止录制", ENGLISH: "Stop recording"},
    "open_recording_folder": {CHINESE: "打开录制文件夹", ENGLISH: "Open recording folder"},
    "recent_recordings": {CHINESE: "最近录制", ENGLISH: "Recent recordings"},
    "recent_empty": {CHINESE: "暂无最近录制", ENGLISH: "No recent recordings"},
    "open_file": {CHINESE: "打开文件", ENGLISH: "Open file"},
    "rename_recording": {CHINESE: "重命名视频", ENGLISH: "Rename video"},
    "rename_video_title": {CHINESE: "重命名视频", ENGLISH: "Rename video"},
    "rename_video_prompt": {CHINESE: "新文件名", ENGLISH: "New file name"},
    "rename_video_unavailable": {CHINESE: "没有可重命名的录制视频", ENGLISH: "No recording is ready to rename"},
    "rename_video_missing": {CHINESE: "录制视频文件不存在", ENGLISH: "The recorded video file cannot be found"},
    "rename_video_invalid": {CHINESE: "文件名不能为空，且不能包含以下字符：\\ / : * ? \" < > |", ENGLISH: "The name cannot be blank or contain \\ / : * ? \" < > |"},
    "rename_video_exists": {CHINESE: "已存在同名文件", ENGLISH: "A file with that name already exists"},
    "rename_video_failed": {CHINESE: "无法重命名视频：{error}", ENGLISH: "Could not rename the video: {error}"},
    "rename_video_busy": {CHINESE: "文件仍在写入，稍后重试…", ENGLISH: "File is still being written; retrying…"},
    "hide_floating_ball": {CHINESE: "隐藏悬浮球", ENGLISH: "Hide floating ball"},
    "show_hide": {CHINESE: "显示/隐藏", ENGLISH: "Show/Hide"},
    "connection_settings": {CHINESE: "连接设置", ENGLISH: "Connection settings"},
    "quit": {CHINESE: "退出", ENGLISH: "Quit"},
    "settings_title": {CHINESE: "OBS 连接设置", ENGLISH: "OBS Connection Settings"},
    "settings_heading": {CHINESE: "连接 OBS", ENGLISH: "Connect OBS"},
    "settings_intro": {CHINESE: "连接本机 OBS WebSocket，并配置快捷键与录制偏好", ENGLISH: "Connect to the local OBS WebSocket server and configure shortcuts"},
    "group_connection": {CHINESE: "连接", ENGLISH: "CONNECTION"},
    "group_preferences": {CHINESE: "偏好设置", ENGLISH: "PREFERENCES"},
    "group_hotkeys": {CHINESE: "快捷键", ENGLISH: "HOTKEYS"},
    "server": {CHINESE: "服务器", ENGLISH: "Server"},
    "host": {CHINESE: "地址", ENGLISH: "Host"},
    "port": {CHINESE: "端口", ENGLISH: "Port"},
    "password": {CHINESE: "密码", ENGLISH: "Password"},
    "password_placeholder": {CHINESE: "OBS WebSocket 密码（可留空）", ENGLISH: "OBS WebSocket password (optional)"},
    "language": {CHINESE: "语言", ENGLISH: "Language"},
    "hotkey": {CHINESE: "显示/隐藏", ENGLISH: "Show/Hide"},
    "hotkey_start": {CHINESE: "开始录制", ENGLISH: "Start recording"},
    "hotkey_pause": {CHINESE: "暂停/继续", ENGLISH: "Pause/Resume"},
    "hotkey_stop": {CHINESE: "停止录制", ENGLISH: "Stop recording"},
    "hotkey_hint": {CHINESE: "点击后按下组合键", ENGLISH: "Click then press a key combination"},
    "hotkey_restore": {CHINESE: "恢复默认快捷键", ENGLISH: "Restore default shortcuts"},
    "autostart": {CHINESE: "开机启动", ENGLISH: "Start with Windows"},
    "autostart_enable": {CHINESE: "登录时启动", ENGLISH: "Launch at sign-in"},
    "auto_rename": {CHINESE: "停止后重命名", ENGLISH: "Rename after stop"},
    "auto_rename_enable": {CHINESE: "停止录制后自动弹出重命名", ENGLISH: "Prompt to rename after stopping"},
    "auto_hide_recording": {CHINESE: "录制时隐藏", ENGLISH: "Hide while recording"},
    "auto_hide_recording_enable": {CHINESE: "开始录制后自动隐藏悬浮球", ENGLISH: "Hide the floating ball while recording"},
    "save_connect": {CHINESE: "保存并连接", ENGLISH: "Save and connect"},
    "cancel": {CHINESE: "取消", ENGLISH: "Cancel"},
    "ok": {CHINESE: "好", ENGLISH: "OK"},
    "capture_bar_in_display": {CHINESE: "悬浮控制条为实心胶囊，通常会被系统从“显示器采集”中排除；若仍出现可开启“录制时隐藏”。", ENGLISH: "The solid floating capsule is normally excluded from display capture; enable hide-while-recording if it still appears."},
    "capture_bar_excluded": {CHINESE: "悬浮控制条已尝试排除“显示器采集”，录制时可留在桌面上而不进画面。", ENGLISH: "The floating control bar is excluded from display capture, so it can stay visible without appearing in recordings."},
    "capture_bar_exclude_failed": {CHINESE: "采集排除不可用：{reason}。可开启“录制时隐藏”或用快捷键隐藏。", ENGLISH: "Capture exclusion unavailable: {reason}. Enable hide-while-recording or use the hide shortcut."},
    "capture_bar_pending": {CHINESE: "正在应用采集排除…", ENGLISH: "Applying capture exclusion?"},
    "shortcut_unavailable": {CHINESE: "快捷键不可用", ENGLISH: "Shortcut unavailable"},
    "obs_action_failed": {CHINESE: "OBS 操作失败", ENGLISH: "OBS action failed"},
    "password_save_failed": {CHINESE: "无法保存密码", ENGLISH: "Unable to save password"},
    "invalid_port": {CHINESE: "端口必须是 1–65535 的整数", ENGLISH: "Port must be an integer from 1 to 65535"},
}


def normalize_language(language: str | None) -> str:
    return language if language in SUPPORTED_LANGUAGES else CHINESE


def tr(key: str, language: str = CHINESE, **values: object) -> str:
    entry = _TEXT.get(key)
    if entry is None:
        return key
    template = entry.get(normalize_language(language), entry[CHINESE])
    if values:
        return template.format(**values)
    return template
