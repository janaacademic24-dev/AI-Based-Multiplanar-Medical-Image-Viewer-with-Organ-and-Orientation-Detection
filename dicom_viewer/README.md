# 🧠 Advanced DICOM Viewer

> AI-powered multiplanar DICOM viewer with organ detection, oblique slicing, ROI tools, and batch export.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green)
![AI](https://img.shields.io/badge/AI-CLIP%20%2F%20ResNet50-orange)

---

## Features

| Feature | Description |
|---|---|
| 📐 Multiplanar Reconstruction | Axial, Coronal, Sagittal views with cross-hair reference lines |
| 🔄 True Oblique Slicing | Bilinear-interpolated oblique planes (not simple rotation) |
| 🌟 MIP View | Maximum Intensity Projection for vascular/bone overview |
| 🤖 AI Organ Detection | CLIP (ViT-B/32) zero-shot or ResNet50 fallback |
| 🧭 Auto Orientation | Reads `ImageOrientationPatient` DICOM tag automatically |
| ✏️ ROI Drawing | Draw, extract, and save regions of interest per view |
| 💾 Batch PNG Export | Export slice ranges with configurable step |
| 🔍 Zoom & Pan | Mouse-wheel zoom + drag pan on every panel |
| 🎨 Dark Theme | Polished dark UI styled with QSS |

---

## Project Structure

```
dicom_viewer/
├── core/
│   ├── dicom_loader.py     ← DICOM folder → 3D numpy volume
│   ├── plane_slicer.py     ← Axial / coronal / sagittal / oblique / MIP
│   └── roi_manager.py      ← ROI extraction & save helpers
├── ai/
│   ├── organ_detector.py   ← CLIP / ResNet50 prediction
│   └── analysis_worker.py  ← QThread wrapper for background inference
├── ui/
│   ├── main_window.py      ← Top-level QMainWindow
│   ├── viewer_panel.py     ← Interactive image panel (zoom / pan / ROI)
│   └── dialogs.py          ← Batch export dialog
├── utils/
│   └── theme.py            ← Dark QSS stylesheet
├── main.py                 ← Entry point
└── requirements.txt
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

For GPU acceleration:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 2. Run the viewer

```bash
python -m dicom_viewer.main
# or with a folder pre-loaded:
python -m dicom_viewer.main --dicom /path/to/your/dicoms
```

---

## Usage

1. **Load DICOM** – click `📁 Load DICOM` and select a folder of `.dcm` files.
2. **Navigate** – drag the sliders below each panel, or scroll with the mouse wheel to zoom.
3. **Oblique / MIP** – use the bottom-right panel; switch mode and adjust the angle.
4. **AI Analysis** – click `🤖 Run AI Analysis`; results appear in a dialog.
5. **Draw ROI** – toggle `✏ Draw ROI`, drag a rectangle on any panel.
6. **Save ROI** – click `💾 Save ROI` to write PNGs for every drawn ROI.
7. **Batch Export** – click `💾 Batch Export` to export a range of slices.

---

## AI Model Details

| Priority | Model | Notes |
|---|---|---|
| 1st | CLIP ViT-B/32 (`open_clip_torch`) | Zero-shot; no fine-tuning needed |
| 2nd | ResNet50 (`torchvision`) | Fallback if CLIP not installed |

The detector auto-picks CLIP when `open_clip_torch` is installed.  
Both models run on GPU if available, CPU otherwise.

---

## Development

```bash
# run tests
python -m pytest tests/

# import as a library
from dicom_viewer.core import DicomLoader, PlaneSlicer
from dicom_viewer.ai import OrganDetector
```

---

## License

MIT
