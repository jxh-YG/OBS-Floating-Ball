"""Small runtime translation catalog for the two supported interface languages."""

from __future__ import annotations


CHINESE = "zh_CN"
ENGLISH = "en_US"
SUPPORTED_LANGUAGES = (CHINESE, ENGLISH)

_TEXT = {
    "app_name": {CHINESE: "OBS Floating Ball", ENGLISH: "OBS Floating Ball"},
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
    "annotate": {CHINESE: "标注", ENGLISH: "Annotate"},
    "brush": {CHINESE: "画笔", ENGLISH: "Brush"},
    "eraser": {CHINESE: "橡皮擦", ENGLISH: "Eraser"},
    "select_color": {CHINESE: "选择颜色", ENGLISH: "Choose color"},
    "custom_color": {CHINESE: "自定义颜色", ENGLISH: "Custom color"},
    "choose_color_title": {CHINESE: "选择标注颜色", ENGLISH: "Choose annotation color"},
    "width": {CHINESE: "粗细", ENGLISH: "Width"},
    "brush_width": {CHINESE: "画笔粗细", ENGLISH: "Brush width"},
    "undo": {CHINESE: "撤销", ENGLISH: "Undo"},
    "clear": {CHINESE: "清屏", ENGLISH: "Clear"},
    "exit_annotation": {CHINESE: "退出标注", ENGLISH: "Exit annotation"},
    "rename_recording": {CHINESE: "重命名视频", ENGLISH: "Rename video"},
    "rename_video_title": {CHINESE: "重命名视频", ENGLISH: "Rename video"},
    "rename_video_prompt": {CHINESE: "新文件名", ENGLISH: "New file name"},
    "rename_video_unavailable": {CHINESE: "没有可重命名的录制视频", ENGLISH: "No recording is ready to rename"},
    "rename_video_missing": {CHINESE: "录制视频文件不存在", ENGLISH: "The recorded video file cannot be found"},
    "rename_video_invalid": {CHINESE: "文件名不能为空，且不能包含以下字符：\\ / : * ? \" < > |", ENGLISH: "The name cannot be blank or contain \\ / : * ? \" < > |"},
    "rename_video_exists": {CHINESE: "已存在同名文件", ENGLISH: "A file with that name already exists"},
    "rename_video_failed": {CHINESE: "无法重命名视频：{error}", ENGLISH: "Could not rename the video: {error}"},
    "hide_floating_ball": {CHINESE: "隐藏悬浮球", ENGLISH: "Hide floating ball"},
    "show_hide": {CHINESE: "显示/隐藏", ENGLISH: "Show/Hide"},
    "connection_settings": {CHINESE: "连接设置", ENGLISH: "Connection settings"},
    "quit": {CHINESE: "退出", ENGLISH: "Quit"},
    "settings_title": {CHINESE: "OBS 连接设置", ENGLISH: "OBS Connection Settings"},
    "settings_heading": {CHINESE: "连接 OBS", ENGLISH: "Connect OBS"},
    "settings_intro": {CHINESE: "连接本机 OBS WebSocket 服务", ENGLISH: "Connect to the local OBS WebSocket server"},
    "group_connection": {CHINESE: "连接", ENGLISH: "CONNECTION"},
    "group_preferences": {CHINESE: "偏好设置", ENGLISH: "PREFERENCES"},
    "server": {CHINESE: "服务器", ENGLISH: "Server"},
    "password": {CHINESE: "密码", ENGLISH: "Password"},
    "password_placeholder": {CHINESE: "OBS WebSocket 密码", ENGLISH: "OBS WebSocket password"},
    "language": {CHINESE: "语言", ENGLISH: "Language"},
    "save_connect": {CHINESE: "保存并连接", ENGLISH: "Save and connect"},
    "cancel": {CHINESE: "取消", ENGLISH: "Cancel"},
    "capture_checking": {CHINESE: "悬浮控制条不会进入显示器采集；首次打开标注工具面板时将验证其采集排除能力。", ENGLISH: "The floating control bar stays out of display capture. Annotation-tool exclusion will be checked when it opens."},
    "capture_ready": {CHINESE: "悬浮控制条和标注工具面板都不会进入采集画面。", ENGLISH: "The floating control bar and annotation tools stay out of display capture."},
    "capture_unavailable": {CHINESE: "标注工具面板的采集排除不可用：{reason}", ENGLISH: "Annotation-tool exclusion unavailable: {reason}"},
    "capture_unavailable_title": {CHINESE: "标注工具面板可能出现在采集画面中", ENGLISH: "Annotation tools may appear in capture"},
    "floating_bar_capture_unavailable": {CHINESE: "悬浮控制条的采集排除不可用：{reason}", ENGLISH: "Floating control bar exclusion unavailable: {reason}"},
    "floating_bar_capture_unavailable_title": {CHINESE: "悬浮控制条可能出现在采集画面中", ENGLISH: "Floating control bar may appear in capture"},
    "shortcut_unavailable": {CHINESE: "快捷键不可用", ENGLISH: "Shortcut unavailable"},
    "obs_action_failed": {CHINESE: "OBS 操作失败", ENGLISH: "OBS action failed"},
    "password_save_failed": {CHINESE: "无法保存密码", ENGLISH: "Unable to save password"},
    "annotation_unavailable": {CHINESE: "无法进入标注", ENGLISH: "Cannot start annotation"},
    "no_screen": {CHINESE: "未找到可用显示器", ENGLISH: "No available display was found"},
}


def normalize_language(language: str | None) -> str:
    return language if language in SUPPORTED_LANGUAGES else CHINESE


def tr(key: str, language: str = CHINESE, **values: object) -> str:
    return _TEXT[key][normalize_language(language)].format(**values)
