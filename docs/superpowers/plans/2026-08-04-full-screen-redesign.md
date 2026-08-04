# Full-Screen Operational Workspace Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign every PyQt screen as one coherent operational workspace while preserving SOM and eDCT analysis, export, history, and worker-thread behavior.

**Architecture:** Keep the existing controller and analysis boundaries. Recompose `screens.py` with two small shared layout helpers, one responsive two-column widget, and existing PyQt controls; centralize the new visual language in `styles.py`. Extend the existing offscreen GUI test module so every behavioral layout change is driven by a focused failing test.

**Tech Stack:** Python 3.12+, PyQt6 6.7.1+, `unittest`, Qt stylesheets, pandas-backed existing analysis runtime.

## Global Constraints

- Preserve user-selected input and output paths.
- Preserve SOM filter semantics and eDCT workbook boundaries.
- Preserve `AnalysisWorker` plus `QThread`; no workbook work on the UI thread.
- Do not change validation, export, persistence, or database behavior.
- Use native `Segoe UI` with Windows-compatible fallbacks.
- Use deep graphite navigation, cool off-white surfaces, slate text, and one restrained teal accent.
- Use 10 px control radii and 14 px major-surface radii.
- Keep `DESIGN_VARIANCE: 4`, `MOTION_INTENSITY: 2`, and `VISUAL_DENSITY: 6`.
- No new dependency, animation framework, theme engine, dark-mode toggle, settings screen, or logo redesign.
- Keep visible copy aligned with `CONTEXT.md`: analysis run, assessed row, validation failure, Check, and Comment.
- Keep all unrelated working-tree changes untouched.

## File Map

- Modify `som_analyzer/src/som_analyzer/gui/styles.py`: semantic colors and complete Qt widget states.
- Modify `som_analyzer/src/som_analyzer/gui/screens.py`: launch screen, shared workspace shell, responsive analysis layouts, state presentation, and selection-driven history.
- Modify `som_analyzer/tests/test_gui_projects.py`: offscreen regression tests for the redesigned screens and preserved actions.
- Do not modify analysis, export, database, configuration, or workbook code.

---

### Task 1: Visual Tokens and Project Launch Screen

**Files:**

- Modify: `som_analyzer/src/som_analyzer/gui/styles.py:3-255`
- Modify: `som_analyzer/src/som_analyzer/gui/screens.py:231-247`
- Test: `som_analyzer/tests/test_gui_projects.py`

**Interfaces:**

- Consumes: `SomAnalyzeController.history_runs(project: str) -> Sequence[Mapping[str, object]]`.
- Produces: `ProjectSelectionPage(controller: SomAnalyzeController)`, `som_recent: QLabel`, `edct_recent: QLabel`, and semantic object names consumed by later screen tasks.

- [ ] **Step 1: Write failing launch-screen and theme tests**

Add imports and tests to `test_gui_projects.py`:

```python
from som_analyzer.gui.styles import APP_STYLESHEET, COLORS


def test_theme_uses_operational_palette(self) -> None:
    self.assertEqual(COLORS["accent"], "#0f766e")
    self.assertIn("'Segoe UI'", APP_STYLESHEET)
    self.assertIn("QPushButton:focus", APP_STYLESHEET)
    self.assertIn("QTableWidget::item:selected", APP_STYLESHEET)
    self.assertNotIn("#f0c23b", APP_STYLESHEET.lower())


def test_project_selection_explains_both_checkers(self) -> None:
    window = MainWindow(SomAnalyzeController())

    self.assertEqual(window.project_page.objectName(), "projectLaunch")
    self.assertEqual(window.project_page.som_button.objectName(), "projectChoice")
    self.assertEqual(window.project_page.edct_button.objectName(), "projectChoice")
    self.assertIn("SOM", window.project_page.som_description.text())
    self.assertIn("eDCT", window.project_page.edct_description.text())
    self.assertEqual(window.project_page.som_recent.text(), "No analysis runs yet")
    self.assertEqual(window.project_page.edct_recent.text(), "No analysis runs yet")
```

