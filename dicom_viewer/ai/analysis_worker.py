"""
Analysis Worker
Background QThread that runs AI inference and volume statistics
without blocking the GUI.
"""

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

from .organ_detector import OrganDetector


class AnalysisWorker(QThread):
    """
    Runs AI organ detection + volume statistics in a background thread.

    Signals:
        progress(str)  – status messages for the UI
        finished(dict) – results dict (or {'error': msg} on failure)
    """

    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)

    def __init__(self, volume: np.ndarray, spacing=(1.0, 1.0, 1.0), orientation: str = ""):
        super().__init__()
        self.volume = volume.copy()
        self.spacing = spacing
        self.orientation = orientation

    # ── thread entry point ─────────────────────────────────────────────────────

    def run(self):
        try:
            detector = OrganDetector()
            detector.load(progress_cb=self.progress.emit)

            self.progress.emit("Sampling representative slices…")
            slices = {
                "Axial":    self.volume[:, :, self.volume.shape[2] // 2],
                "Coronal":  self.volume[:, self.volume.shape[1] // 2, :],
                "Sagittal": self.volume[self.volume.shape[0] // 2, :, :],
            }

            predictions = []
            for view_name, sl in slices.items():
                pred = detector.predict(sl, view_name)
                predictions.append(pred)
                self.progress.emit(
                    f"{view_name}: {pred['class']} ({pred['confidence'] * 100:.1f}%)"
                )

            self.progress.emit("Computing volume statistics…")
            stats = self._volume_statistics()

            self.progress.emit("Done ✓")
            self.finished.emit({
                "slice_predictions": predictions,
                "volume_stats": stats,
                "orientation": self.orientation or "Unknown",
                "model_used": detector.model_name,
                "device": detector.device_name,
            })

        except Exception as e:
            self.progress.emit(f"Error: {e}")
            self.finished.emit({"error": str(e)})

    # ── helpers ────────────────────────────────────────────────────────────────

    def _volume_statistics(self) -> dict:
        voxel_vol = float(np.prod(self.spacing))
        return {
            "Total_Volume_ml": float(self.volume.size * voxel_vol / 1000.0),
            "Mean_Intensity":  float(np.mean(self.volume)),
            "Std_Intensity":   float(np.std(self.volume)),
            "Min_Intensity":   float(np.min(self.volume)),
            "Max_Intensity":   float(np.max(self.volume)),
        }
