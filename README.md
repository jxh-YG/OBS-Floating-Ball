# OBS Floating Ball

Windows 10 19045+ 的本机 OBS 28+ 录制控制条，提供开始、暂停/继续、停止与桌面标注。

## 开发运行

```powershell
py -3.11 -m pip install -r requirements-dev.txt
py -3.11 -m pytest
py -3.11 main.py
```

在 OBS 的“工具 -> WebSocket 服务器设置”中启用本机服务后，首次启动输入密码。密码以当前 Windows 用户的 DPAPI 加密后保存在 Qt 用户设置中。

## 打包

```powershell
.\build.ps1
```

生成文件为 `dist\OBS Floating Ball.exe`。

## 手工验收

1. 使用 OBS 的“显示器采集”开始录制，确认透明悬浮控制条的显示效果符合预期。
2. 点击标注并绘制，确认画笔轨迹进入显示器采集画面。
3. 验证暂停、继续、停止和 OBS 的状态一致；`Ctrl+Alt+H` 可隐藏后恢复控制条。

标注叠层只能被“显示器采集”录入；“窗口采集”和“游戏采集”不会采集到桌面标注层，这是 Windows 采集机制所限。

悬浮控制条采用逐像素透明窗口以保证圆角边缘平滑，因此会出现在显示器采集画面中。标注工具面板仍使用 Windows 的 `WDA_EXCLUDEFROMCAPTURE` 排除在采集画面外；画笔轨迹保留在采集画面中。