- [ ] **Step 2: Run the focused tests and confirm the intended failure**

Run from `som_analyzer/`:

```powershell
uv run python -m unittest discover -s tests -p test_gui_projects.py -k theme_uses_operational_palette -k project_selection_explains_both_checkers -v
```

Expected: FAIL because `COLORS`, the new object names, description labels, and recent-run labels do not exist.

- [ ] **Step 3: Replace the stylesheet with semantic tokens**

In `styles.py`, define one palette and interpolate it into the stylesheet:

```python
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
```

Build `APP_STYLESHEET` from those tokens. Cover these exact selectors and states:

```css
QWidget#appShell
QWidget#projectLaunch
QFrame#projectChoicePanel
QFrame#workspaceHeader
QFrame#sidebarPanel
QFrame#sectionPanel
QLabel#workspaceTitle
QLabel#pageTitle
QLabel#sectionTitle
QLabel#supportingText
QLabel#emptyState
QLabel#statusNeutral
QLabel#statusProgress
QLabel#statusSuccess
QLabel#statusError
QPushButton
QPushButton:hover
QPushButton:pressed
QPushButton:focus
QPushButton:disabled
QPushButton#primaryButton
QPushButton#quietButton
QPushButton#dangerButton
QPushButton#projectChoice
QLineEdit
QLineEdit:focus
QComboBox
QComboBox:focus
QListWidget::item
QListWidget::item:hover
QListWidget::item:selected
QTableWidget
QTableWidget::item:selected
QHeaderView::section
QProgressBar
QProgressBar::chunk
```

Use 14 px radii only on `projectChoicePanel`, `workspaceHeader`, and `sectionPanel`; use 10 px on buttons, line edits, combo boxes, progress bars, and status labels. Use teal for general focus and selection, red only for `dangerButton` and `statusError`, amber only for warnings, and green only for success.

- [ ] **Step 4: Recompose `ProjectSelectionPage` without changing its navigation signals**

Change the constructor to accept the controller and expose the existing buttons plus descriptive labels:

```python
class ProjectSelectionPage(QWidget):
    def __init__(self, controller: SomAnalyzeController) -> None:
        super().__init__()
        self.setObjectName("projectLaunch")

        self.som_button = QPushButton("Open SOM checker")
        self.som_button.setObjectName("projectChoice")
        self.som_description = QLabel(
            "Assess scoped SOM rows, review validation failures, and export an analysis workbook."
        )
        self.som_description.setWordWrap(True)
        self.som_description.setObjectName("supportingText")
        self.som_recent = QLabel(self._recent_text(controller.history_runs("SOM")))

        self.edct_button = QPushButton("Open eDCT checker")
        self.edct_button.setObjectName("projectChoice")
        self.edct_description = QLabel(
            "Validate Supplier Level rows, inspect failures, and export a preserved workbook copy."
        )
        self.edct_description.setWordWrap(True)
        self.edct_description.setObjectName("supportingText")
        self.edct_recent = QLabel(self._recent_text(controller.history_runs("eDCT")))

    @staticmethod
    def _recent_text(rows) -> str:
        if not rows:
            return "No analysis runs yet"
        latest = rows[0]
        return f"Latest run: {latest['started_at']}"
```

Lay out the identity block on the left and the two checker panels in a vertical stack on the right. At widths under the existing 980 px minimum, keep the panels readable by allowing descriptions to wrap; do not add a new responsive abstraction for this single screen.

Update `MainWindow` to instantiate `ProjectSelectionPage(controller)` and update the existing button-text assertions to `Open SOM checker` and `Open eDCT checker`.

- [ ] **Step 5: Run the launch-screen tests**

Run from `som_analyzer/`:

```powershell
uv run python -m unittest discover -s tests -p test_gui_projects.py -k theme_uses_operational_palette -k project_selection_explains_both_checkers -v
```

Expected: PASS.

- [ ] **Step 6: Commit the visual foundation**

