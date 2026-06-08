"""
ROI Manager
Handles region-of-interest extraction and export from DICOM slices.
"""

import numpy as np
from pathlib import Path
from PyQt5.QtCore import QRect


class ROIManager:
    """
    Manages ROI extraction from image views and saving to disk.

    Usage:
        manager = ROIManager()
        roi_array = manager.extract(current_array, roi_rect, base_pixmap_size)
        manager.save(roi_array, save_dir, view_name, slice_idx)
    """

    @staticmethod
    def extract(
        array: np.ndarray,
        roi_rect: QRect,
        pixmap_width: int,
        pixmap_height: int,
    ) -> np.ndarray | None:
        """
        Extract the pixel data inside `roi_rect` (screen coordinates) from `array`.

        Args:
            array         : 2D numpy array (the displayed image data)
            roi_rect      : QRect in screen / pixmap coordinates
            pixmap_width  : width of the displayed pixmap
            pixmap_height : height of the displayed pixmap

        Returns:
            2D numpy array cropped to the ROI, or None if invalid.
        """
        if array is None or roi_rect is None:
            return None

        scale_x = array.shape[1] / max(1, pixmap_width)
        scale_y = array.shape[0] / max(1, pixmap_height)

        x = max(0, int(roi_rect.x() * scale_x))
        y = max(0, int(roi_rect.y() * scale_y))
        w = min(int(roi_rect.width() * scale_x), array.shape[1] - x)
        h = min(int(roi_rect.height() * scale_y), array.shape[0] - y)

        if w <= 0 or h <= 0:
            return None

        return array[y: y + h, x: x + w]

    @staticmethod
    def save(roi_array: np.ndarray, save_dir: str, view_name: str, slice_idx: int) -> Path:
        """
        Save ROI array as a PNG file.

        Returns:
            Path to saved file.
        """
        import cv2

        save_path = Path(save_dir) / f"ROI_{view_name}_{slice_idx:04d}.png"
        cv2.imwrite(str(save_path), roi_array)
        return save_path

    @staticmethod
    def statistics(roi_array: np.ndarray) -> dict:
        """Return basic statistics for the ROI."""
        if roi_array is None or roi_array.size == 0:
            return {}
        return {
            "mean": float(np.mean(roi_array)),
            "std": float(np.std(roi_array)),
            "min": float(np.min(roi_array)),
            "max": float(np.max(roi_array)),
            "pixels": int(roi_array.size),
        }
