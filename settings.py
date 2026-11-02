"""V Menu settings management and UI configuration dialog.

Provides persistent settings storage via Qt's QSettings under the 'v_menu'
namespace, avoiding external files and matching IngeTrazo's native settings
pattern.
"""

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

SETTING_SCALE_KEY = "v_menu/scale"
DEFAULT_SCALE_PERCENT = 100
MIN_SCALE_PERCENT = 50
MAX_SCALE_PERCENT = 150
STEP_SCALE_PERCENT = 5


def get_menu_scale() -> float:
    """Return the configured menu scale multiplier as a float (e.g. 1.0 = 100%)."""
    st = QSettings()
    val = st.value(SETTING_SCALE_KEY, DEFAULT_SCALE_PERCENT)
    try:
        pct = int(val)
        if MIN_SCALE_PERCENT <= pct <= MAX_SCALE_PERCENT:
            return pct / 100.0
    except (ValueError, TypeError):
        pass
    return DEFAULT_SCALE_PERCENT / 100.0


def set_menu_scale(percent: int):
    """Store the menu scale percentage into QSettings."""
    pct = max(MIN_SCALE_PERCENT, min(MAX_SCALE_PERCENT, int(percent)))
    st = QSettings()
    st.setValue(SETTING_SCALE_KEY, pct)


class VMenuSettingsDialog(QDialog):
    """Clean settings dialog allowing the user to adjust radial menu scale."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("V Menu Settings")
        self.setModal(True)
        self.setMinimumWidth(320)

        current_pct = int(round(get_menu_scale() * 100.0))

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        # Header / Description
        info_label = QLabel("Radial Menu Size:", self)
        font = info_label.font()
        font.setBold(True)
        info_label.setFont(font)
        layout.addWidget(info_label)

        # Slider + Value indicator
        slider_layout = QHBoxLayout()
        slider_layout.setSpacing(10)

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(MIN_SCALE_PERCENT, MAX_SCALE_PERCENT)
        self.slider.setSingleStep(STEP_SCALE_PERCENT)
        self.slider.setPageStep(10)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(25)
        self.slider.setValue(current_pct)

        self.value_label = QLabel(self)
        self.value_label.setFixedWidth(70)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._update_value_label(current_pct)

        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(self.value_label)
        layout.addLayout(slider_layout)

        # Reset button
        reset_layout = QHBoxLayout()
        self.reset_btn = QPushButton("Reset to 100%", self)
        self.reset_btn.setFixedWidth(110)
        self.reset_btn.clicked.connect(lambda: self.slider.setValue(DEFAULT_SCALE_PERCENT))
        reset_layout.addStretch()
        reset_layout.addWidget(self.reset_btn)
        layout.addLayout(reset_layout)

        # Dialog standard buttons (OK / Cancel)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self,
        )
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.slider.valueChanged.connect(self._update_value_label)

    def _update_value_label(self, val: int):
        if val == DEFAULT_SCALE_PERCENT:
            self.value_label.setText(f"{val}% (Def)")
        else:
            self.value_label.setText(f"{val}%")

    def _on_accept(self):
        set_menu_scale(self.slider.value())
        self.accept()


def open_settings_dialog(parent: QWidget = None):
    """Open modal settings dialog."""
    dlg = VMenuSettingsDialog(parent)
    return dlg.exec()