```powershell
git add som_analyzer/src/som_analyzer/gui/styles.py som_analyzer/src/som_analyzer/gui/screens.py som_analyzer/tests/test_gui_projects.py
git commit -m "feat: redesign project launch and visual theme"
```

---

### Task 2: Shared Workspace Shell and Navigation

**Files:**

- Modify: `som_analyzer/src/som_analyzer/gui/screens.py:168-230,425-516`
- Test: `som_analyzer/tests/test_gui_projects.py`

**Interfaces:**

- Consumes: `ProjectSelectionPage(controller)`, existing `WelcomePage`, `EdctPage`, and `HistoryPage` widgets.
- Produces: `_create_workspace_header(checker: str) -> tuple[QFrame, QLabel, QLabel]`, `_create_checker_shell(title: str, analysis_page: QWidget, history_page: QWidget) -> tuple[QWidget, QListWidget, QStackedWidget, QPushButton, QLabel, QLabel]`, and existing public `MainWindow` attributes for SOM and eDCT.

- [ ] **Step 1: Write failing shared-shell tests**

Replace the old Welcome-label assertions and add:

```python
def test_both_checkers_use_the_shared_workspace_shell(self) -> None:
    window = MainWindow(SomAnalyzeController())

    for open_button, shell, menu, pages, destination in (
        (
            window.project_page.som_button,
            window.som_shell,
            window.menu,
            window.som_pages,
            window.som_destination_label,
        ),
        (
            window.project_page.edct_button,
            window.edct_shell,
            window.edct_menu,
            window.edct_pages,
            window.edct_destination_label,
        ),
    ):
        open_button.click()
        self.assertEqual(window.pages.currentWidget(), shell)
        self.assertEqual(
            [menu.item(index).text() for index in range(menu.count())],
            ["Analysis", "History"],
        )
        self.assertEqual(destination.text(), "Analysis")
        menu.setCurrentRow(1)
        self.assertEqual(pages.currentIndex(), 1)
        self.assertEqual(destination.text(), "History")


def test_switch_checker_returns_to_launch_screen(self) -> None:
    window = MainWindow(SomAnalyzeController())

    window.project_page.som_button.click()
    window.som_back_button.click()
    self.assertEqual(window.pages.currentWidget(), window.project_page)

    window.project_page.edct_button.click()
    window.edct_back_button.click()
    self.assertEqual(window.pages.currentWidget(), window.project_page)
```

- [ ] **Step 2: Run the shared-shell tests and confirm failure**

Run from `som_analyzer/`:

```powershell
uv run python -m unittest discover -s tests -p test_gui_projects.py -k both_checkers_use_the_shared_workspace_shell -k switch_checker_returns_to_launch_screen -v
```

Expected: FAIL because menus still say Welcome, destination labels do not exist, and the switch button has old copy.

- [ ] **Step 3: Replace duplicated shell construction with two small helpers**

Implement the header helper:

```python
def _create_workspace_header(checker: str) -> tuple[QFrame, QLabel, QLabel]:
    header = QFrame()
    header.setObjectName("workspaceHeader")
    title = QLabel(checker)
    title.setObjectName("workspaceTitle")
    destination = QLabel("Analysis")
    destination.setObjectName("supportingText")
    state = QLabel("Ready")
    state.setObjectName("statusNeutral")
    # Add title and destination at the left, state at the right.
    return header, destination, state
```

Move `MainWindow._wrap_page` to a module-level `_wrap_page(page: QWidget) -> QScrollArea` helper without changing its behavior. Implement `_create_checker_shell` by reusing `_create_sidebar`, `_create_workspace_header`, `_wrap_page`, and one `QStackedWidget`. Return the exact six objects named in Interfaces so `MainWindow` can retain stable attributes for tests and signals.

Change `_create_sidebar` to use:

```python
menu.addItems(("Analysis", "History"))
back_button = QPushButton("Switch checker")
back_button.setObjectName("quietButton")
```

