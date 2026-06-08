"""
Main Window
The top-level QMainWindow that wires together loading, slicing, AI, and export.
"""

import numpy as np
from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QFileDialog, QMessageBox,
    QGroupBox, QComboBox, QDoubleSpinBox, QDialog, QApplication,
)
from PyQt5.QtCore import Qt

from ..core import DicomLoader, PlaneSlicer, normalize_slice
from ..ai import AnalysisWorker
from .viewer_panel import ViewerPanel
from .dialogs import BatchExportDialog


class MainWindow(QMainWindow):
    """
    Four-panel DICOM viewer:
      Top-left   – Axial
      Top-right  – Coronal
      Bottom-left  – Sagittal
      Bottom-right – Oblique / MIP
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced DICOM Viewer  ·  AI Orientation & Organ Detection")
        self.setGeometry(50, 50, 1800, 1000)

        # ── state ──────────────────────────────────────────────────────────────
        self.volume: np.ndarray | None = None
        self.slicer: PlaneSlicer | None = None
        self.dims = None
        self.min_val = self.max_val = 0.0
        self.spacing = (1.0, 1.0, 1.0)
        self.orientation = ""

        self.axial_idx = self.coronal_idx = self.sagittal_idx = self.fourth_idx = 0

        self._build_ui()

    # ══════════════════════════════════════════════════════════════════════════
    # UI construction
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setSpacing(8)
        root_layout.setContentsMargins(10, 10, 10, 10)

        root_layout.addLayout(self._build_toolbar())

        views = QWidget()
        vl = QVBoxLayout(views)
        vl.setSpacing(4)

        top = QHBoxLayout()
        top.addLayout(self._build_standard_panel("Axial",    "axial"))
        top.addLayout(self._build_standard_panel("Coronal",  "coronal"))
        vl.addLayout(top, 1)

        bot = QHBoxLayout()
        bot.addLayout(self._build_standard_panel("Sagittal", "sagittal"))
        bot.addLayout(self._build_fourth_panel())
        vl.addLayout(bot, 1)

        root_layout.addWidget(views, 1)

        self.status = QLabel("Ready  ·  Load a DICOM folder to begin")
        self.status.setStyleSheet(
            "background:#1e2530; color:#c8d0dc; padding:10px; "
            "font-size:13px; border-radius:4px;"
        )
        root_layout.addWidget(self.status)

    # ── toolbar ────────────────────────────────────────────────────────────────

    def _build_toolbar(self) -> QHBoxLayout:
        bar = QHBoxLayout()

        # File
        fg = QGroupBox("File")
        fl = QHBoxLayout(fg)
        self._btn(fl, "📁  Load DICOM",   self.load_dicom,        bold=True)
        self.export_btn = self._btn(fl, "💾  Batch Export", self.batch_export, enabled=False)
        bar.addWidget(fg)

        # AI
        ag = QGroupBox("AI Analysis")
        al = QHBoxLayout(ag)
        self.analyze_btn = self._btn(
            al, "🤖  Run AI Analysis", self.run_analysis,
            color="#27ae60", enabled=False
        )
        bar.addWidget(ag)

        # ROI
        rg = QGroupBox("ROI")
        rl = QHBoxLayout(rg)
        self.roi_toggle = self._btn(rl, "✏  Draw ROI", self.toggle_roi, checkable=True)
        self._btn(rl, "💾  Save ROI", self.save_roi)
        bar.addWidget(rg)

        # View
        vg = QGroupBox("View")
        vl = QHBoxLayout(vg)
        self._btn(vl, "🔍  Reset Zoom", self.reset_zoom)
        bar.addWidget(vg)

        # Info
        self.info_label = QLabel("No data loaded")
        self.info_label.setStyleSheet(
            "font-size:12px; padding:10px; background:#253040; "
            "color:#a8b8c8; border-radius:4px;"
        )
        bar.addWidget(self.info_label, 1)

        return bar

    # ── standard view panel ────────────────────────────────────────────────────

    def _build_standard_panel(self, title: str, name: str) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(4)

        hdr = QLabel(title)
        hdr.setAlignment(Qt.AlignCenter)
        hdr.setStyleSheet(
            "font-weight:bold; font-size:15px; background:#2c3e50; "
            "color:#ecf0f1; padding:7px; border-radius:4px;"
        )
        layout.addWidget(hdr)

        viewer = ViewerPanel(name)
        setattr(self, f"{name}_viewer", viewer)
        layout.addWidget(viewer, 1)

        row = QHBoxLayout()
        slider = QSlider(Qt.Horizontal)
        slider.setEnabled(False)
        slider.valueChanged.connect(lambda v, n=name: self._on_slider(n, v))
        setattr(self, f"{name}_slider", slider)
        row.addWidget(slider, 1)

        lbl = QLabel("0 / 0")
        lbl.setFixedWidth(64)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size:11px; color:#8899aa;")
        setattr(self, f"{name}_lbl", lbl)
        row.addWidget(lbl)

        layout.addLayout(row)
        return layout

    # ── fourth (oblique/MIP) panel ─────────────────────────────────────────────

    def _build_fourth_panel(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(4)

        hdr = QLabel("Oblique / MIP")
        hdr.setAlignment(Qt.AlignCenter)
        hdr.setStyleSheet(
            "font-weight:bold; font-size:15px; background:#5b2c6f; "
            "color:#ecf0f1; padding:7px; border-radius:4px;"
        )
        layout.addWidget(hdr)

        # Mode + angle row
        cfg_row = QHBoxLayout()
        cfg_row.addWidget(QLabel("Mode:"))
        self.fourth_mode = QComboBox()
        self.fourth_mode.addItems(["Oblique Plane", "MIP (Max Intensity)"])
        self.fourth_mode.currentTextChanged.connect(self._on_fourth_mode_change)
        cfg_row.addWidget(self.fourth_mode, 1)

        cfg_row.addWidget(QLabel("Angle:"))
        self.oblique_angle = QDoubleSpinBox()
        self.oblique_angle.setRange(0, 180)
        self.oblique_angle.setValue(0)
        self.oblique_angle.setSuffix("°")
        self.oblique_angle.setSingleStep(5)
        self.oblique_angle.valueChanged.connect(self._refresh_oblique_range)
        cfg_row.addWidget(self.oblique_angle)
        layout.addLayout(cfg_row)

        self.fourth_viewer = ViewerPanel("fourth")
        layout.addWidget(self.fourth_viewer, 1)

        row = QHBoxLayout()
        self.fourth_slider = QSlider(Qt.Horizontal)
        self.fourth_slider.setEnabled(False)
        self.fourth_slider.valueChanged.connect(lambda v: self._on_slider("fourth", v))
        row.addWidget(self.fourth_slider, 1)

        self.fourth_lbl = QLabel("0 / 0")
        self.fourth_lbl.setFixedWidth(64)
        self.fourth_lbl.setAlignment(Qt.AlignCenter)
        self.fourth_lbl.setStyleSheet("font-size:11px; color:#8899aa;")
        row.addWidget(self.fourth_lbl)
        layout.addLayout(row)

        return layout

    # ══════════════════════════════════════════════════════════════════════════
    # Data loading
    # ══════════════════════════════════════════════════════════════════════════

    def load_dicom(self):
        folder = QFileDialog.getExistingDirectory(self, "Select DICOM Folder")
        if not folder:
            return

        try:
            self._set_status("⏳  Loading DICOM…")
            QApplication.processEvents()

            loader = DicomLoader()
            self.volume, self.dims, self.min_val, self.max_val, self.spacing, self.orientation = \
                loader.load_folder(folder)

            self.slicer = PlaneSlicer(self.volume)

            # initialise slice indices to centre
            self.axial_idx    = self.dims[2] // 2
            self.coronal_idx  = self.dims[1] // 2
            self.sagittal_idx = self.dims[0] // 2
            self.fourth_idx   = 0

            # configure sliders
            self._init_slider("axial",    self.dims[2] - 1, self.axial_idx)
            self._init_slider("coronal",  self.dims[1] - 1, self.coronal_idx)
            self._init_slider("sagittal", self.dims[0] - 1, self.sagittal_idx)
            self._refresh_oblique_range()

            self.info_label.setText(
                f"Volume: {self.dims[0]}×{self.dims[1]}×{self.dims[2]}  "
                f"·  Orientation: {self.orientation}  "
                f"·  Spacing: {self.spacing[0]:.2f}×{self.spacing[1]:.2f}×{self.spacing[2]:.2f} mm"
            )

            self.analyze_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self._refresh_all_views()
            self._set_status(f"✅  Loaded  ·  Detected: {self.orientation}")

        except Exception as e:
            QMessageBox.critical(self, "Load Error", str(e))
            self._set_status("❌  Load failed")

    # ══════════════════════════════════════════════════════════════════════════
    # View rendering
    # ══════════════════════════════════════════════════════════════════════════

    def _refresh_all_views(self):
        if self.slicer is None:
            return

        def _norm(arr):
            return normalize_slice(arr, self.min_val, self.max_val)

        # Axial
        ax = _norm(self.slicer.axial(self.axial_idx))
        self.axial_viewer.set_reference_lines(
            self.coronal_idx  / max(1, self.dims[1] - 1),
            self.sagittal_idx / max(1, self.dims[0] - 1),
        )
        self.axial_viewer.display_array(ax, show_ref=True)

        # Coronal
        co = _norm(self.slicer.coronal(self.coronal_idx))
        self.coronal_viewer.set_reference_lines(
            self.sagittal_idx / max(1, self.dims[0] - 1),
            self.axial_idx    / max(1, self.dims[2] - 1),
        )
        self.coronal_viewer.display_array(co, show_ref=True)

        # Sagittal
        sa = _norm(self.slicer.sagittal(self.sagittal_idx))
        self.sagittal_viewer.set_reference_lines(
            self.coronal_idx / max(1, self.dims[1] - 1),
            self.axial_idx   / max(1, self.dims[2] - 1),
        )
        self.sagittal_viewer.display_array(sa, show_ref=True)

        # Fourth
        mode = self.fourth_mode.currentText()
        if mode == "Oblique Plane":
            angle = self.oblique_angle.value()
            n = self.slicer.oblique_n_slices(angle)
            pos = self.fourth_idx / max(1, n - 1)
            fourth_arr = self.slicer.oblique(angle, pos)
        else:
            fourth_arr = self.slicer.mip()

        self.fourth_viewer.display_array(_norm(fourth_arr), show_ref=False)

    # ══════════════════════════════════════════════════════════════════════════
    # Slider / mode handlers
    # ══════════════════════════════════════════════════════════════════════════

    def _on_slider(self, name: str, value: int):
        if name == "axial":
            self.axial_idx = value
            self.axial_lbl.setText(f"{value} / {self.dims[2]-1}")
        elif name == "coronal":
            self.coronal_idx = value
            self.coronal_lbl.setText(f"{value} / {self.dims[1]-1}")
        elif name == "sagittal":
            self.sagittal_idx = value
            self.sagittal_lbl.setText(f"{value} / {self.dims[0]-1}")
        elif name == "fourth":
            self.fourth_idx = value
            self.fourth_lbl.setText(f"{value} / {self.fourth_slider.maximum()}")
        self._refresh_all_views()

    def _on_fourth_mode_change(self, mode: str):
        self.oblique_angle.setEnabled(mode == "Oblique Plane")
        if mode == "Oblique Plane":
            self._refresh_oblique_range()
        else:
            self.fourth_slider.setEnabled(False)
        if self.slicer:
            self._refresh_all_views()

    def _refresh_oblique_range(self):
        if self.slicer is None:
            return
        n = self.slicer.oblique_n_slices(self.oblique_angle.value())
        self.fourth_slider.setMaximum(max(1, n - 1))
        self.fourth_slider.setValue(n // 2)
        self.fourth_slider.setEnabled(True)
        if self.slicer:
            self._refresh_all_views()

    # ══════════════════════════════════════════════════════════════════════════
    # ROI
    # ══════════════════════════════════════════════════════════════════════════

    def toggle_roi(self, checked: bool):
        for name in ("axial", "coronal", "sagittal", "fourth"):
            getattr(self, f"{name}_viewer").set_roi_mode(checked)
        self._set_status("✏  ROI mode on – draw on any panel" if checked else "ROI mode off")

    def save_roi(self):
        if self.volume is None:
            return self._warn("No data loaded")

        import cv2
        save_dir = QFileDialog.getExistingDirectory(self, "Choose save directory")
        if not save_dir:
            return

        saved = 0
        for name in ("axial", "coronal", "sagittal", "fourth"):
            arr = getattr(self, f"{name}_viewer").get_roi_array()
            if arr is not None:
                path = Path(save_dir) / f"ROI_{name.capitalize()}_{self.axial_idx:04d}.png"
                cv2.imwrite(str(path), arr)
                saved += 1

        if saved:
            QMessageBox.information(self, "Saved", f"Saved {saved} ROI(s) to:\n{save_dir}")
            self._set_status(f"✅  Saved {saved} ROI(s)")
        else:
            self._warn("No ROI drawn yet – use 'Draw ROI' first")

    # ══════════════════════════════════════════════════════════════════════════
    # Batch export
    # ══════════════════════════════════════════════════════════════════════════

    def batch_export(self):
        if self.volume is None:
            return self._warn("No data loaded")

        dlg = BatchExportDialog(max(self.dims), self)
        if dlg.exec_() != QDialog.Accepted:
            return

        p = dlg.get_parameters()
        save_dir = QFileDialog.getExistingDirectory(self, "Choose export directory")
        if not save_dir:
            return

        import cv2
        count = 0
        try:
            self._set_status(f"⏳  Exporting {p['view']} slices…")
            QApplication.processEvents()

            for idx in range(p["start"], p["end"] + 1, p["step"]):
                view = p["view"].lower()
                if view == "axial" and idx < self.dims[2]:
                    arr = self.slicer.axial(idx)
                elif view == "coronal" and idx < self.dims[1]:
                    arr = self.slicer.coronal(idx)
                elif view == "sagittal" and idx < self.dims[0]:
                    arr = self.slicer.sagittal(idx)
                else:
                    continue

                norm = normalize_slice(arr, self.min_val, self.max_val)
                cv2.imwrite(str(Path(save_dir) / f"{p['view']}_slice_{idx:04d}.png"), norm)
                count += 1

            QMessageBox.information(self, "Done", f"Exported {count} slices to:\n{save_dir}")
            self._set_status(f"✅  Exported {count} slices")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
            self._set_status("❌  Export failed")

    # ══════════════════════════════════════════════════════════════════════════
    # AI analysis
    # ══════════════════════════════════════════════════════════════════════════

    def run_analysis(self):
        if self.volume is None:
            return self._warn("No data loaded")

        self.analyze_btn.setEnabled(False)
        self._set_status("🤖  Starting AI analysis…")

        self._worker = AnalysisWorker(self.volume, self.spacing, self.orientation)
        self._worker.progress.connect(lambda m: self._set_status(f"🤖  {m}"))
        self._worker.finished.connect(self._on_analysis_done)
        self._worker.start()

    def _on_analysis_done(self, result: dict):
        self.analyze_btn.setEnabled(True)

        if "error" in result:
            QMessageBox.critical(self, "Analysis Error", result["error"])
            self._set_status("❌  Analysis failed")
            return

        preds = result["slice_predictions"]
        stats = result["volume_stats"]

        msg = (
            f"🎯  AI Analysis Complete\n\n"
            f"Model : {result['model_used']}   Device : {result['device']}\n"
            f"Orientation : {result['orientation']}\n\n"
            f"── Organ Predictions ──────────────────\n"
            + "\n".join(
                f"  {p['view']:10s}  {p['class']:<12s}  {p['confidence']*100:.1f}%"
                for p in preds
            )
            + f"\n\n── Volume Statistics ──────────────────\n"
            f"  Volume      : {stats['Total_Volume_ml']:.1f} mL\n"
            f"  Mean HU     : {stats['Mean_Intensity']:.1f}\n"
            f"  Std HU      : {stats['Std_Intensity']:.1f}\n"
            f"  Range       : [{stats['Min_Intensity']:.1f},  {stats['Max_Intensity']:.1f}]"
        )

        QMessageBox.information(self, "Analysis Results", msg)
        self._set_status("✅  AI analysis complete")

    # ══════════════════════════════════════════════════════════════════════════
    # Zoom / helpers
    # ══════════════════════════════════════════════════════════════════════════

    def reset_zoom(self):
        for name in ("axial", "coronal", "sagittal", "fourth"):
            getattr(self, f"{name}_viewer").reset_zoom()
        self._set_status("🔍  Zoom reset")

    def _set_status(self, msg: str):
        self.status.setText(msg)
        QApplication.processEvents()

    def _warn(self, msg: str):
        QMessageBox.warning(self, "Warning", msg)

    def _init_slider(self, name: str, maximum: int, value: int):
        s: QSlider = getattr(self, f"{name}_slider")
        s.setMaximum(maximum)
        s.setValue(value)
        s.setEnabled(True)

    @staticmethod
    def _btn(
        layout: QHBoxLayout,
        text: str,
        slot=None,
        bold: bool = False,
        color: str = "",
        enabled: bool = True,
        checkable: bool = False,
    ) -> QPushButton:
        btn = QPushButton(text)
        btn.setEnabled(enabled)
        btn.setCheckable(checkable)
        style = "padding:9px 14px; font-size:13px;"
        if bold:
            style += " font-weight:bold;"
        if color:
            style += f" background:{color}; color:white;"
        btn.setStyleSheet(style)
        if slot:
            btn.clicked.connect(slot)
        layout.addWidget(btn)
        return btn
