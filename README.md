# 🧠 AI-Based Multiplanar Medical Image Viewer

> An AI-powered DICOM viewer that automatically detects organ regions and scan orientation, with interactive multiplanar reconstruction (MPR), oblique slicing, ROI tools, and batch export.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-41cd52?logo=qt)
![AI](https://img.shields.io/badge/AI-CLIP%20%2F%20ResNet50-ff6f00)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## Overview

This tool is built for researchers and biomedical engineers who need to explore 3D medical datasets beyond what a basic DICOM viewer offers. It combines a clean four-panel MPR interface with an AI model that classifies the scanned organ and confirms the imaging orientation — all running locally, no cloud dependency.

---

## Screenshots

![Main View 1](screenshots/main_view_1.jpg)
![Main View 2](screenshots/main_view_2.jpg)
![Main View 3](screenshots/main_view_3.jpg)

---

## Features

| | Feature | Details |
|---|---|---|
| 📐 | **Multiplanar Reconstruction** | Axial, Coronal, Sagittal with live cross-hair reference lines |
| 🔄 | **True Oblique Slicing** | Bilinear-interpolated oblique planes at any angle (0–180°) |
| 🌟 | **MIP View** | Maximum Intensity Projection for bone and vascular overview |
| 🤖 | **AI Organ Detection** | CLIP ViT-B/32 (zero-shot) with ResNet50 fallback |
| 🧭 | **Auto Orientation** | Reads `ImageOrientationPatient` DICOM tag automatically |
| 🎚️ | **Window / Level** | Adjustable brightness and contrast per view |
| ✏️ | **ROI Drawing** | Draw, extract, measure, and export regions of interest |
| 💾 | **Batch PNG Export** | Export any slice range with a configurable step |
| 🔍 | **Zoom & Pan** | Mouse-wheel zoom and drag pan on every panel |

---

## Project Structure

```
dicom_viewer/
├── core/
│   ├── dicom_loader.py       ← DICOM folder → 3D numpy volume + metadata
│   ├── plane_slicer.py       ← Axial / coronal / sagittal / oblique / MIP
│   └── roi_manager.py        ← ROI extraction and save helpers
├── ai/
│   ├── organ_detector.py     ← CLIP / ResNet50 slice classification
│   └── analysis_worker.py    ← Background QThread (never blocks the UI)
├── ui/
│   ├── main_window.py        ← Four-panel QMainWindow
│   ├── viewer_panel.py       ← Interactive image widget (zoom / pan / ROI)
│   └── dialogs.py            ← Batch export dialog
├── utils/
│   └── theme.py              ← Dark QSS stylesheet
├── tests/
│   └── test_core.py          ← Unit tests (no GPU required)
├── main.py                   ← Entry point
└── requirements.txt
```

---

## Installation

**Python 3.10 or newer is required.**

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/AI-Based-Multiplanar-Medical-Image-Viewer-with-Organ-and-Orientation-Detection.git
cd AI-Based-Multiplanar-Medical-Image-Viewer-with-Organ-and-Orientation-Detection

# 2. Install dependencies
pip install -r requirements.txt
```

For GPU acceleration (optional but recommended for AI inference):
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

**Dependencies:**
```
pydicom        ← read DICOM files
numpy          ← volumetric array operations
scipy / Pillow ← image processing
opencv-python  ← slice export
PyQt5          ← GUI
torch + torchvision   ← AI inference
open_clip_torch       ← CLIP model (preferred; falls back to ResNet50)
```

---

## Usage

```bash
# Launch the viewer
python -m dicom_viewer.main

# Launch with a DICOM folder pre-loaded
python -m dicom_viewer.main --dicom /path/to/your/dicoms
```

### Step-by-step

1. **Load data** — click `📁 Load DICOM` and select a folder of `.dcm` files.
2. **Navigate slices** — drag the slider below each panel, or scroll the mouse wheel to zoom.
3. **Switch the fourth panel** — use the dropdown to toggle between **Oblique Plane** (set an angle) and **MIP**.
4. **Run AI analysis** — click `🤖 Run AI Analysis`; organ predictions and volume statistics appear in a dialog.
5. **Draw an ROI** — toggle `✏ Draw ROI`, then drag a rectangle on any panel.
6. **Save ROI** — click `💾 Save ROI` to export PNG crops of every drawn region.
7. **Batch export** — click `💾 Batch Export` to save a range of slices as numbered PNGs.

---

## AI Model Details

The viewer auto-selects the best available model at runtime:

| Priority | Model | How it works |
|---|---|---|
| 1st | **CLIP ViT-B/32** (`open_clip_torch`) | Zero-shot: matches slice image against text prompts like *"a CT scan showing Brain"* |
| 2nd | **ResNet50** (`torchvision`) | Fallback if CLIP is not installed |

Both models run on GPU if available, CPU otherwise. No fine-tuning or labelled data is needed.

---

## Running Tests

```bash
python -m pytest tests/ -v
```

Tests cover slice shape correctness, normalization edge cases, and DICOM orientation tag parsing — no display or GPU required.

---

## Contributing

Pull requests are welcome. For large changes, please open an issue first to discuss what you'd like to change.

---

## License

MIT
