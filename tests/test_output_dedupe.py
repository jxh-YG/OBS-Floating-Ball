from PySide6.QtCore import QCoreApplication

from obs_floating_controller.obs_websocket import ObsWebSocketClient


def test_recording_output_ready_emits_once_for_duplicate_paths() -> None:
    app = QCoreApplication.instance() or QCoreApplication([])
    assert app is not None
    client = ObsWebSocketClient()
    paths: list[str] = []
    client.recording_output_ready.connect(paths.append)

    client.handle_payload(
        {
            "op": 7,
            "d": {
                "requestType": "StopRecord",
                "requestId": "1",
                "requestStatus": {"result": True, "code": 100},
                "responseData": {"outputPath": "C:/recordings/clip.mkv"},
            },
        }
    )
    client.handle_payload(
        {
            "op": 5,
            "d": {
                "eventType": "RecordStateChanged",
                "eventData": {
                    "outputState": "OBS_WEBSOCKET_OUTPUT_STOPPED",
                    "outputPath": "C:/recordings/clip.mkv",
                },
            },
        }
    )
    assert paths == ["C:/recordings/clip.mkv"]

    client.handle_payload(
        {
            "op": 5,
            "d": {
                "eventType": "RecordStateChanged",
                "eventData": {
                    "outputState": "OBS_WEBSOCKET_OUTPUT_STARTED",
                },
            },
        }
    )
    client.handle_payload(
        {
            "op": 7,
            "d": {
                "requestType": "StopRecord",
                "requestId": "2",
                "requestStatus": {"result": True, "code": 100},
                "responseData": {"outputPath": "C:/recordings/clip2.mkv"},
            },
        }
    )
    assert paths == ["C:/recordings/clip.mkv", "C:/recordings/clip2.mkv"]
