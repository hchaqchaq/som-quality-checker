# Full-Screen Operational Workspace Redesign

## Goal

Redesign every PyQt screen as a coherent operational workspace for SOM and eDCT workbook-quality reviews. Improve navigation, hierarchy, feedback, and history inspection without changing validation, export, persistence, or worker-thread behavior.

## Design Read

This is a full visual and layout redesign for operational users. It uses a calm enterprise-tool language built with native PyQt widgets and Qt stylesheets.

- `DESIGN_VARIANCE: 4`
- `MOTION_INTENSITY: 2`
- `VISUAL_DENSITY: 6`

The design prioritizes scanability, predictable navigation, keyboard clarity, and useful table density over marketing-style visual effects.

## Current-State Audit

### Existing structure

- A project-selection page opens SOM or eDCT.
- Each checker has Welcome and History destinations in a sidebar.
- Analysis screens contain workbook selection, output selection, optional SOM filters, run controls, status, preview, and export path.
- History shows stored runs and per-rule or per-column totals.

### Existing visual language

- Bright blue and yellow palette.
- Roboto/Open Sans/Arial font fallback.
- Large blue hero panels.
- Repeated white rounded cards around most content groups.
- Blue table headers and yellow selections.

### Preserve

- Project separation and checker-specific history.
- User-selected input and output paths.
- SOM scope filters and their current semantics.
- Background analysis through `AnalysisWorker` and `QThread`.
- Current validation, export, preview, and database operations.
- Existing controller boundary between GUI and history storage.

### Retire

- Oversized hero panels on operational screens.
- Repeated card nesting that gives every block equal visual weight.
- Manual run-ID entry for history actions.
- Weak empty states and status feedback that depend mainly on color.
- Separate SOM and eDCT layout treatments for equivalent tasks.

## Chosen Direction

Use an Operational Workspace: a compact shared shell, a clear analysis workspace, and a master-detail history view.

Two alternatives were rejected:

1. A guided linear review would help occasional users but slow repeated work.
2. A dark, table-first data console would maximize density but reduce approachability and daytime readability.

## Information Architecture

### Project selection

The launch screen contains:

- application identity and one concise purpose statement;
- one SOM checker choice and one eDCT checker choice;
- a short description of each checker;
- recent-run context when history exists;
- a clear empty state when no runs exist.

The two checker choices are visually distinct but use the same component structure. The screen does not introduce settings or new workflows.

### Shared workspace shell

After project selection, both checkers use one shell:

- compact left navigation with `Analysis`, `History`, and `Switch checker`;
- slim top bar with active checker, current destination, and current analysis state;
- one main content surface that changes with the selected destination.

The navigation stays on one line per item and uses text labels. The active destination is shown through contrast and weight, not color alone.

### Analysis workspace

The upper analysis region uses two columns at normal desktop widths:

- left: input workbook, output folder, and SOM filters when applicable;
- right: primary Run Analysis action, progress, completion summary, and exported path.

The preview table spans the full width below the setup region. It prioritizes `Check` and `Comment` visibility and retains the checker-specific preview columns.

At narrow widths, the two columns collapse into one vertical sequence: setup, run state, then preview. No control is clipped or hidden.

### History workspace

History uses a master-detail layout:

- the run table is the master list;
- selecting a row loads its rule and column totals in the detail region;
- refresh and delete act on the current selection;
- delete remains visually separated and requires confirmation;
- manual run-ID entry is removed.

If no run is selected, the detail region explains how to select one. If no runs exist, the master region explains that completed analyses will appear there.

## Visual System

### Palette

- Navigation: deep graphite.
- Main background: cool off-white.
- Elevated surface: near-white with a subtle cool border.
- Primary text: dark slate.
- Secondary text: medium slate with WCAG AA contrast.
- Accent: restrained teal used for primary actions, focus, selection, and active navigation.
- Success: green, warning: amber, failure and destructive actions: red.

Teal is the only general accent. Semantic colors are limited to actual state communication.

### Typography

Use native `Segoe UI` with Windows-compatible fallbacks. Hierarchy comes from size, weight, and spacing:

- workspace title: 24 px semibold;
- section title: 17 px semibold;
- body and controls: 14 px;
- supporting text and table metadata: 12-13 px.

