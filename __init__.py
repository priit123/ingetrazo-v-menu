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
from PySide6.QtCore import QEvent, QObject, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QCursor,
    QFont,
    QGuiApplication,
    QIcon,
    QKeyEvent,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPalette,
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

from .settings import get_menu_scale, open_settings_dialog

log = logging.getLogger("ingetrazo.plugins.v_menu")

# =============================================================================
# Configuration: Radial Menu Tool List (10 Tools Clockwise from North)
# =============================================================================
PIE_ITEMS = [
    {
        "key": "pushpull",
        "name": "Push/Pull",
        "shortcut": "P",
        "qt_key": Qt.Key_P,
        "desc": "Push or pull faces into 3D geometry",
    },
    {
        "key": "move",
        "name": "Move",
        "shortcut": "M",
        "qt_key": Qt.Key_M,
        "desc": "Move selected geometry or objects",
    },
    {
        "key": "rotate",
        "name": "Rotate",
        "shortcut": "Q",
        "qt_key": Qt.Key_Q,
        "desc": "Rotate geometry around an axis",
    },
    {
        "key": "scale",
        "name": "Scale",
        "shortcut": "S",
        "qt_key": Qt.Key_S,
        "desc": "Scale selected geometry",
    },
    {
        "key": "offset",
        "name": "Offset",
        "shortcut": "F",
        "qt_key": Qt.Key_F,
        "desc": "Offset edges and contours",
    },
    {
        "key": "delete",
        "name": "Delete",
        "shortcut": "Del",
        "qt_key": Qt.Key_Delete,
        "desc": "Delete selected entities",
    },
    {
        "key": "line",
        "name": "Line",
        "shortcut": "L",
        "qt_key": Qt.Key_L,
        "desc": "Draw straight lines and edges",
    },
    {
        "key": "rectangle",
        "name": "Rectangle",
        "shortcut": "R",
        "qt_key": Qt.Key_R,
        "desc": "Draw planar rectangular faces",
    },
    {
        "key": "circle",
        "name": "Circle",
        "shortcut": "C",
        "qt_key": Qt.Key_C,
        "desc": "Draw circular faces and polygons",
    },
    {
        "key": "tape",
        "name": "Tape Measure",
        "shortcut": "T",
        "qt_key": Qt.Key_T,
        "desc": "Measure distances and create guides",
    },
]

