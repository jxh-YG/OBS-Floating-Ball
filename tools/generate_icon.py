"""Generate a multi-size app icon for packaging."""

from __future__ import annotations

import struct
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication


def _paint_ball(size: int) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    margin = max(1, size // 16)
    painter.setBrush(QColor(255, 255, 255, 235))
    painter.drawEllipse(margin, margin, size - 2 * margin, size - 2 * margin)
    inset = max(2, size // 6)
    painter.setBrush(QColor("#0A84FF"))
    painter.drawEllipse(inset, inset, size - 2 * inset, size - 2 * inset)
    painter.setBrush(QColor(255, 255, 255, 170))
    hl = max(2, size // 5)
    painter.drawEllipse(size // 3, size // 4, hl, max(2, hl // 2))
    painter.end()
    return image


def _png_bytes(image: QImage) -> bytes:
    buffer = QByteArray()
    device = QBuffer(buffer)
    device.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(device, "PNG")
    device.close()
    return bytes(buffer)


def write_ico(path: Path, sizes: tuple[int, ...] = (16, 32, 48, 64, 128, 256)) -> None:
    entries: list[tuple[int, bytes]] = []
    for size in sizes:
        entries.append((size, _png_bytes(_paint_ball(size))))

    count = len(entries)
    offset = 6 + count * 16
    header = struct.pack("<HHH", 0, 1, count)
    directory = bytearray()
    payloads = bytearray()
    for size, data in entries:
        width = 0 if size >= 256 else size
        height = 0 if size >= 256 else size
        directory.extend(
            struct.pack(
                "<BBBBHHII",
                width,
                height,
                0,
                0,
                1,
                32,
                len(data),
                offset + len(payloads),
            )
        )
        payloads.extend(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + directory + payloads)


def main() -> int:
    QApplication([])
    root = Path(__file__).resolve().parents[1]
    out = root / "assets" / "app.ico"
    write_ico(out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
