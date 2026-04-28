from __future__ import annotations

FONT_FAMILY = "'Roboto', 'Open Sans', Arial"

APP_STYLESHEET = f"""
QMainWindow {{
    background-color: #eef4ff;
}}

QWidget {{
    background-color: #eef4ff;
    color: #123f8c;
    font-family: {FONT_FAMILY};
    font-size: 14px;
}}

QWidget#appShell {{
    background-color: #eef4ff;
}}

QWidget#pageSurface {{
    background-color: #ffffff;
    border: 1px solid #c7d8f6;
    border-radius: 18px;
}}

QScrollArea {{
    background-color: transparent;
    border: 0;
}}

QScrollArea > QWidget > QWidget {{
    background-color: transparent;
}}

QWidget#sidebarPanel {{
    background-color: #123f8c;
    border-radius: 18px;
}}

QWidget#heroPanel {{
    background-color: #123f8c;
    border-radius: 16px;
}}

QWidget#heroPanel QLabel {{
    background: transparent;
    color: #ffffff;
}}

QWidget#sidebarLogoFrame {{
    background-color: #f8fbff;
    border: 1px solid #f0c23b;
    border-radius: 14px;
}}

QLabel#sidebarLogo {{
    background-color: transparent;
    padding: 0;
}}

QWidget#sectionCard {{
    background-color: #ffffff;
    border: 1px solid #d7e3f8;
    border-radius: 14px;
}}

QLabel {{
    background: transparent;
    color: #123f8c;
}}

QLabel#pageTitle {{
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
}}

QLabel#pageSubtitle {{
    font-size: 15px;
    color: #fff3c4;
}}

QLabel#sectionTitle {{
    font-size: 18px;
    font-weight: 700;
    color: #123f8c;
}}

QLabel#sectionHint {{
    font-size: 14px;
    color: #3d69b5;
}}

QLabel#statusInfo {{
    font-size: 14px;
    font-weight: 600;
    color: #123f8c;
    background-color: #f7fbff;
    border: 1px solid #cfe0fb;
    border-radius: 10px;
    padding: 10px 12px;
}}

QLabel#statusWarning {{
    font-size: 14px;
    font-weight: 600;
    color: #8a1f1f;
    background-color: #fff1f1;
    border: 1px solid #efb5b5;
    border-radius: 10px;
    padding: 10px 12px;
}}

QLineEdit {{
    background-color: #ffffff;
    border: 1px solid #b8cdee;
    border-radius: 10px;
    padding: 10px 12px;
    color: #123f8c;
    selection-background-color: #f0c23b;
}}

QLineEdit:read-only {{
    background-color: #f8fbff;
}}

QComboBox {{
    background-color: #ffffff;
    border: 1px solid #b8cdee;
    border-radius: 10px;
    padding: 9px 12px;
    color: #123f8c;
    selection-background-color: #f0c23b;
}}

QComboBox:hover {{
    border-color: #215fbe;
}}

QComboBox:disabled {{
    background-color: #f8fbff;
    color: #7f9dcc;
}}

QComboBox QAbstractItemView {{
    background-color: #ffffff;
    border: 1px solid #b8cdee;
    color: #123f8c;
    selection-background-color: #f0c23b;
    selection-color: #123f8c;
    outline: none;
}}

QListWidget {{
    background-color: transparent;
    border: 0;
    color: #ffffff;
    padding: 10px 8px;
    outline: none;
    font-size: 15px;
    font-weight: 600;
}}

QListWidget::item {{
    background-color: transparent;
    border-radius: 10px;
    padding: 12px 14px;
    margin: 4px 0;
}}

QListWidget::item:hover {{
    background-color: #1f57b5;
}}

QListWidget::item:selected {{
    background-color: #f0c23b;
    color: #123f8c;
}}

QPushButton {{
    background-color: #215fbe;
    color: #ffffff;
    border: 0;
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 700;
}}

QPushButton:hover {{
    background-color: #123f8c;
}}

QPushButton:pressed {{
    background-color: #0f3471;
}}

QPushButton:disabled {{
    background-color: #9bb7e8;
    color: #edf3ff;
}}

QPushButton#accentButton {{
    background-color: #f0c23b;
    color: #123f8c;
}}

QPushButton#accentButton:hover {{
    background-color: #ffd35f;
}}

QPushButton#dangerButton {{
    background-color: #cf3f3f;
    color: #ffffff;
}}

QPushButton#dangerButton:hover {{
    background-color: #b72d2d;
}}

QProgressBar {{
    background-color: #e3edfd;
    border: 1px solid #c5d7f3;
    border-radius: 8px;
    min-height: 16px;
    text-align: center;
    color: #123f8c;
}}

QProgressBar::chunk {{
    background-color: #f0c23b;
    border-radius: 7px;
}}

QTableWidget {{
    background-color: #ffffff;
    alternate-background-color: #f6f9ff;
    border: 1px solid #bfd3f0;
    border-radius: 12px;
    gridline-color: #d8e5f8;
    color: #123f8c;
    selection-background-color: #f0c23b;
    selection-color: #123f8c;
}}

QHeaderView::section {{
    background-color: #215fbe;
    color: #ffffff;
    padding: 8px 10px;
    border: 0;
    font-size: 13px;
    font-weight: 700;
}}
"""
