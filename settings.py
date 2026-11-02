"""V Menu settings management and UI configuration dialog.

Provides persistent settings storage via Qt's QSettings under the 'v_menu'
namespace, avoiding external files and matching IngeTrazo's native settings
pattern.
"""

from __future__ import annotations

import json
from PySide6.QtCore import QPointF, QRectF, QSettings, QSize, Qt
from PySide6.QtGui import (
    QAction,
    QColor,
    QIcon,
    QKeySequence,
    QPainter,
    QPalette,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
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
# Master Catalog of Available Tools (21 items)
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
        "name": "Paint",
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


# In-memory cache to avoid querying QSettings on every 'V' keypress
_cached_scale: float | None = None
_cached_slots: list[str] | None = None


def get_menu_scale() -> float:
    """Return the configured menu scale multiplier as a float (e.g. 1.0 = 100%)."""
    global _cached_scale
    if _cached_scale is not None:
        return _cached_scale

    st = QSettings()
    val = st.value(SETTING_SCALE_KEY, DEFAULT_SCALE_PERCENT)
    try:
        pct = int(val)
        if MIN_SCALE_PERCENT <= pct <= MAX_SCALE_PERCENT:
            _cached_scale = pct / 100.0
            return _cached_scale
    except (ValueError, TypeError):
        pass
    _cached_scale = DEFAULT_SCALE_PERCENT / 100.0
    return _cached_scale


def set_menu_scale(percent: int):
    """Store the menu scale percentage into QSettings and update cache."""
    global _cached_scale
    pct = max(MIN_SCALE_PERCENT, min(MAX_SCALE_PERCENT, int(percent)))
    _cached_scale = pct / 100.0
    st = QSettings()
    st.setValue(SETTING_SCALE_KEY, pct)


def get_menu_slots() -> list[str]:
    """Return the list of 10 configured tool keys for the radial menu."""
    global _cached_slots
    if _cached_slots is not None:
        return list(_cached_slots)

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
                    _cached_slots = valid
                    return list(_cached_slots)
        except Exception:
            pass
    _cached_slots = list(DEFAULT_SLOTS)
    return list(_cached_slots)


def set_menu_slots(slots: list[str]):
    """Store the 10 tool keys for the radial menu into QSettings and update cache."""
    global _cached_slots
    if len(slots) == NUM_SLOTS:
        _cached_slots = list(slots)
        st = QSettings()
        st.setValue(SETTING_SLOTS_KEY, json.dumps(slots))


def get_pie_items() -> list[dict]:
    """Return the resolved list of tool item dictionaries for the pie menu."""
    return [TOOL_CATALOG[key] for key in get_menu_slots()]


def _make_delete_icon(size: int = 18) -> QIcon:
    """Create a theme-aware vector trash bin QIcon for the Delete tool in dropdowns."""
    app = QApplication.instance()
    dark = True
    if app is not None:
        bg = app.palette().color(QPalette.ColorRole.Window)
        dark = bg.lightness() < 128

    color = QColor(224, 224, 224) if dark else QColor(20, 22, 26)
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing, True)
    s = size / 18.0
    center = QPointF(size / 2.0, size / 2.0)
    rect = QRectF(0.0, 0.0, float(size), float(size))

    pen = QPen(color, max(1.0, 1.8 * s), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    bx = rect.x() + 4.0 * s
    by = rect.y() + 5.5 * s
    bw = rect.width() - 8.0 * s
    bh = rect.height() - 7.0 * s
    r_corner = 2.0 * s
    painter.drawLine(QPointF(rect.x() + 2.0 * s, by), QPointF(rect.right() - 2.0 * s, by))
    painter.drawLine(QPointF(center.x() - 2.5 * s, by - 2.5 * s), QPointF(center.x() + 2.5 * s, by - 2.5 * s))
    painter.drawRoundedRect(QRectF(bx, by, bw, bh), r_corner, r_corner)
    painter.drawLine(QPointF(center.x() - 2.0 * s, by + 2.5 * s), QPointF(center.x() - 2.0 * s, by + bh - 2.5 * s))
    painter.drawLine(QPointF(center.x() + 2.0 * s, by + 2.5 * s), QPointF(center.x() + 2.0 * s, by + bh - 2.5 * s))
    painter.end()
    return QIcon(pix)


def _resolve_catalog_icons(win: QWidget | None) -> dict[str, QIcon]:
    """Resolve QIcons for all tools in TOOL_CATALOG from the main window's QActions."""
    icons: dict[str, QIcon] = {"delete": _make_delete_icon(18)}
    if win is None:
        return icons

    all_actions = win.findChildren(QAction)
    by_seq: dict[QKeySequence, QAction] = {}
    for act in all_actions:
        for seq in act.shortcuts():
            if not seq.isEmpty() and seq not in by_seq:
                by_seq[seq] = act
        sc = act.shortcut()
        if not sc.isEmpty() and sc not in by_seq:
            by_seq[sc] = act

    tool_actions = getattr(win, "_tool_actions", {}) or {}
    nav_actions = getattr(win, "_nav_actions", {}) or {}

    for key, tool in TOOL_CATALOG.items():
        if key == "delete":
            continue
        shortcut = tool.get("shortcut")
        qt_key = tool.get("qt_key")
        target_seq = QKeySequence(shortcut) if shortcut else QKeySequence(qt_key)
        act = by_seq.get(target_seq)
        if act is None:
            act = tool_actions.get(key) or nav_actions.get(key)
        if act is not None and not act.icon().isNull():
            icons[key] = act.icon()

    return icons


class VMenuSettingsDialog(QDialog):
    """Clean settings dialog allowing the user to configure scale and menu slots."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("V Menu Settings")
        self.setModal(True)
        self.setMinimumWidth(380)

        current_pct = int(round(get_menu_scale() * 100.0))
        current_slots = get_menu_slots()
        catalog_icons = _resolve_catalog_icons(parent)

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

        self.slider.valueChanged.connect(self._on_slider_value_changed)
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
        self._slot_keys: list[str] = []
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
            combo.setIconSize(QSize(18, 18))
            for key, tool in TOOL_CATALOG.items():
                label = f"{tool['name']} ({tool['shortcut']})"
                icon = catalog_icons.get(key)
                if icon is not None:
                    combo.addItem(icon, label, key)
                else:
                    combo.addItem(label, key)

            selected_key = current_slots[i] if i < len(current_slots) else DEFAULT_SLOTS[i]
            idx = combo.findData(selected_key)
            if idx >= 0:
                combo.setCurrentIndex(idx)

            self._slot_keys.append(combo.currentData())
            combo.currentIndexChanged.connect(lambda _idx, slot_idx=i: self._on_slot_changed(slot_idx))

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

    def _on_slot_changed(self, changed_slot_idx: int):
        """Automatically swap tools if the user selects a tool already assigned to another slot."""
        combo = self.slot_combos[changed_slot_idx]
        new_key = combo.currentData()
        old_key = self._slot_keys[changed_slot_idx]
        if new_key == old_key:
            return

        for i, other_combo in enumerate(self.slot_combos):
            if i != changed_slot_idx and other_combo.currentData() == new_key:
                swap_idx = other_combo.findData(old_key)
                if swap_idx >= 0:
                    other_combo.blockSignals(True)
                    other_combo.setCurrentIndex(swap_idx)
                    other_combo.blockSignals(False)
                    self._slot_keys[i] = old_key
                break

        self._slot_keys[changed_slot_idx] = new_key

    def _on_slider_value_changed(self, val: int):
        """Snap slider value to STEP_SCALE_PERCENT (5%) increments even when dragging."""
        snapped = int(round(val / STEP_SCALE_PERCENT) * STEP_SCALE_PERCENT)
        snapped = max(MIN_SCALE_PERCENT, min(MAX_SCALE_PERCENT, snapped))
        if snapped != val:
            self.slider.blockSignals(True)
            self.slider.setValue(snapped)
            self.slider.blockSignals(False)
        self._update_value_label(snapped)

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
                combo.blockSignals(True)
                combo.setCurrentIndex(idx)
                combo.blockSignals(False)
            self._slot_keys[i] = combo.currentData()

    def _on_accept(self):
        set_menu_scale(self.slider.value())
        selected_keys = [combo.currentData() for combo in self.slot_combos]
        set_menu_slots(selected_keys)
        self.accept()


def open_settings_dialog(parent: QWidget = None):
    """Open modal settings dialog."""
    dlg = VMenuSettingsDialog(parent)
    return dlg.exec()
