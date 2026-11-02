"""V Menu settings management and UI configuration dialog.

Provides persistent settings storage via Qt's QSettings under the 'v_menu'
namespace, avoiding external files and matching IngeTrazo's native settings
pattern.
"""

from __future__ import annotations

import json
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

SETTING_SCALE_KEY = "v_menu/scale"
DEFAULT_SCALE_PERCENT = 100
MIN_SCALE_PERCENT = 50
MAX_SCALE_PERCENT = 150
STEP_SCALE_PERCENT = 5

SETTING_SLOTS_KEY = "v_menu/slots"

# =============================================================================
# Master Catalog of Available Tools (20 items)
# =============================================================================
TOOL_CATALOG: dict[str, dict] = {
    "pushpull": {
        "key": "pushpull",
        "name": "Push/Pull",
        "shortcut": "P",
        "qt_key": Qt.Key_P,
        "modifiers": Qt.NoModifier,
        "desc": "Push or pull faces into 3D geometry",
    },
    "move": {
        "key": "move",
        "name": "Move",
        "shortcut": "M",
        "qt_key": Qt.Key_M,
        "modifiers": Qt.NoModifier,
        "desc": "Move selected geometry or objects",
    },
    "rotate": {
        "key": "rotate",
        "name": "Rotate",
        "shortcut": "Q",
        "qt_key": Qt.Key_Q,
        "modifiers": Qt.NoModifier,
        "desc": "Rotate geometry around an axis",
    },
    "scale": {
        "key": "scale",
        "name": "Scale",
        "shortcut": "S",
        "qt_key": Qt.Key_S,
        "modifiers": Qt.NoModifier,
        "desc": "Scale selected geometry",
    },
    "offset": {
        "key": "offset",
        "name": "Offset",
        "shortcut": "F",
        "qt_key": Qt.Key_F,
        "modifiers": Qt.NoModifier,
        "desc": "Offset edges and contours",
    },
    "delete": {
        "key": "delete",
        "name": "Delete",
        "shortcut": "Del",
        "qt_key": Qt.Key_Delete,
        "modifiers": Qt.NoModifier,
        "desc": "Delete selected entities",
    },
    "eraser": {
        "key": "eraser",
        "name": "Eraser",
        "shortcut": "E",
        "qt_key": Qt.Key_E,
        "modifiers": Qt.NoModifier,
        "desc": "Erase edges or entities by clicking or dragging",
    },
    "line": {
        "key": "line",
        "name": "Line",
        "shortcut": "L",
        "qt_key": Qt.Key_L,
        "modifiers": Qt.NoModifier,
        "desc": "Draw straight lines and edges",
    },
    "rectangle": {
        "key": "rectangle",
        "name": "Rectangle",
        "shortcut": "R",
        "qt_key": Qt.Key_R,
        "modifiers": Qt.NoModifier,
        "desc": "Draw planar rectangular faces",
    },
    "circle": {
        "key": "circle",
        "name": "Circle",
        "shortcut": "C",
        "qt_key": Qt.Key_C,
        "modifiers": Qt.NoModifier,
        "desc": "Draw circular faces and polygons",
    },
    "tape": {
        "key": "tape",
        "name": "Tape Measure",
        "shortcut": "T",
        "qt_key": Qt.Key_T,
        "modifiers": Qt.NoModifier,
        "desc": "Measure distances and create guides",
    },
    "dimension": {
        "key": "dimension",
        "name": "Dimension",
        "shortcut": "D",
        "qt_key": Qt.Key_D,
        "modifiers": Qt.NoModifier,
        "desc": "Add linear dimension measurements",
    },
    "arc": {
        "key": "arc",
        "name": "Arc",
        "shortcut": "A",
        "qt_key": Qt.Key_A,
        "modifiers": Qt.NoModifier,
        "desc": "Draw 2-point circular arcs",
    },
    "paint": {
        "key": "paint",
        "name": "Paint / Material",
        "shortcut": "B",
        "qt_key": Qt.Key_B,
        "modifiers": Qt.NoModifier,
        "desc": "Apply colors and materials to faces",
    },
    "arc3": {
        "key": "arc3",
        "name": "3-Point Arc",
        "shortcut": "J",
        "qt_key": Qt.Key_J,
        "modifiers": Qt.NoModifier,
        "desc": "Draw 3-point circular arcs",
    },
    "center_arc": {
        "key": "center_arc",
        "name": "Center Arc",
        "shortcut": "Shift+O",
        "qt_key": Qt.Key_O,
        "modifiers": Qt.ShiftModifier,
        "desc": "Draw arcs from center point",
    },
    "protractor": {
        "key": "protractor",
        "name": "Protractor",
        "shortcut": "Shift+H",
        "qt_key": Qt.Key_H,
        "modifiers": Qt.ShiftModifier,
        "desc": "Measure angles and create angled guides",
    },
    "text": {
        "key": "text",
        "name": "Text",
        "shortcut": "X",
        "qt_key": Qt.Key_X,
        "modifiers": Qt.NoModifier,
        "desc": "Create text notes and leader labels",
    },
    "geopath": {
        "key": "geopath",
        "name": "Path",
        "shortcut": "Y",
        "qt_key": Qt.Key_Y,
        "modifiers": Qt.NoModifier,
        "desc": "Draw georeferenced path lines",
    },
    "orbit": {
        "key": "orbit",
        "name": "Orbit",
        "shortcut": "O",
        "qt_key": Qt.Key_O,
        "modifiers": Qt.NoModifier,
        "desc": "Rotate the camera view around the model",
    },
    "pan": {
        "key": "pan",
        "name": "Pan",
        "shortcut": "H",
        "qt_key": Qt.Key_H,
        "modifiers": Qt.NoModifier,
        "desc": "Slide camera view horizontally and vertically",
    },
}

