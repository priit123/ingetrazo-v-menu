# SPDX-License-Identifier: GPL-3.0-or-later
# V Menu — Pie / Radial Menu for IngeTrazo
"""V Menu — Circular radial quick tool menu for IngeTrazo 3D CAD/BIM modeler.

Pressing 'V' opens a 10-slice circular radial menu directly under the cursor,
providing fast 1-click access to core modeling tools:
1. Push/Pull (P) - North (12:00)
2. Move (M)
3. Rotate (Q)
4. Scale (S)
5. Offset (F)
6. Delete (Del) - South (06:00)
7. Line (L)
8. Rectangle (R)
9. Circle (C)
10. Tape Measure (T)
"""
from __future__ import annotations

import logging
import math
from PySide6.QtCore import QEvent, QObject, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QTextEdit,
    QWidget,
)
from tools.base import Tool

log = logging.getLogger("ingetrazo.plugins.v_menu")

# =============================================================================
# Configuration: Radial Menu Tool List (10 Tools Clockwise from North)
# =============================================================================
PIE_ITEMS = [
    {
        "key": "pushpull",
        "name": "Push/Pull",
        "shortcut": "P",
        "desc": "Push or pull faces into 3D geometry",
    },
    {
        "key": "move",
        "name": "Move",
        "shortcut": "M",
        "desc": "Move selected geometry or objects",
    },
    {
        "key": "rotate",
        "name": "Rotate",
        "shortcut": "Q",
        "desc": "Rotate geometry around an axis",
    },
    {
        "key": "scale",
        "name": "Scale",
        "shortcut": "S",
        "desc": "Scale selected geometry",
    },
    {
        "key": "offset",
        "name": "Offset",
        "shortcut": "F",
        "desc": "Offset edges and contours",
    },
    {
        "key": "delete",
        "name": "Delete",
        "shortcut": "Del",
        "desc": "Delete selected entities",
        "is_action": True,
    },
    {
        "key": "line",
        "name": "Line",
        "shortcut": "L",
        "desc": "Draw straight lines and edges",
    },
    {
        "key": "rectangle",
        "name": "Rectangle",
        "shortcut": "R",
        "desc": "Draw planar rectangular faces",
    },
    {
        "key": "circle",
        "name": "Circle",
        "shortcut": "C",
        "desc": "Draw circular faces and polygons",
    },
    {
        "key": "tape",
        "name": "Tape Measure",
        "shortcut": "T",
        "desc": "Measure distances and create guides",
    },
]

# Visual sizing constants
INNER_RADIUS = 44.0      # Center dead-zone radius (pixels)
OUTER_RADIUS = 120.0     # Outer menu radius (pixels)
TOTAL_SIZE = int(OUTER_RADIUS * 2 + 30)  # Widget canvas size


# =============================================================================
# Theme-aware color palettes
# =============================================================================
def _is_dark_theme() -> bool:
    """Detect IngeTrazo's active theme via Qt application palette lightness.

    Works with IngeTrazo's live theme switching: Qt always updates its
    palette immediately when the user toggles dark / light mode.
    """
    app = QApplication.instance()
    if app is None:
        return True
    from PySide6.QtGui import QPalette
    bg = app.palette().color(QPalette.ColorRole.Window)
    return bg.lightness() < 128


# Dark theme — based on IngeTrazo panel bg #2E2E31, text #E0E0E0
_DARK_PALETTE: dict[str, QColor] = {
    "bg":         QColor(46, 46, 49, 220),    # Sector fill (#2E2E31)
    "center_bg":  QColor(30, 30, 33, 250),    # Center hub — slightly darker
    "border":     QColor(255, 255, 255, 25),  # Sector dividers
    "hover":      QColor(243, 115, 41, 230),  # IngeTrazo brand orange
    "text":       QColor(224, 224, 224),      # #E0E0E0
    "text_dim":   QColor(160, 160, 165),      # Dimmed secondary text
    "text_hover": QColor(255, 255, 255),      # Text on active orange sector
}

# Light theme — based on IngeTrazo panel bg #F3F3F3, text #14161A
_LIGHT_PALETTE: dict[str, QColor] = {
    "bg":         QColor(243, 243, 243, 220), # Sector fill (#F3F3F3)
    "center_bg":  QColor(219, 219, 219, 250), # Center hub (#DBDBDB)
    "border":     QColor(0, 0, 0, 40),        # Sector dividers
    "hover":      QColor(243, 115, 41, 230),  # IngeTrazo brand orange
    "text":       QColor(20, 22, 26),         # #14161A
    "text_dim":   QColor(80, 85, 95),         # Dimmed secondary text
    "text_hover": QColor(20, 22, 26),         # Dark text in light theme
}