Visible copy uses the repository domain vocabulary: analysis run, assessed row, validation failure, Check, and Comment.

### Shape and elevation

- Controls use a 10 px radius.
- Major surfaces use a 14 px radius.
- Tables use a subtle border and no decorative shadow.
- Elevation is reserved for the main workspace surface and transient dialogs.
- Internal groups prefer spacing and headings over nested cards.

### Controls

- Each screen has one visually dominant primary action.
- Secondary actions use quiet or outlined styling.
- Destructive actions use red only when enabled and remain separate from routine actions.
- All buttons have hover, pressed, disabled, and keyboard-focus states.
- Button text remains on one line at supported desktop widths.

## Interaction States

### Ready

The run panel states what is needed next. Run Analysis stays disabled until required input and output paths are present.

### Loading

The current indeterminate progress behavior remains tied to the background worker. File pickers, filters, and Run Analysis are disabled while work is active. The status text identifies the active checker and action.

### Success

The outcome summary shows run ID, duration, total rows, assessed rows where available, failed rows, and exported path. The preview updates immediately.

### Failure

The failure message appears in the run panel near the action that caused it. It uses a short title plus the actionable error text and does not rely on red alone.

### Empty

- No preview: explain that results appear after a completed analysis.
- No history: explain that completed runs appear here.
- No history selection: prompt the user to select a run.
- No rule totals: state that the selected run has no recorded failures.

## Data Flow and Boundaries

The redesign changes presentation and navigation only.

- `gui/app.py` remains the application bootstrap and controller boundary.
- `analysis/runner.py` and `analysis/edct.py` retain analysis and export behavior.
- `AnalysisWorker` and `QThread` continue to protect UI responsiveness.
- Repository methods remain responsible for listing, inspecting, and deleting runs.
- Existing SOM filter normalization and eDCT workbook boundaries remain unchanged.

Equivalent SOM and eDCT layout code may share small widget-building helpers. No general component framework, theme engine, or new dependency is introduced.

## Error Handling and Safety

- Missing input or output selections are shown inline and prevent execution.
- Workbook and export exceptions retain their original diagnostic text inside a readable failure state.
- History deletion requires a selected run and a confirmation dialog.
- Deleting a run refreshes both the master list and detail region.
- Switching checker or destination does not terminate an active worker or mutate analysis data.
- Existing user-selected paths remain explicit and are never replaced with hardcoded defaults.

## Accessibility and Desktop Behavior

- Text and control contrast target WCAG AA.
- Focus indicators are visible on every interactive control.
- Status meaning is communicated with text in addition to color.
- Logical tab order follows the visible workflow.
- Controls retain practical target sizes for mouse and keyboard use.
- Tables remain keyboard-selectable and expose a clear selected row.
- The layout remains usable at the application's minimum supported window size.

## Implementation Scope

Primary changes should remain in:

- `som_analyzer/src/som_analyzer/gui/styles.py`;
- `som_analyzer/src/som_analyzer/gui/screens.py`;
- focused GUI tests under `som_analyzer/tests/`.

`gui/app.py` changes only if a small application-level palette or font setting is required. Business logic, validation rules, export code, and database schema are out of scope.

## Verification

Automated checks:

- project selection opens each checker;
- sidebar navigation switches Analysis and History;
- Switch checker returns to project selection;
- required selections control Run Analysis availability;
- SOM filters remain wired to the existing scope-filter path;
- selecting a history row loads its totals;
- deleting history requires confirmation and refreshes the view;
- empty, loading, success, and failure states render with the expected roles;
- existing analysis, export, database, and GUI tests still pass.

Visual checks:

- render project selection, SOM analysis, eDCT analysis, and both history views;
- inspect ready, loading, success, failure, and empty states;
- inspect normal and minimum supported window sizes;
- verify text is not clipped, primary actions remain visible, tables are usable, and no horizontal layout overflow occurs.

## Explicit Non-Goals

- No changes to validation rules or workbook outputs.
- No web frontend or migration away from PyQt.
- No new animation or UI dependency.
- No dark-mode toggle in this redesign.
- No settings screen, onboarding wizard, or dashboard metrics.
- No redesign of the application logo.