DEFAULT_SLOTS = [
    "pushpull",
    "move",
    "rotate",
    "scale",
    "offset",
    "delete",
    "line",
    "rectangle",
    "circle",
    "tape",
]

NUM_SLOTS = 10


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


def get_menu_slots() -> list[str]:
    """Return the list of 10 configured tool keys for the radial menu."""
    st = QSettings()
    raw = st.value(SETTING_SLOTS_KEY, None)
    if raw:
        try:
            if isinstance(raw, str):
                slots = json.loads(raw)
            elif isinstance(raw, list):
                slots = list(raw)
            else:
                slots = []

            if isinstance(slots, list) and len(slots) == NUM_SLOTS:
                valid = [k for k in slots if k in TOOL_CATALOG]
                if len(valid) == NUM_SLOTS:
                    return valid
        except Exception:
            pass
    return list(DEFAULT_SLOTS)


def set_menu_slots(slots: list[str]):
    """Store the 10 tool keys for the radial menu into QSettings."""
    if len(slots) == NUM_SLOTS:
        st = QSettings()
        st.setValue(SETTING_SLOTS_KEY, json.dumps(slots))


def get_pie_items() -> list[dict]:
    """Return the resolved list of tool item dictionaries for the pie menu."""
    slot_keys = get_menu_slots()
    items = []
    for key in slot_keys:
        if key in TOOL_CATALOG:
            items.append(TOOL_CATALOG[key])
        else:
            items.append(TOOL_CATALOG["pushpull"])
    return items


