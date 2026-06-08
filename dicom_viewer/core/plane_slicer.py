"""
Plane Slicer
Generates axial/coronal/sagittal views and true oblique slices from a 3D volume.
"""

import numpy as np


def normalize_slice(data: np.ndarray, min_val: float, max_val: float) -> np.ndarray:
    """Normalize a 2D slice to uint8 [0, 255]."""
    if max_val <= min_val:
        return np.zeros_like(data, dtype=np.uint8)
    norm = np.clip((data - min_val) / (max_val - min_val), 0, 1)
    return (norm * 255).astype(np.uint8)


class PlaneSlicer:
    """
    Extracts standard and oblique 2D slices from a (H, W, D) volume.

    Usage:
        slicer = PlaneSlicer(volume)
        axial   = slicer.axial(idx)
        coronal = slicer.coronal(idx)
        sag     = slicer.sagittal(idx)
        oblique = slicer.oblique(angle_deg=45, position=0.5)
        mip     = slicer.mip()
    """

    def __init__(self, volume: np.ndarray):
        self.volume = volume
        self.shape = volume.shape  # (H, W, D)

    # ──────────────────────── Standard views ─────────────────────────

    def axial(self, idx: int) -> np.ndarray:
        """Return axial slice at depth index `idx`."""
        idx = self._clamp(idx, self.shape[2] - 1)
        return self.volume[:, :, idx]

    def coronal(self, idx: int) -> np.ndarray:
        """Return coronal slice (flipped for anatomical orientation)."""
        idx = self._clamp(idx, self.shape[1] - 1)
        sl = self.volume[:, idx, :].T
        return np.rot90(sl, 2)

    def sagittal(self, idx: int) -> np.ndarray:
        """Return sagittal slice (flipped for anatomical orientation)."""
        idx = self._clamp(idx, self.shape[0] - 1)
        sl = self.volume[idx, :, :].T
        return np.rot90(sl, 2)

    # ──────────────────────── Special views ──────────────────────────

    def mip(self, axis: int = 2) -> np.ndarray:
        """Maximum Intensity Projection along the given axis."""
        return np.max(self.volume, axis=axis)

    def oblique(self, angle_degrees: float, position: float) -> np.ndarray:
        """
        Extract a true oblique slice from the volume.

        Args:
            angle_degrees: rotation angle in the XY plane (0–180)
            position:      normalized position along the oblique direction (0.0–1.0)

        Returns:
            2D numpy array of the extracted slice
        """
        angle_rad = np.deg2rad(angle_degrees)
        depth, height, width = self.volume.shape

        direction = np.array([np.cos(angle_rad), np.sin(angle_rad), 0.0])
        center = np.array([depth / 2, height / 2, width / 2])

        max_dist = np.sqrt(
            (depth * np.cos(angle_rad)) ** 2 + (height * np.sin(angle_rad)) ** 2
        )
        n = int(max_dist)
        if n < 1:
            return np.zeros((width, 1), dtype=self.volume.dtype)

        start_pos = position * max_dist - max_dist / 2
        slice_center = center + direction * start_pos

        oblique_slice = np.zeros((width, n), dtype=self.volume.dtype)

        for i in range(n):
            offset = direction * (i - max_dist / 2)
            x = slice_center[0] + offset[0]
            y = slice_center[1] + offset[1]

            for j in range(width):
                z = j
                if 0 <= x < depth - 1 and 0 <= y < height - 1:
                    x0, y0 = int(x), int(y)
                    x1 = min(x0 + 1, depth - 1)
                    y1 = min(y0 + 1, height - 1)
                    dx, dy = x - x0, y - y0

                    v00 = self.volume[x0, y0, int(z)]
                    v01 = self.volume[x0, y1, int(z)]
                    v10 = self.volume[x1, y0, int(z)]
                    v11 = self.volume[x1, y1, int(z)]

                    oblique_slice[j, i] = (
                        v00 * (1 - dx) * (1 - dy)
                        + v01 * (1 - dx) * dy
                        + v10 * dx * (1 - dy)
                        + v11 * dx * dy
                    )

        return oblique_slice

    def max_index(self, axis: str) -> int:
        """Return the last valid index for the given axis name."""
        return {"axial": self.shape[2] - 1,
                "coronal": self.shape[1] - 1,
                "sagittal": self.shape[0] - 1}.get(axis, 0)

    def oblique_n_slices(self, angle_degrees: float) -> int:
        """Number of oblique slices available at this angle."""
        angle_rad = np.deg2rad(angle_degrees)
        depth, height, _ = self.volume.shape
        return max(1, int(np.sqrt(
            (depth * np.cos(angle_rad)) ** 2 + (height * np.sin(angle_rad)) ** 2
        )))

    @staticmethod
    def _clamp(val: int, max_val: int) -> int:
        return max(0, min(val, max_val))
