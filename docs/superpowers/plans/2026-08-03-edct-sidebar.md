# eDCT Sidebar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give eDCT the same sidebar navigation and responsive page presentation as SOM while preserving all analysis and history behavior.

**Architecture:** Keep `EdctPage` as the Welcome workflow, move its existing `HistoryPage` into a separate eDCT stacked page, and compose both inside an eDCT shell owned by `MainWindow`. Reuse existing Qt widgets and stylesheet object names; add no dependency or generic checker framework.

**Tech Stack:** Python 3.12, PyQt6, unittest, uv

## Global Constraints

- Keep eDCT validation, analysis scope, export, worker-thread, preview-data, and database behavior unchanged.
- Keep SOM behavior unchanged.
- Use exactly `Welcome`, `History`, and `Back to projects` for eDCT navigation.
- Add no dependency or generic checker framework.

---

### Task 1: eDCT sidebar navigation and separate pages

**Files:**
- Modify: `som_analyzer/tests/test_gui_projects.py`
- Modify: `som_analyzer/src/som_analyzer/gui/screens.py`

**Interfaces:**
- Consumes: `MainWindow`, `EdctPage`, `HistoryPage`, and the existing `QStackedWidget` navigation pattern.
- Produces: `MainWindow.edct_shell`, `edct_menu`, `edct_pages`, `edct_page`, `edct_history_page`, and `edct_back_button` as observable GUI widgets.

- [ ] **Step 1: Write the failing navigation test**

Extend the existing project-navigation test to select eDCT and assert that the eDCT shell opens on Welcome, the menu labels are `Welcome` and `History`, History and Welcome switch the visible stacked page, and Back to projects returns to project selection.

- [ ] **Step 2: Run the focused test and verify RED**

Run from `som_analyzer/`: `uv run python -m unittest tests.test_gui_projects.ProjectNavigationTests.test_user_can_select_projects_and_return -v`

Expected: FAIL because `MainWindow` does not yet expose an eDCT shell/menu/stack.

- [ ] **Step 3: Implement the minimal eDCT shell**

Remove History from the Welcome layout. Build the eDCT horizontal shell beside the existing SOM shell, using a sidebar menu and stacked Welcome/History pages. Keep a reference from Welcome to the separate eDCT history widget so a completed analysis can refresh it. Reset the eDCT menu to Welcome when entering the project.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run from `som_analyzer/`: `uv run python -m unittest tests.test_gui_projects.ProjectNavigationTests.test_user_can_select_projects_and_return -v`

Expected: PASS.

### Task 2: SOM-matching eDCT presentation and scrolling

**Files:**
- Modify: `som_analyzer/tests/test_gui_projects.py`
- Modify: `som_analyzer/src/som_analyzer/gui/screens.py`

**Interfaces:**
- Consumes: the eDCT shell from Task 1 and existing stylesheet object names `sidebarPanel`, `pageSurface`, `heroPanel`, and `sectionCard`.
- Produces: scrollable eDCT Welcome/History surfaces and card-grouped Welcome controls.

- [ ] **Step 1: Write the failing presentation test**

Add an offscreen GUI test asserting that the eDCT sidebar uses `sidebarPanel`, the content stack uses `pageSurface`, and Welcome and History are hosted in vertically scrollable page wrappers while the preview contract remains unchanged.

- [ ] **Step 2: Run the focused presentation test and verify RED**

Run from `som_analyzer/`: `uv run python -m unittest tests.test_gui_projects.ProjectNavigationTests.test_edct_uses_som_page_presentation -v`

Expected: FAIL until the eDCT shell and scrollable surfaces expose the approved presentation.

- [ ] **Step 3: Apply existing SOM presentation patterns**

Build the eDCT sidebar with the existing logo frame, title, width calculation, spacing, and menu styling. Group Welcome content into a hero, workbook-selection card, analysis card, preview card, and export card using existing stylesheet object names. Keep all existing eDCT widget attributes and signal connections.

- [ ] **Step 4: Run focused GUI tests and type-oriented checks**

Run from `som_analyzer/`: `uv run python -m unittest tests.test_gui_projects -v`

Run from `som_analyzer/`: `uv run python -m compileall -q src tests`

Expected: both commands exit successfully.

- [ ] **Step 5: Run the full suite**

Run from `som_analyzer/`: `uv run python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 6: Review and commit**

Review the implementation against `.scratch/edct-sidebar/spec.md` and repository standards, then commit only the implementation plan, GUI source, and GUI tests with message `feat: align edct navigation with som`.