Keep the logo, checker title, fixed sidebar width, and one-line menu items. Remove the old blue/yellow inline title color and let the stylesheet own it.

- [ ] **Step 4: Wire both shells in `MainWindow`**

Use `_create_checker_shell` twice and retain these attributes:

```python
self.som_shell
self.menu
self.som_pages
self.som_back_button
self.som_destination_label
self.som_state_label
self.edct_shell
self.edct_menu
self.edct_pages
self.edct_back_button
self.edct_destination_label
self.edct_state_label
```

In `_on_menu_changed` and `_on_edct_menu_changed`, set destination text from the selected menu item before refreshing History. Reset each menu to Analysis whenever its checker is opened.

- [ ] **Step 5: Run all navigation tests**

Run from `som_analyzer/`:

```powershell
uv run python -m unittest discover -s tests -p test_gui_projects.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit the shared shell**

```powershell
git add som_analyzer/src/som_analyzer/gui/screens.py som_analyzer/tests/test_gui_projects.py
git commit -m "feat: unify checker workspace navigation"
```

---

### Task 3: Responsive Analysis Workspace and Complete Run States

**Files:**

- Modify: `som_analyzer/src/som_analyzer/gui/screens.py:249-424,518-807`
- Test: `som_analyzer/tests/test_gui_projects.py`

**Interfaces:**

- Consumes: existing `_run_edct`, `_run_som`, `CheckableComboBox`, `AnalysisWorker`, and checker header state labels from Task 2.
- Produces: `ResponsiveColumns(left: QWidget, right: QWidget, breakpoint: int = 900)`, `status_changed = pyqtSignal(str)` on both analysis pages, `_update_run_enabled() -> None`, and semantic ready/loading/success/failure/empty states.

- [ ] **Step 1: Write failing responsive and readiness tests**

Add `QBoxLayout` to the test imports and add:

```python
def test_analysis_requires_input_and_output_before_run(self) -> None:
    window = MainWindow(SomAnalyzeController())

    for page in (window.welcome_page, window.edct_page):
        self.assertFalse(page.run_button.isEnabled())
        page.input_file.setText("C:/input.xlsx")
        self.assertFalse(page.run_button.isEnabled())
        page.output_dir.setText("C:/output")
        self.assertTrue(page.run_button.isEnabled())


def test_analysis_columns_collapse_at_narrow_width(self) -> None:
    window = MainWindow(SomAnalyzeController())

    columns = window.welcome_page.workspace_columns
    columns.resize(760, 500)
    self.app.processEvents()
    self.assertEqual(columns.layout().direction(), QBoxLayout.Direction.TopToBottom)

    columns.resize(1000, 500)
    self.app.processEvents()
    self.assertEqual(columns.layout().direction(), QBoxLayout.Direction.LeftToRight)


def test_analysis_pages_expose_empty_and_semantic_status_states(self) -> None:
    window = MainWindow(SomAnalyzeController())

    for page in (window.welcome_page, window.edct_page):
        self.assertEqual(page.status.objectName(), "statusNeutral")
        self.assertIn("after an analysis run", page.preview_empty.text())
        page._set_status("Analysis started", "progress")
        self.assertEqual(page.status.objectName(), "statusProgress")
        page._set_status("Analysis completed", "success")
        self.assertEqual(page.status.objectName(), "statusSuccess")
        page._set_status("Analysis failed", "error")
        self.assertEqual(page.status.objectName(), "statusError")
```

Use `_set_status` as the shared method name on both `WelcomePage` and `EdctPage`; rename the current eDCT direct assignments accordingly.

- [ ] **Step 2: Run the analysis-layout tests and confirm failure**

Run from `som_analyzer/`:

```powershell
uv run python -m unittest discover -s tests -p test_gui_projects.py -k analysis_requires_input_and_output_before_run -k analysis_columns_collapse_at_narrow_width -k analysis_pages_expose_empty_and_semantic_status_states -v
```

Expected: FAIL because the run actions begin enabled, responsive columns and empty labels do not exist, and status roles are incomplete.

- [ ] **Step 3: Add one responsive layout widget**

Add `QBoxLayout` to the PyQt imports and implement:

```python
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(left, 3)
        layout.addWidget(right, 2)

    def resizeEvent(self, event) -> None:
        direction = (
            QBoxLayout.Direction.TopToBottom
            if event.size().width() < self.breakpoint
            else QBoxLayout.Direction.LeftToRight
        )
        cast(QBoxLayout, self.layout()).setDirection(direction)
        super().resizeEvent(event)
