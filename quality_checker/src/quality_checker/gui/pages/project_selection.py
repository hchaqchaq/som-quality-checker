from __future__ import annotations

from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..app import QualityCheckerController


class ProjectSelectionPage(QWidget):
    def __init__(self, controller: QualityCheckerController) -> None:
        super().__init__()
        self.setObjectName("projectLaunch")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(36)

        identity = QVBoxLayout()
        identity.addStretch(1)
        title = QLabel("Quality Checker")
        title.setObjectName("pageTitle")
        purpose = QLabel("Select a checker to assess workbook quality and review analysis history.")
        purpose.setObjectName("supportingText")
        purpose.setWordWrap(True)
        purpose.setMaximumWidth(380)
        identity.addWidget(title)
        identity.addWidget(purpose)
        identity.addStretch(1)
        layout.addLayout(identity, 2)

        choices = QVBoxLayout()
        choices.setSpacing(16)

        som_panel = QFrame()
        som_panel.setObjectName("projectChoicePanel")
        som_layout = QVBoxLayout(som_panel)
        som_layout.setContentsMargins(22, 22, 22, 22)
        som_layout.setSpacing(10)
        self.som_button = QPushButton("Open SOM checker")
        self.som_button.setObjectName("projectChoice")
        self.som_description = QLabel(
            "SOM analysis applies selected scope filters, reports validation failures, and exports an analysis workbook."
        )
        self.som_description.setObjectName("supportingText")
        self.som_description.setWordWrap(True)
        self.som_recent = QLabel(self._recent_text(controller.history_runs("SOM")))
        self.som_recent.setObjectName("supportingText")
        som_layout.addWidget(self.som_button)
        som_layout.addWidget(self.som_description)
        som_layout.addWidget(self.som_recent)

        edct_panel = QFrame()
        edct_panel.setObjectName("projectChoicePanel")
        edct_layout = QVBoxLayout(edct_panel)
        edct_layout.setContentsMargins(22, 22, 22, 22)
        edct_layout.setSpacing(10)
        self.edct_button = QPushButton("Open eDCT checker")
        self.edct_button.setObjectName("projectChoice")
        self.edct_description = QLabel(
            "eDCT analysis validates Supplier Level and PN Level rows, reports failures, "
            "and exports a preserved workbook copy."
        )
        self.edct_description.setObjectName("supportingText")
        self.edct_description.setWordWrap(True)
        self.edct_recent = QLabel(self._recent_text(controller.history_runs("eDCT")))
        self.edct_recent.setObjectName("supportingText")
        edct_layout.addWidget(self.edct_button)
        edct_layout.addWidget(self.edct_description)
        edct_layout.addWidget(self.edct_recent)

        choices.addStretch(1)
        choices.addWidget(som_panel)
        choices.addWidget(edct_panel)
        choices.addStretch(1)
        layout.addLayout(choices, 3)

    @staticmethod
    def _recent_text(rows) -> str:
        if not rows:
            return "No analysis runs yet"
        return f"Latest run: {rows[0]['started_at']}"
