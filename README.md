# AI-Based-Multiplanar-Medical-Image-Viewer-with-Organ-and-Orientation-Detection
An AI-powered medical imaging tool that automatically detects the organ and determines the scan’s orientation . The project uses a pretrained AI model and displays the slices in an interactive multiplanar viewer (MPR) with axial, coronal, sagittal, and oblique views.  Users can scroll through slices, zoom in/out, and see dynamic reference lines.
# 🧠 Enhanced DICOM Viewer

A modern **medical imaging tool** designed for exploring, analyzing, and visualizing **DICOM datasets** interactively.  
Built with **Python, PyQt5, VTK, and OpenCV**, this viewer provides a smooth graphical interface for radiological data analysis, segmentation, and visualization.

---

## 🩻 Overview

The **Enhanced DICOM Viewer** enables researchers and biomedical engineers to:
- Load and explore **3D medical image datasets**.
- View **Axial**, **Sagittal**, **Coronal**, and **3D Oblique** slices.
- Perform **basic image analysis**, apply filters, and manage **regions of interest (ROI)**.
- Enhance visualization using **histograms**, **window/level control**, and **intensity projections**.

---

## 🧩 Features
1) Detection of the organ and its orientation, using pre-trained Ai model.
2) Zooming in and out.
3) controlling the brightness and contrast.
4) Displaying the organ in 4 views (Sagittal,coronal,axial and oblique)
5) Saving limited volume for any of the view ports
6) Dynamic reference lines.
    

### 🖥️ Visualization
- Multi-view display: Axial, Sagittal, Coronal, and 3D.
- Adjustable **window/level** controls for contrast and brightness.
- Support for **MIP (Maximum Intensity Projection)** and **Oblique planes**.
- Slice navigation via mouse or slider.

### 🧠 Analysis & Processing

- ROI selection, measurement, and management.    
- Real-time updates across all views.

---

## 📸 Screenshots

| View | Example |
|------|----------|
| Axial View | ![Axial View](assets/screenshots/axial.png) |
| Sagittal View | ![Sagittal View](assets/screenshots/sagittal.png) |
| Coronal View | ![Coronal View](assets/screenshots/coronal.png) |
| 3D Oblique | ![3D Oblique](assets/screenshots/3d_oblique.png) |
| ROI Selection | ![ROI Example](assets/screenshots/roi_example.png) |

---
## How to use ??
1) Run the code!
2) Make sure your data is dicom!
3) Upload your data!

### 🧰 Requirements
Make sure you have **Python 3.8+** installed.

Install the dependencies:
```bash
pip install PyQt5 vtk pydicom numpy matplotlib opencv-python