```

This is the only new layout class. Use it once per analysis page.

- [ ] **Step 4: Recompose SOM and eDCT analysis pages**

For each page:

1. Remove the hero panel.
2. Put workbook selection and SOM filters into a left `sectionPanel`.
3. Put Run Analysis, progress, status, and exported path into a right `sectionPanel`.
4. Assign the resulting `ResponsiveColumns` to `self.workspace_columns`.
5. Put the preview panel below at full width.
6. Add `self.preview_empty = QLabel("Preview rows will appear here after an analysis run.")` with object name `emptyState` above the empty table.
7. Hide `preview_empty` after a successful result fills the table.

Keep existing field attributes and signal handlers so analysis tests and behavior remain stable.

- [ ] **Step 5: Implement readiness and semantic state transitions**

On both pages, connect the read-only path fields:

```python
self.input_file.textChanged.connect(self._update_run_enabled)
self.output_dir.textChanged.connect(self._update_run_enabled)
self._busy = False
self._update_run_enabled()
```

Implement:

```python
status_changed = pyqtSignal(str)

def _update_run_enabled(self) -> None:
    ready = bool(self.input_file.text().strip() and self.output_dir.text().strip())
    self.run_button.setEnabled(ready and not self._busy)

def _set_status(self, text: str, level: str = "neutral") -> None:
    object_names = {
        "neutral": "statusNeutral",
        "progress": "statusProgress",
        "success": "statusSuccess",
        "error": "statusError",
    }
    self.status.setText(text)
    self.status.setObjectName(object_names[level])
    self.status.style().unpolish(self.status)
    self.status.style().polish(self.status)
    self.status_changed.emit(text)
```

Update `_set_busy_state` on SOM and the equivalent eDCT run code to assign `self._busy`, disable file/filter controls while busy, call `_update_run_enabled`, and show the progress bar only while busy.

Use these state calls:

```python
self._set_status("Choose an input workbook and output folder to begin.")
self._set_status("Analysis in progress", "progress")
self._set_status(completion_text, "success")
self._set_status(f"Analysis failed: {error}", "error")
```

Connect `status_changed` to the matching header state label in `MainWindow`. Keep diagnostic exception text intact.

- [ ] **Step 6: Run focused and existing GUI tests**

Run from `som_analyzer/`:

```powershell
uv run python -m unittest discover -s tests -p test_gui_projects.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit the analysis workspace**

```powershell
git add som_analyzer/src/som_analyzer/gui/screens.py som_analyzer/tests/test_gui_projects.py
git commit -m "feat: redesign analysis workspaces"
```

---

### Task 4: Selection-Driven History and Safe Deletion

**Files:**

- Modify: `som_analyzer/src/som_analyzer/gui/screens.py:809-988`
- Test: `som_analyzer/tests/test_gui_projects.py`

**Interfaces:**

- Consumes: `SomAnalyzeController.history_runs`, `history_columns`, and `delete_history_run`.
- Produces: `HistoryPage._selected_run_id() -> int | None`, `HistoryPage._load_selected_run() -> None`, selection-driven rule totals, and confirmed deletion.

- [ ] **Step 1: Add a deterministic controller fake and failing history tests**

Add imports:

```python
from unittest.mock import patch

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox
```

Add this fake beside the test class:

```python
class HistoryController(SomAnalyzeController):
    def __init__(self) -> None:
        super().__init__()
        self.deleted: list[int] = []

    def history_runs(self, project: str = "SOM"):
        return [
            {
                "id": 17,
                "started_at": "2026-08-04 10:00:00",
                "duration_s": 1.25,
                "rows_total": 40,
                "rows_in_scope": 32,
                "rows_failed": 6,
                "status": "completed",
                "input_file": "input.xlsx",
                "exported_file": "output.xlsx",
            }
        ]

    def history_columns(self, run_id: int):
        return [{"rule_name": "email", "column_name": "Owner email", "fail_count": 3}]

    def delete_history_run(self, run_id: int) -> None:
        self.deleted.append(run_id)
```

Add tests:

```python
def test_history_selection_loads_rule_totals(self) -> None:
    controller = HistoryController()
    window = MainWindow(controller)
    history = window.history_page

    self.assertFalse(hasattr(history, "run_id_input"))
    self.assertFalse(history.delete_button.isEnabled())
    self.assertIn("Select an analysis run", history.columns_status.text())

    history.runs_table.selectRow(0)
    self.app.processEvents()

    self.assertEqual(history._selected_run_id(), 17)
    self.assertTrue(history.delete_button.isEnabled())
    self.assertEqual(history.columns_table.rowCount(), 1)
    self.assertEqual(history.columns_table.item(0, 2).text(), "3")


def test_history_delete_requires_confirmation(self) -> None:
    controller = HistoryController()
    window = MainWindow(controller)
    history = window.history_page
    history.runs_table.selectRow(0)

    with patch.object(
        QMessageBox,
        "question",
        return_value=QMessageBox.StandardButton.No,
    ):
        history.delete_button.click()
    self.assertEqual(controller.deleted, [])

    with patch.object(
        QMessageBox,
        "question",
        return_value=QMessageBox.StandardButton.Yes,
    ):
        history.delete_button.click()
    self.assertEqual(controller.deleted, [17])
```

- [ ] **Step 2: Run the history tests and confirm failure**

Run from `som_analyzer/`:

```powershell
uv run python -m unittest discover -s tests -p test_gui_projects.py -k history_selection_loads_rule_totals -k history_delete_requires_confirmation -v
```

Expected: FAIL because history still requires manual run-ID input and deletes immediately.

- [ ] **Step 3: Recompose History as master-detail**

Remove the hero panel, manual `run_id_input`, and `columns_button`. Keep `refresh_button`, `delete_button`, `history_status`, `runs_table`, `columns_status`, and `columns_table`.

Configure selection:

```python
self.runs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
self.runs_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
self.runs_table.itemSelectionChanged.connect(self._load_selected_run)
self.delete_button.setEnabled(False)
self.columns_status.setText("Select an analysis run to inspect validation failure totals.")
```

Place runs and details side by side with `ResponsiveColumns(runs_panel, details_panel, breakpoint=900)`. Put Refresh in the master panel and Delete in the detail panel so the destructive action is isolated.

Store the integer run ID on the first-column item:

```python
id_item = QTableWidgetItem(str(run["id"]))
id_item.setData(Qt.ItemDataRole.UserRole, int(run["id"]))
self.runs_table.setItem(row_index, 0, id_item)
```

- [ ] **Step 4: Implement selection, empty totals, and confirmation**

Replace `_selected_run_id`, `_load_columns`, and `_delete_run` with:

```python
def _selected_run_id(self) -> int | None:
    row = self.runs_table.currentRow()
    if row < 0:
        return None
    item = self.runs_table.item(row, 0)
    return int(item.data(Qt.ItemDataRole.UserRole)) if item is not None else None

def _load_selected_run(self) -> None:
    run_id = self._selected_run_id()
    self.delete_button.setEnabled(run_id is not None)
    if run_id is None:
        self.columns_table.setRowCount(0)
        self.columns_status.setText(
            "Select an analysis run to inspect validation failure totals."
        )
        return

    rows = self.controller.history_columns(run_id)
    self._fill_columns(rows)
    self.columns_status.setText(
        f"Validation failure totals for run {run_id}"
        if rows
        else f"Run {run_id} has no recorded validation failures."
    )

def _delete_run(self) -> None:
    run_id = self._selected_run_id()
    if run_id is None:
        return
    answer = QMessageBox.question(
        self,
        "Delete analysis run",
        f"Delete analysis run {run_id} from history?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    if answer != QMessageBox.StandardButton.Yes:
        return
    self.controller.delete_history_run(run_id)
    self.refresh_runs()
    self.history_status.setText(f"Deleted analysis run {run_id}")
```