# Base sizing constants (at 100% scale)
BASE_INNER_RADIUS = 44.0      # Center dead-zone radius (pixels)
BASE_OUTER_RADIUS = 120.0     # Outer menu radius (pixels)
INNER_RADIUS = BASE_INNER_RADIUS
OUTER_RADIUS = BASE_OUTER_RADIUS
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
        self.scale_factor = 1.0
        self.inner_radius = BASE_INNER_RADIUS
        self.outer_radius = BASE_OUTER_RADIUS

        # Cached drawing resources & precomputed sector geometry
        self._cached_fonts = {}
        self._sector_paths: list[QPainterPath] = []
        self._icon_centers: list[QPointF] = []
        self._icon_rects: list[QRectF] = []

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setMouseTracking(True)

        # Precompute geometry & load icons
        self.apply_scale(get_menu_scale())
        self._load_app_icons()

    def apply_scale(self, scale: float):
        """Update geometry, fonts and canvas size based on scale multiplier."""
        self.scale_factor = max(0.5, min(2.0, float(scale)))
        self.inner_radius = BASE_INNER_RADIUS * self.scale_factor
        self.outer_radius = BASE_OUTER_RADIUS * self.scale_factor
        total_dim = int(round(self.outer_radius * 2 + 30.0 * self.scale_factor))
        self.resize(total_dim, total_dim)

        title_pt = max(6, int(round(8.0 * self.scale_factor)))
        sub_pt = max(5, int(round(7.0 * self.scale_factor)))
        self._cached_fonts = {
            "title": QFont("Segoe UI", title_pt, QFont.Bold),
            "sub": QFont("Segoe UI", sub_pt),
        }
        self._precompute_geometry()

    def _precompute_geometry(self):
        """Precompute QPainterPath sectors and icon positioning vectors."""
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        rect_out = QRectF(cx - self.outer_radius, cy - self.outer_radius, self.outer_radius * 2, self.outer_radius * 2)
        rect_in = QRectF(cx - self.inner_radius, cy - self.inner_radius, self.inner_radius * 2, self.inner_radius * 2)
        r_icon = (self.inner_radius + self.outer_radius) / 2.0

        self._sector_paths.clear()
        self._icon_centers.clear()
        self._icon_rects.clear()

        for i, item in enumerate(self.items):
            mid_deg = i * self.slice_angle
            start_deg_math = 90.0 - (mid_deg - self.slice_angle / 2.0)
            span_deg_math = -self.slice_angle

            # Sector geometry path
            path = QPainterPath()
            path.arcMoveTo(rect_out, start_deg_math)
            path.arcTo(rect_out, start_deg_math, span_deg_math)
            path.arcTo(rect_in, start_deg_math + span_deg_math, -span_deg_math)
            path.closeSubpath()
            self._sector_paths.append(path)

            # Icon center & bounding rect
            rad = math.radians(mid_deg - 90.0)
            icon_cx = cx + r_icon * math.cos(rad)
            icon_cy = cy + r_icon * math.sin(rad)
            center_pt = QPointF(icon_cx, icon_cy)
            self._icon_centers.append(center_pt)

            base_size = 18.0 if item["key"] == "delete" else 24.0
            icon_size = base_size * self.scale_factor
            rect = QRectF(icon_cx - icon_size / 2.0, icon_cy - icon_size / 2.0, icon_size, icon_size)
            self._icon_rects.append(rect)

    def _load_app_icons(self):
        """Retrieve official QIcons from IngeTrazo tool actions.

        NOTE: win._tool_actions is a private IngeTrazo internal used here
        only for icon loading. A public app.get_tool_icon() API has been
        requested in the IngeTrazo issue tracker. This call is read-only
        and fails silently — icons fall back to vector rendering if absent.
        """
        tool_actions = getattr(self.win, "_tool_actions", {}) or {}
        for item in self.items:
            key = item["key"]
            act = tool_actions.get(key)
            if act is not None and not act.icon().isNull():
                self._icons[key] = act.icon()

    def show_at_cursor(self):
        """Display menu centered exactly at current cursor coordinates, bounded to screen."""
        self.apply_scale(get_menu_scale())

        cursor_pos = QCursor.pos()
        target_x = cursor_pos.x() - self.width() // 2
        target_y = cursor_pos.y() - self.height() // 2

        # Keep menu fully within current screen bounds
        screen = QGuiApplication.screenAt(cursor_pos) or QGuiApplication.primaryScreen()
        if screen is not None:
            geo = screen.availableGeometry()
            target_x = max(geo.left(), min(target_x, geo.right() - self.width()))
            target_y = max(geo.top(), min(target_y, geo.bottom() - self.height()))

        self.move(target_x, target_y)
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

        if dist < self.inner_radius or dist > (self.outer_radius + 30.0 * self.scale_factor):
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

            if dist < self.inner_radius:
                # Center click toggles Clean Screen (Ctrl+0)
                self.close()
                QTimer.singleShot(0, self._trigger_clean_screen)
                return

            item_to_activate = None
            if 0 <= self._hovered_index < self.num_items:
                item_to_activate = self.items[self._hovered_index]

            # Close first so focus returns to the viewport before the key event
            self.close()
            if item_to_activate is not None:
                QTimer.singleShot(0, lambda: self._activate_item(item_to_activate))

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
        """Activate the selected tool using public Qt APIs.

        1. For 'delete', directly targets the viewport via Key_Delete.
        2. For regular tools, first attempts to trigger the corresponding QAction
           (works even when toolbars are hidden in Clean Screen mode).
        3. Falls back to sending simulated QKeyEvent if no matching QAction is found.
        """
        name = item["name"]
        qt_key = item["qt_key"]
        shortcut = item["shortcut"]

        vp = getattr(self.win, "viewport", None)

        if item.get("key") == "delete":
            # Delete is handled directly by Viewport's keyPressEvent
            target = vp if vp is not None else self.win
            if vp is not None and hasattr(vp, "setFocus"):
                vp.setFocus()
            press = QKeyEvent(QEvent.KeyPress, qt_key, Qt.NoModifier, "")
            release = QKeyEvent(QEvent.KeyRelease, qt_key, Qt.NoModifier, "")
            if target is not None:
                QApplication.sendEvent(target, press)
                QApplication.sendEvent(target, release)
            if vp is not None and hasattr(vp, "setFocus"):
                vp.setFocus()
            self._flash(f"Active tool: {name}")
            return

        # Public Qt API: find matching QAction on the main window by shortcut sequence.
        # This triggers successfully even when toolbars are hidden (Clean Screen mode).
        triggered = False
        if self.win is not None:
            target_seq = QKeySequence(qt_key)
            for act in self.win.findChildren(QAction):
                shortcuts = act.shortcuts()
                if (shortcuts and any(s == target_seq for s in shortcuts)) or act.shortcut() == target_seq:
                    act.trigger()
                    triggered = True
                    break

        if not triggered:
            # Fallback: simulate key press on window/viewport
            shortcut_text = shortcut if len(shortcut) == 1 else ""
            target = self.win if self.win is not None else vp
            press = QKeyEvent(QEvent.KeyPress, qt_key, Qt.NoModifier, shortcut_text)
            release = QKeyEvent(QEvent.KeyRelease, qt_key, Qt.NoModifier, shortcut_text)
            if target is not None:
                QApplication.sendEvent(target, press)
                QApplication.sendEvent(target, release)

        # Restore focus to viewport so modeling can continue immediately
        if vp is not None and hasattr(vp, "setFocus"):
            vp.setFocus()

        self._flash(f"Active tool: {name}")

    def _trigger_clean_screen(self):
        """Toggle Clean Screen via public QAction lookup or key simulation."""
        # 1. Preferred public Qt API: find Clean Screen QAction on the window
        if self.win:
            for action in self.win.actions():
                sc = action.shortcut().toString()
                text = action.text().lower()
                if sc in ("Ctrl+0", "Ctrl+Num+0") or "clean" in text:
                    action.trigger()
                    self._flash("Clean Screen toggled")
                    return

        # 2. Fallback: simulate Ctrl+0 key event
        press = QKeyEvent(QEvent.KeyPress, Qt.Key_0, Qt.ControlModifier, "0")
        release = QKeyEvent(QEvent.KeyRelease, Qt.Key_0, Qt.ControlModifier, "0")
        target = self.win if self.win else QApplication.activeWindow()
        if target:
            QApplication.sendEvent(target, press)
            QApplication.sendEvent(target, release)
            self._flash("Clean Screen toggled")

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

        # 1. Draw each sector wedge (using precomputed paths and geometries)
        pen_hover = QPen(QColor(255, 255, 255, 120), 1.5)
        pen_normal = QPen(pal["border"], 1.0)
        brush_hover = QBrush(pal["hover"])
        brush_normal = QBrush(pal["bg"])

        for i, item in enumerate(self.items):
            is_hover = (i == self._hovered_index)

            # Fill and border
            painter.setPen(pen_hover if is_hover else pen_normal)
            painter.setBrush(brush_hover if is_hover else brush_normal)
            painter.drawPath(self._sector_paths[i])

            # Sector content — icon using precomputed positions
            center_pt = self._icon_centers[i]
            icon_rect = self._icon_rects[i]
            icon_color = pal["text_hover"] if is_hover else pal["text"]

            if item["key"] == "delete":
                _draw_delete_icon(painter, center_pt, icon_rect.width(), icon_color)
            else:
                icon = self._icons.get(item["key"])
                if icon and not icon.isNull():
                    icon.paint(painter, icon_rect.toRect(), Qt.AlignCenter)
                else:
                    _draw_fallback_icon(painter, center_pt, icon_rect.width(), icon_color)

        # 2. Center hub circle (clean, neutral border without highlight)
        painter.setPen(QPen(pal["border"], 1.5))
        painter.setBrush(QBrush(pal["center_bg"]))
        painter.drawEllipse(center, self.inner_radius, self.inner_radius)

        # 3. Center hub text
        font_title = self._cached_fonts["title"]
        font_sub = self._cached_fonts["sub"]
        hw = self.inner_radius - 2.0
        text_rect_top = QRectF(cx - hw, cy - 14.0 * self.scale_factor, hw * 2, 14.0 * self.scale_factor)
        text_rect_bottom = QRectF(cx - hw, cy + 1.0 * self.scale_factor, hw * 2, 14.0 * self.scale_factor)

        if 0 <= self._hovered_index < self.num_items:
            active_item = self.items[self._hovered_index]
            painter.setFont(font_title)
            painter.setPen(pal["text_hover"])
            painter.drawText(text_rect_top, Qt.AlignCenter, active_item["name"])

            painter.setFont(font_sub)
            painter.setPen(QColor(243, 115, 41))
            painter.drawText(text_rect_bottom, Qt.AlignCenter, f"Key: {active_item['shortcut']}")
        else:
            # Default center text — immediate Clean Screen action hint
            painter.setFont(font_title)
            painter.setPen(QColor(243, 115, 41))
            painter.drawText(text_rect_top, Qt.AlignCenter, "Clean Screen")

            painter.setFont(font_sub)
            painter.setPen(pal["text_dim"])
            painter.drawText(text_rect_bottom, Qt.AlignCenter, "Ctrl+0")


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
_SETTINGS_ACTION: QAction | None = None


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
    """Extension initialization hook. Installs key event filter and settings menu action."""
    global _KEY_FILTER, _SETTINGS_ACTION
    win = app.window

    _KEY_FILTER = PieMenuKeyFilter(win)
    win._v_menu_key_filter = _KEY_FILTER

    # Install filter on the 3D viewport only — avoids capturing V across
    # the whole application and conflicting with other extensions.
    vp = getattr(app, "viewport", None) or getattr(win, "viewport", None)
    if vp is not None:
        vp.installEventFilter(_KEY_FILTER)
    else:
        # Viewport not available at load time — fall back to window scope
        win.installEventFilter(_KEY_FILTER)
        log.warning("V Menu: viewport not found; event filter installed on main window.")

    # Register Settings entry in Extensions menu
    try:
        if hasattr(app, "add_menu_action"):
            _SETTINGS_ACTION = app.add_menu_action(
                "V Menu Settings...",
                lambda: open_settings_dialog(win),
                tip="Configure radial menu scale and size",
            )
        elif hasattr(app, "add_menu"):
            menu = app.add_menu("V Menu")
            _SETTINGS_ACTION = menu.addAction("Settings...", lambda: open_settings_dialog(win))
    except Exception:
        log.exception("V Menu: failed to register Settings menu item")

    log.info("V Menu loaded. Press 'V' in the 3D viewport to open the menu.")