def _get_palette() -> dict[str, QColor]:
    """Return the color palette matching the current IngeTrazo theme."""
    return _DARK_PALETTE if _is_dark_theme() else _LIGHT_PALETTE


# =============================================================================
# Delete Vector Icon & Generic Fallback
# =============================================================================
def _draw_delete_icon(painter: QPainter, center: QPointF, size: float, color: QColor):
    """Draw clean vector trash bin glyph for the Delete action."""
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    hs = size / 2.0
    rect = QRectF(center.x() - hs, center.y() - hs, size, size)

    pen = QPen(color, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    # Trash bin icon
    bx, by, bw, bh = rect.x() + 4, rect.y() + 6, rect.width() - 8, rect.height() - 7
    painter.drawLine(QPointF(rect.x() + 2, by), QPointF(rect.right() - 2, by))
    painter.drawLine(QPointF(center.x() - 3, by - 3), QPointF(center.x() + 3, by - 3))
    painter.drawRoundedRect(QRectF(bx, by, bw, bh), 2, 2)
    painter.drawLine(QPointF(center.x() - 2.5, by + 3), QPointF(center.x() - 2.5, by + bh - 3))
    painter.drawLine(QPointF(center.x() + 2.5, by + 3), QPointF(center.x() + 2.5, by + bh - 3))
    painter.restore()


def _draw_fallback_icon(painter: QPainter, center: QPointF, size: float, color: QColor):
    """Draw a minimal fallback dot if an application icon is unavailable."""
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(Qt.NoPen)
    painter.setBrush(color)
    painter.drawEllipse(center, size * 0.2, size * 0.2)
    painter.restore()


# =============================================================================
# Pie Menu Widget (Radial Menu)
# =============================================================================
class PieMenuWidget(QWidget):
    """Circular radial menu centered under cursor."""

    def __init__(self, main_window=None, items: list[dict] = None):
        if callable(main_window):
            main_window = main_window()
        if main_window is None:
            main_window = QApplication.activeWindow()

        super().__init__(main_window, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.win = main_window
        self.items = items or PIE_ITEMS
        self.num_items = len(self.items)
        self.slice_angle = 360.0 / max(1, self.num_items)

        self._hovered_index = -1
        self._icons: dict[str, QIcon] = {}

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setMouseTracking(True)
        self.resize(TOTAL_SIZE, TOTAL_SIZE)

        # Load native IngeTrazo icons
        self._load_app_icons()

    def _load_app_icons(self):
        """Retrieve official QIcons from IngeTrazo tool actions."""
        tool_actions = getattr(self.win, "_tool_actions", {}) or {}
        for item in self.items:
            key = item["key"]
            act = tool_actions.get(key)
            if act is not None and not act.icon().isNull():
                self._icons[key] = act.icon()

    def show_at_cursor(self):
        """Display menu centered exactly at current cursor coordinates."""
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x() - self.width() // 2, cursor_pos.y() - self.height() // 2)
        self._hovered_index = -1
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()
        self.grabMouse()

    # --- Event Handlers ---

    def mouseMoveEvent(self, event):
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        pos = event.position()
        dx = pos.x() - cx
        dy = pos.y() - cy
        dist = math.hypot(dx, dy)

        if dist < INNER_RADIUS or dist > (OUTER_RADIUS + 30.0):
            new_hover = -1
        else:
            # 0 degrees is North (Top), angle increases clockwise.
            deg = (math.degrees(math.atan2(dy, dx)) + 90.0) % 360.0
            # Slices are centered around their respective mid-angles.
            shifted = (deg + self.slice_angle / 2.0) % 360.0
            new_hover = int(shifted // self.slice_angle)
            if new_hover >= self.num_items:
                new_hover = self.num_items - 1

        if new_hover != self._hovered_index:
            self._hovered_index = new_hover
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            cx = self.width() / 2.0
            cy = self.height() / 2.0
            pos = event.position()
            dist = math.hypot(pos.x() - cx, pos.y() - cy)

            if dist < INNER_RADIUS:
                # Center click toggles Clean Screen (Fullscreen)
                self._trigger_clean_screen()
                self.close()
                return

            if 0 <= self._hovered_index < self.num_items:
                self._activate_item(self.items[self._hovered_index])
            self.close()
        elif event.button() == Qt.RightButton:
            # Right click cancels and closes menu
            self.close()

    def keyPressEvent(self, event):
        key = event.key()
        # Esc or V cancels and closes menu
        if key in (Qt.Key_Escape, Qt.Key_V):
            self.close()
            event.accept()
            return

        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.releaseMouse()
        super().closeEvent(event)

    # --- Tool Execution ---

    def _activate_item(self, item: dict):
        """Activate selected IngeTrazo tool or command."""
        key = item["key"]
        name = item["name"]

        # 1. Delete selection
        if key == "delete":
            fn = getattr(self.win, "_on_delete_selection", None)
            if callable(fn):
                fn()
            else:
                self.win.viewport.scene.delete_selection()
                self.win.viewport.update()
            self._flash(f"Deleted: {name}")
            return

        # 2. Standard interactive tools (Push/Pull, Move, Rotate, etc.)
        tool_actions = getattr(self.win, "_tool_actions", {}) or {}
        act = tool_actions.get(key)
        if act is not None:
            act.trigger()
            self._flash(f"Active tool: {name}")
            return

        # 3. Fallback: direct _activate_tool invocation
        fn = getattr(self.win, "_activate_tool", None)
        if callable(fn):
            fn(key)
            self._flash(f"Active tool: {name}")
        else:
            log.warning("Could not find tool with key: %s", key)

    def _trigger_clean_screen(self):
        """Toggle Clean Screen mode (AutoCAD/IngeTrazo Ctrl+0 full presentation view)."""
        clean_act = getattr(self.win, "_act_clean_screen", None)
        if clean_act is not None:
            clean_act.toggle()
            is_clean = clean_act.isChecked()
            self._flash(f"Clean Screen: {'ON' if is_clean else 'OFF'}")
            return

        # Fallback to direct method call if action not found
        fn = getattr(self.win, "_toggle_clean_screen", None)
        if callable(fn):
            current_state = bool(getattr(self.win, "_clean_screen_state", None))
            fn(not current_state)
            self._flash(f"Clean Screen: {'OFF' if current_state else 'ON'}")
        else:
            log.warning("Clean Screen action/method not found on MainWindow")

    def _flash(self, message: str):
        vp = getattr(self.win, "viewport", None)
        if vp and hasattr(vp, "flash_status"):
            vp.flash_status(message, 2500)
        else:
            sb = self.win.statusBar() if hasattr(self.win, "statusBar") else None
            if sb:
                sb.showMessage(message, 2500)

    # --- Visual Rendering (QPainter) ---

    def paintEvent(self, event):
        dark = _is_dark_theme()  # Resolve theme once per paint — used for palette + icon selection
        pal = _DARK_PALETTE if dark else _LIGHT_PALETTE
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        cx = self.width() / 2.0
        cy = self.height() / 2.0
        center = QPointF(cx, cy)

        # 1. Draw each sector wedge
        for i, item in enumerate(self.items):
            is_hover = (i == self._hovered_index)

            # Qt angle system: 0 is at 3 o'clock (East), positive is counter-clockwise.
            # Convert so 0 is North (Top), increasing clockwise:
            mid_deg = i * self.slice_angle
            start_deg_math = 90.0 - (mid_deg - self.slice_angle / 2.0)
            span_deg_math = -self.slice_angle

            # Sector geometry path
            path = QPainterPath()
            rect_out = QRectF(cx - OUTER_RADIUS, cy - OUTER_RADIUS, OUTER_RADIUS * 2, OUTER_RADIUS * 2)
            rect_in = QRectF(cx - INNER_RADIUS, cy - INNER_RADIUS, INNER_RADIUS * 2, INNER_RADIUS * 2)

            path.arcMoveTo(rect_out, start_deg_math)
            path.arcTo(rect_out, start_deg_math, span_deg_math)
            path.arcTo(rect_in, start_deg_math + span_deg_math, -span_deg_math)
            path.closeSubpath()

            # Fill and border
            if is_hover:
                painter.setPen(QPen(QColor(255, 255, 255, 120), 1.5))
                painter.setBrush(QBrush(pal["hover"]))
            else:
                painter.setPen(QPen(pal["border"], 1.0))
                painter.setBrush(QBrush(pal["bg"]))

            painter.drawPath(path)

            # Sector content — icon centred in the wedge (midpoint between inner and outer radius)
            rad = math.radians(mid_deg - 90.0)
            cos_rad = math.cos(rad)
            sin_rad = math.sin(rad)

            # Icon position: visual midpoint of the wedge band
            r_icon = (INNER_RADIUS + OUTER_RADIUS) / 2.0
            icon_cx = cx + r_icon * cos_rad
            icon_cy = cy + r_icon * sin_rad

            # Delete icon is drawn smaller
            icon_size = 18 if item["key"] == "delete" else 24.0
            icon_rect = QRectF(icon_cx - icon_size / 2.0, icon_cy - icon_size / 2.0, icon_size, icon_size)

            icon_color = pal["text_hover"] if is_hover else pal["text"]
            if item["key"] == "delete":
                _draw_delete_icon(painter, QPointF(icon_cx, icon_cy), icon_size, icon_color)
            else:
                icon = self._icons.get(item["key"])
                if icon and not icon.isNull():
                    icon.paint(painter, icon_rect.toRect(), Qt.AlignCenter)
                else:
                    _draw_fallback_icon(painter, QPointF(icon_cx, icon_cy), icon_size, icon_color)

        # 2. Center hub circle (clean, neutral border without highlight)
        painter.setPen(QPen(pal["border"], 1.5))
        painter.setBrush(QBrush(pal["center_bg"]))
        painter.drawEllipse(center, INNER_RADIUS, INNER_RADIUS)

        # 3. Center hub text
        if 0 <= self._hovered_index < self.num_items:
            active_item = self.items[self._hovered_index]
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.setPen(pal["text_hover"])
            painter.drawText(QRectF(cx - 40, cy - 14, 80, 14), Qt.AlignCenter, active_item["name"])

            painter.setFont(QFont("Segoe UI", 7))
            painter.setPen(QColor(243, 115, 41))
            painter.drawText(QRectF(cx - 40, cy + 1, 80, 14), Qt.AlignCenter, f"Key: {active_item['shortcut']}")
        else:
            # Default center text — immediate Clean Screen action hint
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.setPen(QColor(243, 115, 41))
            painter.drawText(QRectF(cx - 42, cy - 14, 84, 14), Qt.AlignCenter, "Clean Screen")

            painter.setFont(QFont("Segoe UI", 7))
            painter.setPen(pal["text_dim"])
            painter.drawText(QRectF(cx - 42, cy + 1, 84, 14), Qt.AlignCenter, "Ctrl+0")


# =============================================================================
# Keyboard Event Filter (Captures 'V' key reliably in 3D Viewport and Window)
# =============================================================================
class PieMenuKeyFilter(QObject):
    """Event filter intercepting 'V' keypresses without Qt shortcut clashes."""

    def __init__(self, win):
        super().__init__(win)
        self.win = win

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            txt = event.text().lower() if hasattr(event, "text") else ""

            # Check for 'V' keypress (both Qt.Key_V and char 'v')
            if (key == Qt.Key_V or txt == "v") and not event.isAutoRepeat():
                # Allow standard modifier combos (e.g. Ctrl+V paste)
                mods = event.modifiers()
                if mods & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier):
                    return False

                # Allow normal text typing when focused on input fields or VCB
                focus = QApplication.focusWidget()
                if focus is not None and isinstance(
                    focus, (QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox)
                ):
                    return False

                # Toggle menu closed if already open
                global _PIE_MENU_INSTANCE
                if _PIE_MENU_INSTANCE is not None and _PIE_MENU_INSTANCE.isVisible():
                    _PIE_MENU_INSTANCE.close()
                    return True

                show_pie_menu(self.win)
                return True

        return False


# =============================================================================
# Native Tool Class and Extension Entry Points
# =============================================================================
_PIE_MENU_INSTANCE: PieMenuWidget | None = None
_KEY_FILTER: PieMenuKeyFilter | None = None


def _get_or_create_pie_menu(win=None) -> PieMenuWidget:
    global _PIE_MENU_INSTANCE
    if callable(win):
        win = win()
    if win is None:
        win = QApplication.activeWindow()

    if _PIE_MENU_INSTANCE is None or _PIE_MENU_INSTANCE.win != win:
        _PIE_MENU_INSTANCE = PieMenuWidget(win, PIE_ITEMS)
    return _PIE_MENU_INSTANCE


def show_pie_menu(win=None):
    """Show Pie Menu at cursor."""
    try:
        menu = _get_or_create_pie_menu(win)
        menu.show_at_cursor()
    except Exception:
        log.exception("Error opening Pie Menu")


class VPieMenuTool(Tool):
    """Native IngeTrazo Tool class listed in Extensions menu."""

    name = "V Menu"
    # Shortcut is handled directly via PieMenuKeyFilter to prevent Qt shortcut ambiguity
    description = "Open radial tool menu under cursor [V]"

    def on_activate(self, viewport):
        win = viewport.window() if callable(getattr(viewport, "window", None)) else None
        show_pie_menu(win)

    def on_deactivate(self, viewport):
        pass


def setup(app):
    """Extension initialization hook. Installs global event filter."""
    global _KEY_FILTER
    win = app.window

    _KEY_FILTER = PieMenuKeyFilter(win)
    win._v_menu_key_filter = _KEY_FILTER

    # 1. Install filter on 3D Viewport
    vp = getattr(app, "viewport", None) or getattr(win, "viewport", None)
    if vp is not None:
        vp.installEventFilter(_KEY_FILTER)

    # 2. Install filter on main window and application event loop
    win.installEventFilter(_KEY_FILTER)
    q_app = QApplication.instance()
    if q_app is not None:
        q_app.installEventFilter(_KEY_FILTER)

    log.info("V Menu (Pie Menu) loaded successfully. Shortcut: 'V'.")