class VMenuSettingsDialog(QDialog):
    """Clean settings dialog allowing the user to configure scale and menu slots."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("V Menu Settings")
        self.setModal(True)
        self.setMinimumWidth(380)

        current_pct = int(round(get_menu_scale() * 100.0))
        current_slots = get_menu_slots()

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(18, 18, 18, 18)

        # ---------------------------------------------------------------------
        # Section 1: Radial Menu Size
        # ---------------------------------------------------------------------
        size_group = QGroupBox("Menu Size", self)
        size_layout = QVBoxLayout(size_group)
        size_layout.setSpacing(10)

        slider_layout = QHBoxLayout()
        slider_layout.setSpacing(10)

        self.slider = QSlider(Qt.Horizontal, size_group)
        self.slider.setRange(MIN_SCALE_PERCENT, MAX_SCALE_PERCENT)
        self.slider.setSingleStep(STEP_SCALE_PERCENT)
        self.slider.setPageStep(10)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(25)
        self.slider.setValue(current_pct)

        self.value_label = QLabel(size_group)
        self.value_label.setFixedWidth(70)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._update_value_label(current_pct)

        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(self.value_label)
        size_layout.addLayout(slider_layout)

        reset_size_layout = QHBoxLayout()
        self.reset_size_btn = QPushButton("Reset to 100%", size_group)
        self.reset_size_btn.setFixedWidth(110)
        self.reset_size_btn.clicked.connect(lambda: self.slider.setValue(DEFAULT_SCALE_PERCENT))
        reset_size_layout.addStretch()
        reset_size_layout.addWidget(self.reset_size_btn)
        size_layout.addLayout(reset_size_layout)

        self.slider.valueChanged.connect(self._update_value_label)
        main_layout.addWidget(size_group)

        # ---------------------------------------------------------------------
        # Section 2: Slot Configuration (10 slots)
        # ---------------------------------------------------------------------
        slots_group = QGroupBox("Menu Slots (Clockwise from North)", self)
        slots_vbox = QVBoxLayout(slots_group)
        slots_vbox.setSpacing(8)

        # Scroll area in case screen height is limited
        scroll = QScrollArea(slots_group)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll_content = QWidget()
        form_layout = QFormLayout(scroll_content)
        form_layout.setSpacing(8)
        form_layout.setContentsMargins(4, 4, 4, 4)

        self.slot_combos: list[QComboBox] = []
        slot_descriptions = [
            "Slot 1 (12:00 North):",
            "Slot 2:",
            "Slot 3:",
            "Slot 4:",
            "Slot 5:",
            "Slot 6 (06:00 South):",
            "Slot 7:",
            "Slot 8:",
            "Slot 9:",
            "Slot 10:",
        ]

        for i in range(NUM_SLOTS):
            combo = QComboBox(scroll_content)
            for key, tool in TOOL_CATALOG.items():
                label = f"{tool['name']} ({tool['shortcut']})"
                combo.addItem(label, key)

            selected_key = current_slots[i] if i < len(current_slots) else DEFAULT_SLOTS[i]
            idx = combo.findData(selected_key)
            if idx >= 0:
                combo.setCurrentIndex(idx)

            form_layout.addRow(slot_descriptions[i], combo)
            self.slot_combos.append(combo)

        scroll.setWidget(scroll_content)
        slots_vbox.addWidget(scroll)

        reset_slots_layout = QHBoxLayout()
        self.reset_slots_btn = QPushButton("Reset Slots to Default", slots_group)
        self.reset_slots_btn.clicked.connect(self._reset_slots_to_default)
        reset_slots_layout.addStretch()
        reset_slots_layout.addWidget(self.reset_slots_btn)
        slots_vbox.addLayout(reset_slots_layout)

        main_layout.addWidget(slots_group)

        # ---------------------------------------------------------------------
        # Dialog standard buttons (OK / Cancel)
        # ---------------------------------------------------------------------
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self,
        )
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def _update_value_label(self, val: int):
        if val == DEFAULT_SCALE_PERCENT:
            self.value_label.setText(f"{val}% (Def)")
        else:
            self.value_label.setText(f"{val}%")

    def _reset_slots_to_default(self):
        for i, combo in enumerate(self.slot_combos):
            key = DEFAULT_SLOTS[i]
            idx = combo.findData(key)
            if idx >= 0:
                combo.setCurrentIndex(idx)

    def _on_accept(self):
        set_menu_scale(self.slider.value())
        selected_keys = [combo.currentData() for combo in self.slot_combos]
        set_menu_slots(selected_keys)
        self.accept()


def open_settings_dialog(parent: QWidget = None):
    """Open modal settings dialog."""
    dlg = VMenuSettingsDialog(parent)
    return dlg.exec()
