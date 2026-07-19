"""Real-WebSocket integration tests against a local in-process OBS v5 simulator."""

from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import Callable
from queue import Queue

import pytest
import websockets
from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer

from obs_floating_controller.auth import build_obs_auth
from obs_floating_controller.models import RecordingState
from obs_floating_controller.obs_websocket import OUTPUT_EVENT_SUBSCRIPTION, ObsWebSocketClient


class MockObsServer:
    def __init__(
        self, password: str = "", require_auth: bool = False, initial_recording: bool = True
    ) -> None:
        self.password = password
        self.require_auth = require_auth
        self.initial_recording = initial_recording
        self.requests: Queue[str] = Queue()
        self.identify_payloads: Queue[dict[str, object]] = Queue()
        self.ready = threading.Event()
        self.port = 0
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._server: websockets.asyncio.server.Server | None = None
        self._client: websockets.asyncio.server.ServerConnection | None = None

    def start(self) -> None:
        self._thread.start()
        assert self.ready.wait(5)

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)

        async def start_server() -> None:
            self._server = await websockets.serve(self._handler, "127.0.0.1", 0)
            self.port = self._server.sockets[0].getsockname()[1]
            self.ready.set()

        self._loop.run_until_complete(start_server())
        self._loop.run_forever()
        pending = asyncio.all_tasks(self._loop)
        for task in pending:
            task.cancel()
        if pending:
            self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        self._loop.run_until_complete(self._loop.shutdown_asyncgens())
        self._loop.close()

    async def _handler(self, websocket: websockets.asyncio.server.ServerConnection) -> None:
        self._client = websocket
        hello: dict[str, object] = {"rpcVersion": 1}
        if self.require_auth:
            hello["authentication"] = {"salt": "mock-salt", "challenge": "mock-challenge"}
        await websocket.send(json.dumps({"op": 0, "d": hello}))
        identify = json.loads(await websocket.recv())
        self.identify_payloads.put(identify["d"])
        if self.require_auth:
            expected = build_obs_auth(self.password, "mock-salt", "mock-challenge")
            if identify["d"].get("authentication") != expected:
                await websocket.close(code=4009, reason="Authentication Failed")
                return
        await websocket.send(json.dumps({"op": 2, "d": {"negotiatedRpcVersion": 1}}))
        async for raw in websocket:
            payload = json.loads(raw)
            request_type = payload["d"].get("requestType")
            self.requests.put(request_type)
            request_id = payload["d"]["requestId"]
            if request_type == "GetRecordStatus":
                response_data = {
                    "outputActive": self.initial_recording,
                    "outputPaused": False,
                    "outputDuration": 5_000 if self.initial_recording else 0,
                }
            elif request_type == "StopRecord":
                response_data = {"outputPath": "C:/recordings/meeting.mkv"}
            else:
                response_data = {}
            await websocket.send(
                json.dumps(
                    {
                        "op": 7,
                        "d": {
                            "requestType": request_type,
                            "requestId": request_id,
                            "requestStatus": {"result": True, "code": 100},
                            "responseData": response_data,
                        },
                    }
                )
            )

    def send_record_event(self, output_state: str) -> None:
        async def send() -> None:
            if self._client:
                await self._client.send(
                    json.dumps(
                        {
                            "op": 5,
                            "d": {
                                "eventType": "RecordStateChanged",
                                "eventData": {
                                    "outputState": output_state,
                                },
                            },
                        }
                    )
                )

        asyncio.run_coroutine_threadsafe(send(), self._loop).result(5)

    def drop_client(self) -> None:
        async def drop() -> None:
            if self._client:
                self._client.transport.abort()

        asyncio.run_coroutine_threadsafe(drop(), self._loop).result(5)

    def stop(self) -> None:
        async def close() -> None:
            if self._server:
                self._server.close()
                await self._server.wait_closed()

        asyncio.run_coroutine_threadsafe(close(), self._loop).result(5)
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(5)


@pytest.fixture(scope="module")
def qt_app() -> QCoreApplication:
    return QCoreApplication.instance() or QCoreApplication([])


def wait_until(predicate: Callable[[], bool], timeout_ms: int = 3_000) -> bool:
    loop = QEventLoop()
    timer = QTimer()
    timer.setInterval(10)
    timer.timeout.connect(lambda: loop.quit() if predicate() else None)
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(loop.quit)
    timer.start()
    timeout.start(timeout_ms)
    while not predicate() and timeout.isActive():
        loop.exec()
    return predicate()


def next_request(server: MockObsServer) -> str:
    assert wait_until(lambda: not server.requests.empty())
    return server.requests.get_nowait()


def next_identify(server: MockObsServer) -> dict[str, object]:
    assert wait_until(lambda: not server.identify_payloads.empty())
    return server.identify_payloads.get_nowait()


def disconnect_client(client: ObsWebSocketClient) -> None:
    client.disconnect_from_server()
    assert wait_until(lambda: not client.is_connected)


def test_mock_obs_restores_status_and_accepts_record_commands(qt_app: QCoreApplication) -> None:
    server = MockObsServer()
    server.start()
    client = ObsWebSocketClient()
    output_paths: list[str] = []
    client.recording_output_ready.connect(output_paths.append)
    client.connect_to_server("", port=server.port)
    assert wait_until(lambda: client.current_status.state is RecordingState.RECORDING)
    assert next_identify(server)["eventSubscriptions"] == OUTPUT_EVENT_SUBSCRIPTION
    assert next_request(server) == "GetRecordStatus"

    client.pause_record()
    client.resume_record()
    client.stop_record()
    assert [next_request(server) for _ in range(3)] == ["PauseRecord", "ResumeRecord", "StopRecord"]
    assert wait_until(lambda: output_paths == ["C:/recordings/meeting.mkv"])

    server.send_record_event("OBS_WEBSOCKET_OUTPUT_PAUSED")
    assert wait_until(lambda: client.current_status.state is RecordingState.PAUSED)
    server.send_record_event("OBS_WEBSOCKET_OUTPUT_RESUMED")
    assert wait_until(lambda: client.current_status.state is RecordingState.RECORDING)
    disconnect_client(client)
    server.stop()


def test_mock_obs_accepts_start_record_while_idle(qt_app: QCoreApplication) -> None:
    server = MockObsServer(initial_recording=False)
    server.start()
    client = ObsWebSocketClient()
    client.connect_to_server("", port=server.port)
    assert wait_until(lambda: client.is_connected)
    assert next_request(server) == "GetRecordStatus"
    client.start_record()
    assert next_request(server) == "StartRecord"
    disconnect_client(client)
    server.stop()


def test_mock_obs_rejects_wrong_password(qt_app: QCoreApplication) -> None:
    server = MockObsServer(password="correct", require_auth=True)
    server.start()
    client = ObsWebSocketClient()
    messages: list[str] = []
    client.connection_changed.connect(lambda connected, message: messages.append(message) if not connected else None)
    client.connect_to_server("wrong", port=server.port)
    assert wait_until(lambda: any("密码错误" in message for message in messages))
    assert not client._retry_timer.isActive()
    disconnect_client(client)
    server.stop()


def test_client_retries_after_an_unexpected_server_disconnect(qt_app: QCoreApplication) -> None:
    server = MockObsServer()
    server.start()
    client = ObsWebSocketClient()
    client.connect_to_server("", port=server.port)
    assert wait_until(lambda: client.is_connected)
    assert next_request(server) == "GetRecordStatus"

    server.drop_client()
    assert wait_until(lambda: not client.is_connected)
    assert client._retry_timer.isActive()
    client.disconnect_from_server()
    server.stop()
