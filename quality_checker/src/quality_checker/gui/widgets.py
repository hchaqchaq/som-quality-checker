from __future__ import annotations

from typing import cast

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPixmap, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QBoxLayout,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QListWidget,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..application import APP_LOGO_PATH


class CheckableComboBox(QComboBox):
    def __init__(self, placeholder: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModel(QStandardItemModel(self))
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText(placeholder)
        self._keep_popup_open = False
        self.view().pressed.connect(self._toggle_item)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def hidePopup(self) -> None:
        if self._keep_popup_open:
            self._keep_popup_open = False
            return
        super().hidePopup()

    def set_values(self, values: list[str]) -> None:
        model = cast(QStandardItemModel, self.model())
        model.clear()
        self._append_item("All", None, checked=True)
        for value in values:
            self._append_item(value, value, checked=False)
        self.setEnabled(True)
        self._update_display_text()

    def reset(self, message: str) -> None:
        model = cast(QStandardItemModel, self.model())
        model.clear()
        self._append_item(message, None, checked=False, checkable=False)
        self.setEnabled(False)
        self.lineEdit().setText(message)

    def checked_values(self) -> list[str]:
        model = cast(QStandardItemModel, self.model())
        selected: list[str] = []
        for row in range(model.rowCount()):
            item = model.item(row)
            if item.data(Qt.ItemDataRole.UserRole) is None:
                continue
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(str(item.data(Qt.ItemDataRole.UserRole)))
        return selected

    def has_loaded_values(self) -> bool:
        model = cast(QStandardItemModel, self.model())
        return model.rowCount() > 0 and model.item(0).text() == "All"

    def _append_item(
        self,
        text: str,
        value: str | None,
        checked: bool,
        checkable: bool = True,
    ) -> None:
        item = QStandardItem(text)
        flags = Qt.ItemFlag.ItemIsEnabled
        if checkable:
            flags |= Qt.ItemFlag.ItemIsUserCheckable
        item.setFlags(flags)
        item.setData(value, Qt.ItemDataRole.UserRole)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        cast(QStandardItemModel, self.model()).appendRow(item)

    def _toggle_item(self, index) -> None:
        item = cast(QStandardItemModel, self.model()).itemFromIndex(index)
        if not item or not item.isCheckable():
            return

        self._keep_popup_open = True
        next_state = (
            Qt.CheckState.Unchecked
            if item.checkState() == Qt.CheckState.Checked
            else Qt.CheckState.Checked
        )
        item.setCheckState(next_state)
        self._sync_all_item(item)
        self._update_display_text()

    def _sync_all_item(self, changed_item: QStandardItem) -> None:
        model = cast(QStandardItemModel, self.model())
        all_item = model.item(0)
        if changed_item is all_item and changed_item.checkState() == Qt.CheckState.Checked:
            for row in range(1, model.rowCount()):
                model.item(row).setCheckState(Qt.CheckState.Unchecked)
            return

        if changed_item is not all_item and changed_item.checkState() == Qt.CheckState.Checked:
            all_item.setCheckState(Qt.CheckState.Unchecked)
            return

        any_checked = any(
            model.item(row).checkState() == Qt.CheckState.Checked
            for row in range(1, model.rowCount())
        )
        if not any_checked:
            all_item.setCheckState(Qt.CheckState.Checked)

    def _update_display_text(self) -> None:
        values = self.checked_values()
        if not values:
            self.lineEdit().setText("All")
            return
        if len(values) <= 2:
            self.lineEdit().setText(", ".join(values))
            return
        self.lineEdit().setText(f"{len(values)} selected")


class ResponsiveColumns(QWidget):
    def __init__(
        self,
        left: QWidget,
        right: QWidget,
        breakpoint: int = 900,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.breakpoint = breakpoint
        layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        left.setMinimumWidth(0)
        right.setMinimumWidth(0)
        layout.addWidget(left, 3)
        layout.addWidget(right, 2)

    def minimumSizeHint(self) -> QSize:
        return QSize(0, 0)

    def resizeEvent(self, event) -> None:
        direction = (
            QBoxLayout.Direction.TopToBottom
            if event.size().width() < self.breakpoint
            else QBoxLayout.Direction.LeftToRight
        )
        cast(QBoxLayout, self.layout()).setDirection(direction)
        super().resizeEvent(event)


def _create_section_card(title: str, hint: str) -> QFrame:
    card = QFrame()
    card.setObjectName("sectionPanel")
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(14, 14, 14, 14)
    card_layout.setSpacing(8)

    title_label = QLabel(title)
    title_label.setObjectName("sectionTitle")
    hint_label = QLabel(hint)
    hint_label.setObjectName("sectionHint")
    hint_label.setWordWrap(True)
    card_layout.addWidget(title_label)
    card_layout.addWidget(hint_label)
    return card


def _create_sidebar(
    title: str,
    menu_items: tuple[str, ...] = ("Analysis", "History"),
) -> tuple[QFrame, QListWidget, QPushButton]:
    sidebar = QFrame()
    sidebar.setObjectName("sidebarPanel")
    layout = QVBoxLayout(sidebar)
    layout.setContentsMargins(12, 14, 12, 14)
    layout.setSpacing(10)

    if APP_LOGO_PATH.exists():
        logo_frame = QFrame()
        logo_frame.setObjectName("sidebarLogoFrame")
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(10, 10, 10, 10)
        logo_layout.setSpacing(0)
        logo = QLabel()
        logo.setObjectName("sidebarLogo")
        logo.setPixmap(
            QPixmap(str(APP_LOGO_PATH)).scaled(
                126,
                126,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        logo.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        logo_layout.addWidget(logo)
        layout.addWidget(logo_frame)

    title_label = QLabel(title)
    title_label.setObjectName("sidebarTitle")
    title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    layout.addWidget(title_label)

    menu = QListWidget()
    menu.addItems(menu_items)
    menu.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    menu.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    layout.addWidget(menu, 1)

    back_button = QPushButton("Switch checker")
    back_button.setObjectName("quietButton")
    layout.addWidget(back_button)

    content_width = max(
        title_label.sizeHint().width(),
        menu.sizeHintForColumn(0) + 34,
        back_button.sizeHint().width(),
        146,
    )
    menu.setFixedWidth(content_width)
    sidebar.setFixedWidth(
        content_width + layout.contentsMargins().left() + layout.contentsMargins().right()
    )
    return sidebar, menu, back_button


def _wrap_page(page: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setWidget(page)
    return scroll


def _create_workspace_header(checker: str) -> tuple[QFrame, QLabel, QLabel]:
    header = QFrame()
    header.setObjectName("workspaceHeader")
    layout = QHBoxLayout(header)
    layout.setContentsMargins(18, 14, 18, 14)
    layout.setSpacing(10)

    title = QLabel(checker)
    title.setObjectName("workspaceTitle")
    destination = QLabel("Analysis")
    destination.setObjectName("supportingText")
    state = QLabel("Ready")
    state.setObjectName("statusNeutral")

    layout.addWidget(title)
    layout.addWidget(destination)
    layout.addStretch(1)
    layout.addWidget(state)
    return header, destination, state


def _create_checker_shell(
    title: str,
    analysis_page: QWidget,
    history_page: QWidget,
    settings_page: QWidget | None = None,
) -> tuple[QWidget, QListWidget, QStackedWidget, QPushButton, QLabel, QLabel]:
    shell = QWidget()
    shell_layout = QHBoxLayout(shell)
    shell_layout.setContentsMargins(0, 0, 0, 0)
    shell_layout.setSpacing(14)

    menu_items = (
        ("Analysis", "History", "Settings")
        if settings_page is not None
        else ("Analysis", "History")
    )
    sidebar, menu, back_button = _create_sidebar(title, menu_items)
    shell_layout.addWidget(sidebar)

    content = QWidget()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(12)
    header, destination, state = _create_workspace_header(title)
    content_layout.addWidget(header)

    pages = QStackedWidget()
    pages.setObjectName("pageSurface")
    pages.addWidget(_wrap_page(analysis_page))
    pages.addWidget(_wrap_page(history_page))
    if settings_page is not None:
        pages.addWidget(_wrap_page(settings_page))
    content_layout.addWidget(pages)
    shell_layout.addWidget(content)
    shell_layout.setStretch(0, 0)
    shell_layout.setStretch(1, 1)
    return shell, menu, pages, back_button, destination, state