Move existing column-table population into `_fill_columns(rows) -> None`. In `refresh_runs`, clear the detail table, disable Delete, and set either `No analysis runs yet.` or `Select an analysis run to inspect validation failure totals.` based on row count.

- [ ] **Step 5: Run history and full GUI tests**

Run from `som_analyzer/`:

```powershell
uv run python -m unittest discover -s tests -p test_gui_projects.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit the history redesign**

```powershell
git add som_analyzer/src/som_analyzer/gui/screens.py som_analyzer/tests/test_gui_projects.py
git commit -m "feat: redesign run history workflow"
```

---

### Task 5: Full Regression and Visual Pre-Flight

**Files:**

- Modify only if a check exposes a redesign regression: `som_analyzer/src/som_analyzer/gui/styles.py`, `som_analyzer/src/som_analyzer/gui/screens.py`, `som_analyzer/tests/test_gui_projects.py`

**Interfaces:**

- Consumes: completed redesigned GUI from Tasks 1-4.
- Produces: verified application behavior and visual evidence at supported sizes.

- [ ] **Step 1: Run the full package test suite**

Run from `som_analyzer/`:

```powershell
uv run python -m unittest discover -s tests -v
```

Expected: all tests PASS. Existing analysis, export, database, filter, and GUI behavior remains unchanged.

- [ ] **Step 2: Start the desktop application**

Run from the repository root:

```powershell
uv run python main.py
```

Expected: the project launch screen opens at 1180 by 760 with no clipped text or empty unexplained tables.

- [ ] **Step 3: Inspect every screen at normal size**

Check this exact sequence:

1. Project launch with SOM and eDCT descriptions and recent-run text.
2. SOM Analysis ready state, path selection, filter loading, progress, success or failure, preview, and exported path.
3. SOM History empty or populated state, row selection, totals, cancelled deletion, and confirmed deletion using a disposable run.
4. Switch checker back to the launch screen.
5. eDCT Analysis with the same states and no SOM filters.
6. eDCT History with project-specific runs only.

Expected: one graphite/off-white/teal theme, one primary action per screen, complete text-based status feedback, and no old blue/yellow hero styling.

- [ ] **Step 4: Inspect the minimum supported size**

Resize the window to 980 by 660 and repeat the four main destinations.

Expected:

- analysis setup and run panels stack vertically;
- history master and detail panels stack vertically;
- scroll areas preserve access to every control;
- navigation labels remain on one line;
- button labels do not wrap;
- tables remain selectable;
- no horizontal scrollbar appears in the page scroll areas.

- [ ] **Step 5: Run the visual-design pre-flight**

Confirm:

- one teal accent is used across every screen;
- 10 px controls and 14 px major panels are consistent;
- no oversized hero panel remains;
- status colors always include explanatory text;
- focus, hover, pressed, disabled, and selected states are visible;
- failure and destructive red are not used decoratively;
- empty preview, empty history, no selection, and no totals all explain the next action;
- visible copy contains no em dash characters;
- the logo is unchanged;
- no animation, new dependency, or business-logic change was introduced.

- [ ] **Step 6: Commit only if pre-flight fixes were needed**

If Steps 1-5 required corrections:

```powershell
git add som_analyzer/src/som_analyzer/gui/styles.py som_analyzer/src/som_analyzer/gui/screens.py som_analyzer/tests/test_gui_projects.py
git commit -m "fix: complete redesign pre-flight"
```

If no correction was needed, do not create an empty commit.