def teardown(app):
    """Extension teardown hook. Removes event filter, settings action and closes menu.

    Called by IngeTrazo when the extension is disabled or unloaded.
    Ensures no filter or state lingers until the next restart.
    """
    global _KEY_FILTER, _PIE_MENU_INSTANCE, _SETTINGS_ACTION
    win = app.window

    # Close menu immediately if it is open
    if _PIE_MENU_INSTANCE is not None:
        try:
            _PIE_MENU_INSTANCE.close()
        except RuntimeError:
            pass  # Widget already destroyed
        _PIE_MENU_INSTANCE = None

    # Remove settings menu action if registered
    if _SETTINGS_ACTION is not None:
        try:
            _SETTINGS_ACTION.deleteLater()
        except Exception:
            pass
        _SETTINGS_ACTION = None

    # Remove event filter from all possible targets (no-op if not installed)
    if _KEY_FILTER is not None:
        vp = getattr(app, "viewport", None) or getattr(win, "viewport", None)
        if vp is not None:
            vp.removeEventFilter(_KEY_FILTER)
        win.removeEventFilter(_KEY_FILTER)
        q_app = QApplication.instance()
        if q_app is not None:
            q_app.removeEventFilter(_KEY_FILTER)
        _KEY_FILTER = None

    # Remove the attribute that was stamped onto the window
    try:
        del win._v_menu_key_filter
    except AttributeError:
        pass

    log.info("V Menu unloaded.")
