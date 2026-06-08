"""
Dialogs
Reusable modal dialogs for the DICOM viewer.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QDialogButtonBox,
)


class BatchExportDialog(QDialog):
    """
    Dialog to configure a batch PNG export of slices.

    Usage:
        dlg = BatchExportDialog(max_slices, parent)
        if dlg.exec_() == QDialog.Accepted:
            params = dlg.get_parameters()
            # params = {'view': 'Axial', 'start': 0, 'end': 99, 'step': 1}
    """

    def __init__(self, max_slices: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Batch Export Slices")
        self.setModal(True)
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # View selector
        layout.addWidget(QLabel("View plane:"))
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Axial", "Coronal", "Sagittal"])
        layout.addWidget(self.view_combo)

        # Slice range
        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("Start:"))
        self.start_spin = QSpinBox()
        self.start_spin.setRange(0, max_slices - 1)
        self.start_spin.setValue(0)
        range_row.addWidget(self.start_spin)

        range_row.addWidget(QLabel("End:"))
        self.end_spin = QSpinBox()
        self.end_spin.setRange(0, max_slices - 1)
        self.end_spin.setValue(max_slices - 1)
        range_row.addWidget(self.end_spin)
        layout.addLayout(range_row)

        # Step
        step_row = QHBoxLayout()
        step_row.addWidget(QLabel("Export every N slices:"))
        self.step_spin = QSpinBox()
        self.step_spin.setRange(1, 50)
        self.step_spin.setValue(1)
        step_row.addWidget(self.step_spin)
        layout.addLayout(step_row)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_parameters(self) -> dict:
        return {
            "view":  self.view_combo.currentText(),
            "start": self.start_spin.value(),
            "end":   self.end_spin.value(),
            "step":  self.step_spin.value(),
        }
