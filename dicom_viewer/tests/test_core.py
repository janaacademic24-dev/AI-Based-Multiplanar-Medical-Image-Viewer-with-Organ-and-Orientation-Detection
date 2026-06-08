"""
tests/test_core.py
Basic unit tests for core modules (no PyQt5 / GPU required).
"""

import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dicom_viewer.core.plane_slicer import PlaneSlicer, normalize_slice
from dicom_viewer.core.dicom_loader import plane_from_dicom_tags


# ── PlaneSlicer ────────────────────────────────────────────────────────────────

@pytest.fixture
def dummy_volume():
    """30×40×20 synthetic volume with a bright sphere in the centre."""
    vol = np.zeros((30, 40, 20), dtype=np.float32)
    cx, cy, cz = 15, 20, 10
    for z in range(20):
        for y in range(40):
            for x in range(30):
                if (x - cx)**2 + (y - cy)**2 + (z - cz)**2 < 25:
                    vol[x, y, z] = 1000.0
    return vol


def test_axial_shape(dummy_volume):
    s = PlaneSlicer(dummy_volume)
    sl = s.axial(10)
    assert sl.shape == (30, 40)


def test_coronal_shape(dummy_volume):
    s = PlaneSlicer(dummy_volume)
    sl = s.coronal(20)
    assert sl.shape == (20, 30)   # after T + rot90(2)


def test_sagittal_shape(dummy_volume):
    s = PlaneSlicer(dummy_volume)
    sl = s.sagittal(15)
    assert sl.shape == (20, 40)


def test_mip_shape(dummy_volume):
    s = PlaneSlicer(dummy_volume)
    mip = s.mip(axis=2)
    assert mip.shape == (30, 40)


def test_oblique_returns_2d(dummy_volume):
    s = PlaneSlicer(dummy_volume)
    sl = s.oblique(45.0, 0.5)
    assert sl.ndim == 2
    assert sl.shape[0] > 0 and sl.shape[1] > 0


def test_clamp():
    assert PlaneSlicer._clamp(-5, 10) == 0
    assert PlaneSlicer._clamp(20, 10) == 10
    assert PlaneSlicer._clamp(5, 10)  == 5


# ── normalize_slice ────────────────────────────────────────────────────────────

def test_normalize_output_range():
    data = np.array([[0.0, 500.0], [1000.0, 250.0]])
    out = normalize_slice(data, 0.0, 1000.0)
    assert out.dtype == np.uint8
    assert out.min() == 0
    assert out.max() == 255


def test_normalize_flat_image():
    data = np.ones((5, 5)) * 300.0
    out = normalize_slice(data, 300.0, 300.0)   # min == max
    assert (out == 0).all()


# ── plane_from_dicom_tags ──────────────────────────────────────────────────────

class FakeDS:
    def __init__(self, iop):
        self.ImageOrientationPatient = iop


def test_axial_detection():
    # Standard axial IOP: row along X, col along Y → normal along Z (axis 2)
    ds = FakeDS([1, 0, 0, 0, 1, 0])
    assert plane_from_dicom_tags(ds) == "Axial"


def test_sagittal_detection():
    # row along Y, col along Z → normal along X (axis 0)
    ds = FakeDS([0, 1, 0, 0, 0, 1])
    assert plane_from_dicom_tags(ds) == "Sagittal"


def test_missing_tag():
    class NoTag:
        pass
    assert plane_from_dicom_tags(NoTag()) == "Unknown"
