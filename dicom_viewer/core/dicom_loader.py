"""
DICOM Loader
Handles loading, parsing, and organizing DICOM series into volumetric arrays.
"""

import numpy as np
from pathlib import Path
import pydicom


def plane_from_dicom_tags(ds) -> str:
    """
    Determine imaging plane from DICOM ImageOrientationPatient tag.
    Returns: 'Axial', 'Coronal', 'Sagittal', or 'Unknown'
    """
    iop = getattr(ds, 'ImageOrientationPatient', None)
    if iop is None or len(iop) < 6:
        return "Unknown"

    try:
        row = np.array(iop[:3], dtype=float)
        col = np.array(iop[3:6], dtype=float)
        normal = np.cross(row, col)
        axis = int(np.argmax(np.abs(normal)))
        return {0: "Sagittal", 1: "Coronal", 2: "Axial"}.get(axis, "Unknown")
    except Exception:
        return "Unknown"


class DicomLoader:
    """
    Loads a folder of DICOM files into a 3D numpy volume.

    Usage:
        loader = DicomLoader()
        volume, dims, min_val, max_val, spacing, orientation = loader.load_folder("path/to/dicoms")
    """

    @staticmethod
    def load_folder(folder_path: str):
        """
        Load all DICOM files from a folder.

        Returns:
            volume      (H, W, D) float32 numpy array
            dims        tuple (H, W, D)
            min_val     float
            max_val     float
            spacing     tuple (row_mm, col_mm, slice_mm)
            orientation str  e.g. 'Axial'
        """
        folder = Path(folder_path)
        dicom_files = sorted(
            list(folder.glob("*.dcm")) + list(folder.glob("*.DCM"))
        )

        if not dicom_files:
            raise ValueError(f"No DICOM files found in: {folder_path}")

        slices = []
        for idx, f in enumerate(dicom_files):
            try:
                ds = pydicom.dcmread(str(f), force=True)
                pos = float(getattr(ds, 'InstanceNumber', idx))
                slices.append((pos, ds))
            except Exception as e:
                print(f"[WARN] Skipping {f.name}: {e}")

        if not slices:
            raise ValueError("No valid DICOM slices could be read.")

        slices.sort(key=lambda x: x[0])

        first_ds = slices[0][1]
        rows, cols = first_ds.pixel_array.shape
        volume = np.zeros((rows, cols, len(slices)), dtype=np.float32)

        for i, (_, ds) in enumerate(slices):
            arr = ds.pixel_array.astype(np.float32)
            if hasattr(ds, 'RescaleSlope') and hasattr(ds, 'RescaleIntercept'):
                arr = arr * float(ds.RescaleSlope) + float(ds.RescaleIntercept)
            volume[:, :, i] = arr

        spacing = [1.0, 1.0, 1.0]
        if hasattr(first_ds, 'PixelSpacing'):
            spacing[0] = float(first_ds.PixelSpacing[0])
            spacing[1] = float(first_ds.PixelSpacing[1])
        if hasattr(first_ds, 'SliceThickness'):
            spacing[2] = float(first_ds.SliceThickness)

        orientation = plane_from_dicom_tags(first_ds)

        return volume, volume.shape, float(np.min(volume)), float(np.max(volume)), tuple(spacing), orientation
