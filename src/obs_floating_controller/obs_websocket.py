"""OBS WebSocket v5 client built on Qt WebSockets."""

from __future__ import annotations

import json
from itertools import count
from typing import Any

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtNetwork import QAbstractSocket
from PySide6.QtWebSockets import QWebSocket

from .auth import build_obs_auth
from .i18n import CHINESE, tr
from .models import RecordStatus, RecordingStateMachine

OUTPUT_EVENT_SUBSCRIPTION = 1 << 6


def build_identify_payload(hello_data: dict[str, Any], password: str) -> dict[str, Any]:
    identify: dict[str, Any] = {
        "rpcVersion": 1,
        "eventSubscriptions": OUTPUT_EVENT_SUBSCRIPTION,
    }
    authentication = hello_data.get("authentication")
    if authentication:
        identify["authentication"] = build_obs_auth(
            password, authentication["salt"], authentication["challenge"]
        )
    return {"op": 1, "d": identify}


def build_request_payload(request_type: str, request_id: str) -> dict[str, Any]:
    return {"op": 6, "d": {"requestType": request_type, "requestId": request_id}}


class ObsWebSocketClient(QObject):
    """Maintains one reconnecting OBS WebSocket v5 connection."""

    connection_changed = Signal(bool, str)
    record_status_changed = Signal(object)
    recording_output_ready = Signal(str)
    request_failed = Signal(str)
    request_sent = Signal(str, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._socket = QWebSocket()
        self._socket.connected.connect(self._on_connected)
        self._socket.disconnected.connect(self._on_disconnected)
        self._socket.textMessageReceived.connect(self._on_text_message)
        self._socket.errorOccurred.connect(self._on_error)
        self._state_machine = RecordingStateMachine()
        self._host = "127.0.0.1"
        self._port = 4455
        self._password = ""
        self._language = CHINESE
        self._identified = False
        self._should_retry = False
        self._restart_pending = False
        self._retry_attempt = 0
        self._last_error = tr("not_connected", self._language)
        self._request_ids = count(1)
        self._pending: dict[str, str] = {}
        self._last_emitted_output_path: str | None = None
        self._retry_timer = QTimer(self)
        self._retry_timer.setSingleShot(True)
        self._retry_timer.timeout.connect(self._open)

    @property
    def current_status(self) -> RecordStatus:
        return self._state_machine.status()

    @property
    def is_connected(self) -> bool:
        return self._identified

    def set_language(self, language: str) -> None:
        self._language = language

    def connect_to_server(self, password: str, host: str = "127.0.0.1", port: int = 4455) -> None:
        self._host = host
        self._port = port
        self._password = password
        self._should_retry = True
        self._restart_pending = self._socket.state() != QAbstractSocket.SocketState.UnconnectedState
        self._retry_timer.stop()
        if self._restart_pending:
            self._socket.close()
        else:
            self._open()

    def disconnect_from_server(self) -> None:
        self._should_retry = False
        self._restart_pending = False
        self._retry_timer.stop()
        if self._socket.state() != QAbstractSocket.SocketState.UnconnectedState:
            self._socket.close()
        else:
            self._publish_disconnected(tr("not_connected", self._language))

    def start_record(self) -> None:
        self._send_request("StartRecord")

    def pause_record(self) -> None:
        self._send_request("PauseRecord")

    def resume_record(self) -> None:
        self._send_request("ResumeRecord")

    def stop_record(self) -> None:
        self._send_request("StopRecord")

    def refresh_status(self) -> None:
        self._send_request("GetRecordStatus")

    def _open(self) -> None:
        if not self._should_retry:
            return
        self._identified = False
        self.connection_changed.emit(False, tr("connecting", self._language))
        self._socket.open(QUrl(f"ws://{self._host}:{self._port}"))

    def _on_connected(self) -> None:
        self._last_error = ""

    def _on_error(self, _error: QAbstractSocket.SocketError) -> None:
        if self._socket.error() == QAbstractSocket.SocketError.ConnectionRefusedError:
            self._last_error = tr("connection_refused", self._language)
        elif self._socket.error() != QAbstractSocket.SocketError.RemoteHostClosedError:
            self._last_error = tr("connection_error", self._language, error=self._socket.errorString())

    def _on_disconnected(self) -> None:
        reason = self._last_error or tr("connection_lost", self._language)
        authentication_failed = self._socket.closeCode().value == 4009
        if authentication_failed:
            reason = tr("auth_failed", self._language)
            self._should_retry = False
        self._publish_disconnected(reason)
        if self._restart_pending:
            self._restart_pending = False
            self._retry_attempt = 0
            QTimer.singleShot(0, self._open)
        elif self._should_retry:
            self._schedule_retry()

    def _schedule_retry(self) -> None:
        self._retry_attempt += 1
        delay_ms = min(30_000, 1_000 * (2 ** min(self._retry_attempt - 1, 5)))
        self.connection_changed.emit(
            False,
            tr(
                "retry",
                self._language,
                message=self._last_error or tr("connection_lost", self._language),
                seconds=delay_ms // 1000,
            ),
        )
        self._retry_timer.start(delay_ms)

    def _on_text_message(self, raw_message: str) -> None:
        try:
            payload = json.loads(raw_message)
        except json.JSONDecodeError:
            self._last_error = tr("invalid_payload", self._language)
            self._socket.close()
            return
        self.handle_payload(payload)

    def handle_payload(self, payload: dict[str, Any]) -> None:
        """Handle a decoded OBS payload. Public for deterministic protocol tests."""
        operation = payload.get("op")
        data = payload.get("d", {})
        if operation == 0:
            self._socket.sendTextMessage(json.dumps(build_identify_payload(data, self._password)))
        elif operation == 2:
            self._identified = True
            self._retry_attempt = 0
            self.connection_changed.emit(True, tr("connected", self._language))
            self._send_request("GetRecordStatus")
        elif operation == 5 and data.get("eventType") == "RecordStateChanged":
            self._apply_record_data(data.get("eventData", {}))
        elif operation == 7:
            self._handle_request_response(data)

    def _handle_request_response(self, data: dict[str, Any]) -> None:
        request_id = data.get("requestId", "")
        request_type = self._pending.pop(request_id, data.get("requestType", ""))
        request_status = data.get("requestStatus", {})
        if not request_status.get("result", False):
            comment = request_status.get("comment") or tr("unknown_error", self._language)
            code = request_status.get("code", "-")
            self.request_failed.emit(
                tr(
                    "request_failed",
                    self._language,
                    request=request_type or "OBS",
                    comment=comment,
                    code=code,
                )
            )
            return
        if request_type == "GetRecordStatus":
            self._apply_record_data(data.get("responseData", {}))
        elif request_type == "StopRecord":
            self._publish_recording_output(data.get("responseData", {}))

    def _apply_record_data(self, data: dict[str, Any]) -> None:
        output_state = data.get("outputState")
        if output_state == "OBS_WEBSOCKET_OUTPUT_PAUSED":
            output_active, output_paused = True, True
        elif output_state in {
            "OBS_WEBSOCKET_OUTPUT_STARTED",
            "OBS_WEBSOCKET_OUTPUT_RESUMED",
            "OBS_WEBSOCKET_OUTPUT_STARTING",
        }:
            output_active, output_paused = True, False
        elif output_state in {
            "OBS_WEBSOCKET_OUTPUT_STOPPED",
            "OBS_WEBSOCKET_OUTPUT_STOPPING",
        }:
            output_active, output_paused = False, False
        else:
            output_active = bool(data.get("outputActive", False))
            output_paused = bool(data.get("outputPaused", False))
        status = self._state_machine.apply_obs_status(
            output_active=output_active,
            output_paused=output_paused,
            output_duration_ms=data.get("outputDuration"),
        )
        self.record_status_changed.emit(status)
        if status.is_active:
            # Next stop should be allowed to publish a new output path.
            self._last_emitted_output_path = None
        else:
            self._publish_recording_output(data)

    def _publish_recording_output(self, data: dict[str, Any]) -> None:
        output_path = data.get("outputPath")
        if not isinstance(output_path, str) or not output_path:
            return
        # StopRecord reply and RecordStateChanged both carry outputPath; emit once.
        if output_path == self._last_emitted_output_path:
            return
        self._last_emitted_output_path = output_path
        self.recording_output_ready.emit(output_path)

    def _send_request(self, request_type: str) -> None:
        if not self._identified:
            self.request_failed.emit(tr("operation_unavailable", self._language))
            return
        request_id = str(next(self._request_ids))
        self._pending[request_id] = request_type
        self._socket.sendTextMessage(json.dumps(build_request_payload(request_type, request_id)))
        self.request_sent.emit(request_type, request_id)

    def _publish_disconnected(self, message: str) -> None:
        self._identified = False
        self._state_machine.disconnected()
        self.record_status_changed.emit(self._state_machine.status())
        self.connection_changed.emit(False, message)
