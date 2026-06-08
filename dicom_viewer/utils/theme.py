"""
Theme
Dark QSS stylesheet for the DICOM viewer.
"""

DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1a1e26;
    color: #d4dce8;
    font-family: "Segoe UI", "SF Pro Display", sans-serif;
}

QGroupBox {
    border: 1px solid #3a4252;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: bold;
    font-size: 12px;
    color: #8899bb;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QPushButton {
    background-color: #2d3748;
    color: #d4dce8;
    border: 1px solid #4a5568;
    border-radius: 5px;
    padding: 8px 14px;
    font-size: 12px;
}
QPushButton:hover  { background-color: #3a4a5c; }
QPushButton:pressed { background-color: #253040; }
QPushButton:disabled { background-color: #242832; color: #556070; }
QPushButton:checked  { background-color: #c0392b; color: white; }

QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #2d3748;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #4a90d9;
    border: none;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover { background: #5ba3e8; }
QSlider::sub-page:horizontal { background: #3a6090; border-radius: 3px; }

QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #253040;
    border: 1px solid #3a4252;
    border-radius: 4px;
    padding: 5px 8px;
    color: #d4dce8;
}
QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #8899bb;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background: #253040;
    border: 1px solid #3a4252;
    selection-background-color: #3a6090;
}

QMessageBox { background-color: #1a1e26; }
QDialog     { background-color: #1a1e26; }
QLabel      { background: transparent; }
"""
