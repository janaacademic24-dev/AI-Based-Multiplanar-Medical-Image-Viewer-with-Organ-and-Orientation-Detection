"""
Viewer Panel
Interactive QLabel subclass with zoom, pan, ROI drawing, and reference-line overlay.
"""

import numpy as np
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor


class ViewerPanel(QLabel):
    """
    A single MPR view panel supporting:
      - Zoom  (mouse wheel)
      - Pan   (left-drag when not in ROI mode)
      - ROI   (left-drag in ROI mode)
      - Reference cross-hair lines (cyan)
    """

    def __init__(self, view_name: str):
        super().__init__()
        self.view_name = view_name
        self.setMinimumSize(400, 400)
        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(False)
        self.setStyleSheet("border: 2px solid #3d4450; background: #111418;")

        # zoom / pan state
        self.zoom_factor: float = 1.0
        self._pan_offset = QPoint(0, 0)
        self._panning = False
        self._last_pan = QPoint()

        # ROI state
        self.roi_mode: bool = False
        self._roi_start: QPoint | None = None
        self._drawing_roi: bool = False
        self.roi_rect: QRect | None = None

        # display data
        self.current_array: np.ndarray | None = None
        self.base_pixmap: QPixmap | None = None
        self._ref_h: float | None = None
        self._ref_v: float | None = None

        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)

    # ── public API ─────────────────────────────────────────────────────────────

    def display_array(self, arr: np.ndarray, show_ref: bool = False):
        """Render a uint8 grayscale 2D array."""
        if arr is None or arr.size == 0:
            return
        self.current_array = arr.copy()
        arr_c = np.ascontiguousarray(arr.astype(np.uint8))
        h, w = arr_c.shape
        qimg = QImage(arr_c.data, w, h, w, QImage.Format_Grayscale8)
        self.base_pixmap = QPixmap.fromImage(qimg.copy())
        self._render(show_ref)

    def set_reference_lines(self, h_pos: float | None = None, v_pos: float | None = None):
        """Set normalized (0–1) positions for the cyan cross-hair lines."""
        self._ref_h = h_pos
        self._ref_v = v_pos

    def set_roi_mode(self, enabled: bool):
        self.roi_mode = enabled
        if not enabled:
            self.roi_rect = None
        self.setCursor(Qt.CrossCursor if enabled else Qt.ArrowCursor)

    def reset_zoom(self):
        self.zoom_factor = 1.0
        self._pan_offset = QPoint(0, 0)
        self._render(True)

    def get_roi_array(self) -> np.ndarray | None:
        """Return the cropped ROI array, or None if no ROI drawn."""
        if self.roi_rect is None or self.current_array is None or self.base_pixmap is None:
            return None

        scale_x = self.current_array.shape[1] / max(1, self.base_pixmap.width())
        scale_y = self.current_array.shape[0] / max(1, self.base_pixmap.height())

        x = max(0, int(self.roi_rect.x() * scale_x))
        y = max(0, int(self.roi_rect.y() * scale_y))
        w = min(int(self.roi_rect.width() * scale_x), self.current_array.shape[1] - x)
        h = min(int(self.roi_rect.height() * scale_y), self.current_array.shape[0] - y)

        if w <= 0 or h <= 0:
            return None
        return self.current_array[y: y + h, x: x + w]

    # ── Qt event overrides ─────────────────────────────────────────────────────

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.zoom_factor = (
            min(self.zoom_factor * 1.1, 5.0) if delta > 0
            else max(self.zoom_factor * 0.9, 0.5)
        )
        self._render(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.base_pixmap is not None:
            self._render(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.roi_mode:
                self._roi_start = event.pos()
                self._drawing_roi = True
            else:
                self._panning = True
                self._last_pan = event.pos()
                self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._drawing_roi and self._roi_start:
            p = event.pos()
            x = min(self._roi_start.x(), p.x())
            y = min(self._roi_start.y(), p.y())
            w = abs(p.x() - self._roi_start.x())
            h = abs(p.y() - self._roi_start.y())
            self.roi_rect = QRect(x, y, w, h)
            self._render(True)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drawing_roi = False
            self._panning = False
            self.setCursor(Qt.CrossCursor if self.roi_mode else Qt.ArrowCursor)

    # ── internal rendering ─────────────────────────────────────────────────────

    def _render(self, show_ref: bool = False):
        if self.base_pixmap is None:
            return

        pixmap = self.base_pixmap.copy()
        painter = QPainter(pixmap)

        # reference lines
        if show_ref:
            painter.setPen(QPen(QColor(0, 200, 255), 1))
            if self._ref_h is not None:
                y = int(self._ref_h * pixmap.height())
                painter.drawLine(0, y, pixmap.width(), y)
            if self._ref_v is not None:
                x = int(self._ref_v * pixmap.width())
                painter.drawLine(x, 0, x, pixmap.height())

        # ROI overlay
        if self.roi_rect is not None:
            painter.setPen(QPen(QColor(255, 80, 80), 2))
            painter.drawRect(self.roi_rect)

        painter.end()

        # scale with zoom
        if self.zoom_factor != 1.0:
            new_size = pixmap.size() * self.zoom_factor
            pixmap = pixmap.scaled(new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.setPixmap(pixmap)
