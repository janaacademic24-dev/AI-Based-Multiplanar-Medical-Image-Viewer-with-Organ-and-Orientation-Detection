"""
main.py
Entry point for the Advanced DICOM Viewer.

Usage:
    python main.py
    python main.py --dicom /path/to/dicom/folder
"""

import sys
import argparse


def main():
    from PyQt5.QtWidgets import QApplication
    from dicom_viewer.ui import MainWindow
    from dicom_viewer.utils import DARK_STYLESHEET

    parser = argparse.ArgumentParser(description="Advanced DICOM Viewer")
    parser.add_argument("--dicom", help="Path to DICOM folder to load on startup")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)

    win = MainWindow()
    win.show()

    # Auto-load folder if provided via CLI
    if args.dicom:
        win.load_dicom_path(args.dicom)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
