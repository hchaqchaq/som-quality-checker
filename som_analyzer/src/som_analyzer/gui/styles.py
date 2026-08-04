from __future__ import annotations

FONT_FAMILY = "'Segoe UI', Arial, sans-serif"

COLORS = {
    "canvas": "#f4f7f8",
    "surface": "#fbfcfc",
    "surface_muted": "#edf2f3",
    "navigation": "#172326",
    "navigation_hover": "#233337",
    "text": "#182326",
    "text_muted": "#526267",
    "border": "#ccd7d9",
    "accent": "#0f766e",
    "accent_hover": "#0b5f59",
    "accent_soft": "#d9efec",
    "success": "#217a4b",
    "warning": "#9a5b00",
    "danger": "#b42318",
}

APP_STYLESHEET = f"""
QMainWindow,
QWidget {{
    background-color: {COLORS["canvas"]};
    color: {COLORS["text"]};
    font-family: {FONT_FAMILY};
    font-size: 14px;
}}

QWidget#appShell,
QWidget#projectLaunch {{
    background-color: {COLORS["canvas"]};
}}

QWidget#pageSurface,
QFrame#projectChoicePanel,
QFrame#workspaceHeader,
QFrame#sectionPanel,
QWidget#sectionCard {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 14px;
}}

QScrollArea,
QScrollArea > QWidget > QWidget {{
    background-color: transparent;
    border: 0;
}}

QWidget#sidebarPanel,
QWidget#heroPanel {{
    background-color: {COLORS["navigation"]};
    border-radius: 14px;
}}

QWidget#heroPanel QLabel {{
    background: transparent;
    color: {COLORS["surface"]};
}}

QWidget#sidebarLogoFrame {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 14px;
}}

QLabel,
QLabel#sidebarLogo {{
    background: transparent;
    color: {COLORS["text"]};
}}

QLabel#workspaceTitle,
QLabel#pageTitle {{
    font-size: 24px;
    font-weight: 600;
    color: {COLORS["text"]};
}}

QWidget#heroPanel QLabel#pageTitle {{
    color: {COLORS["surface"]};
}}

QLabel#pageSubtitle,
QLabel#supportingText,
QLabel#sectionHint {{
    color: {COLORS["text_muted"]};
}}

QWidget#heroPanel QLabel#pageSubtitle {{
    color: {COLORS["surface_muted"]};
}}

QLabel#sectionTitle {{
    font-size: 17px;
    font-weight: 600;
    color: {COLORS["text"]};
}}

QLabel#sidebarTitle {{
    color: {COLORS["surface"]};
    font-size: 17px;
    font-weight: 600;
}}

QLabel#emptyState {{
    color: {COLORS["text_muted"]};
    background-color: {COLORS["surface_muted"]};
    border-radius: 10px;
    padding: 14px;
}}

QLabel#statusNeutral,
QLabel#statusInfo,
QLabel#statusProgress,
QLabel#statusSuccess,
QLabel#statusError,
QLabel#statusWarning {{
    border-radius: 10px;
    padding: 10px 12px;
    font-weight: 600;
}}

QLabel#statusNeutral,
QLabel#statusInfo {{
    color: {COLORS["text"]};
    background-color: {COLORS["surface_muted"]};
    border: 1px solid {COLORS["border"]};
}}

QLabel#statusProgress {{
    color: {COLORS["accent_hover"]};
    background-color: {COLORS["accent_soft"]};
    border: 1px solid {COLORS["accent"]};
}}

QLabel#statusSuccess {{
    color: {COLORS["success"]};
    background-color: #e5f4eb;
    border: 1px solid {COLORS["success"]};
}}

QLabel#statusError,
QLabel#statusWarning {{
    color: {COLORS["danger"]};
    background-color: #fce8e6;
    border: 1px solid {COLORS["danger"]};
}}

QLineEdit,
QComboBox {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    padding: 9px 11px;
    color: {COLORS["text"]};
    selection-background-color: {COLORS["accent"]};
    selection-color: {COLORS["surface"]};
}}

QLineEdit:focus,
QComboBox:focus,
QComboBox:hover {{
    border: 2px solid {COLORS["accent"]};
}}

QLineEdit:read-only,
QComboBox:disabled {{
    background-color: {COLORS["surface_muted"]};
    color: {COLORS["text_muted"]};
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    color: {COLORS["text"]};
    selection-background-color: {COLORS["accent_soft"]};
    selection-color: {COLORS["text"]};
    outline: none;
}}

QListWidget {{
    background-color: transparent;
    border: 0;
    color: {COLORS["surface"]};
    padding: 8px 6px;
    outline: none;
    font-weight: 600;
}}

QListWidget::item {{
    background-color: transparent;
    border-radius: 10px;
    padding: 11px 12px;
    margin: 3px 0;
}}

QListWidget::item:hover {{
    background-color: {COLORS["navigation_hover"]};
}}

QListWidget::item:selected {{
    background-color: {COLORS["accent"]};
    color: {COLORS["surface"]};
}}

QPushButton {{
    background-color: {COLORS["surface_muted"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    padding: 10px 15px;
    font-weight: 600;
}}

QPushButton:hover {{
    border-color: {COLORS["accent"]};
    background-color: {COLORS["accent_soft"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["border"]};
}}

QPushButton:focus {{
    border: 2px solid {COLORS["accent"]};
}}

QPushButton:disabled {{
    background-color: {COLORS["surface_muted"]};
    color: #87969a;
    border-color: {COLORS["border"]};
}}

QPushButton#primaryButton,
QPushButton#accentButton,
QPushButton#projectChoice {{
    background-color: {COLORS["accent"]};
    color: {COLORS["surface"]};
    border-color: {COLORS["accent"]};
}}

QPushButton#primaryButton:hover,
QPushButton#accentButton:hover,
QPushButton#projectChoice:hover {{
    background-color: {COLORS["accent_hover"]};
}}

QPushButton#quietButton {{
    background-color: transparent;
    color: {COLORS["surface"]};
    border-color: #6f8084;
}}

QPushButton#dangerButton {{
    background-color: {COLORS["danger"]};
    color: {COLORS["surface"]};
    border-color: {COLORS["danger"]};
}}

QProgressBar {{
    background-color: {COLORS["surface_muted"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    min-height: 16px;
    text-align: center;
    color: {COLORS["text"]};
}}

QProgressBar::chunk {{
    background-color: {COLORS["accent"]};
    border-radius: 9px;
}}

QTableWidget {{
    background-color: {COLORS["surface"]};
    alternate-background-color: {COLORS["surface_muted"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    gridline-color: {COLORS["border"]};
    color: {COLORS["text"]};
}}

QTableWidget::item:selected {{
    background-color: {COLORS["accent_soft"]};
    color: {COLORS["text"]};
}}

QHeaderView::section {{
    background-color: {COLORS["navigation"]};
    color: {COLORS["surface"]};
    padding: 8px 10px;
    border: 0;
    font-size: 13px;
    font-weight: 600;
}}
"""
