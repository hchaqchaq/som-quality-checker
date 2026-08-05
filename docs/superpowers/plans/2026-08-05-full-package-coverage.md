# Full Package Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce 100% statement and branch coverage for `som_analyzer/src/som_analyzer`.

**Architecture:** Keep production behavior unchanged. Exercise existing public and callback paths through the current unittest modules, use temporary files and mocks only at OS/GUI boundaries, and place the coverage gate in the package configuration.

**Tech Stack:** Python 3.12+, unittest, coverage.py, pandas, openpyxl, PyQt6, uv.

## Global Constraints

- Cover every production module under `som_analyzer/src/som_analyzer`.
- Require both statement and branch coverage at 100%.
- Do not broadly omit modules or branches.
- Use `# pragma: no cover` only for code proven unreachable in tests and explain why inline.
- Preserve the existing untracked `som_analyzer/data/` directory.

---

### Task 1: Coverage gate and analysis gaps

**Files:**

- Modify: `som_analyzer/pyproject.toml`
- Modify: `som_analyzer/tests/test_validation_rules.py`
- Modify: `som_analyzer/tests/test_edct_analysis.py`

**Interfaces:**

- Consumes: existing unittest discovery and analyzer public functions.
- Produces: a reproducible `coverage run -m unittest discover -s tests` gate covering analysis modules.

- [ ] **Step 1: Add focused tests for the currently missing loader, runner, validator, config, and eDCT success/error branches.**

Use existing workbook builders and temporary-directory helpers. Assert returned data, failure entries, exported output, and raised exceptions rather than mock call counts.

- [ ] **Step 2: Run each new test before any production edit.**

Run: `uv run python -m unittest <new-test-id> -v`

Expected: fail only where the asserted branch is not yet exercised or exposes incorrect behavior.

- [ ] **Step 3: Add the coverage development dependency and gate.**

Add `coverage` to the package development dependency group and configure:

```toml
[tool.coverage.run]
branch = true
source = ["som_analyzer"]

[tool.coverage.report]
fail_under = 100
show_missing = true
```

- [ ] **Step 4: Measure the remaining package gaps.**

Run: `uv run coverage run -m unittest discover -s tests`

Run: `uv run coverage report`

Expected: analysis gaps are closed; remaining misses are isolated to repository, GUI, and smoke modules.

### Task 2: Repository and CLI paths

**Files:**

- Modify: `som_analyzer/tests/test_validation_rules.py`
- Create: `som_analyzer/tests/test_smoke.py`

**Interfaces:**

- Consumes: `RunRepository` and `som_analyzer.smoke.main`.
- Produces: deterministic coverage of schema creation/migration, run lifecycle, query/delete operations, smoke success, and smoke argument/error paths.

- [ ] **Step 1: Add repository lifecycle tests using a temporary SQLite database.**

Exercise creation, migration, successful and failed runs, project filtering, detail lookup, deletion, rule-total replacement, and missing-record behavior through the public repository API.

- [ ] **Step 2: Run the repository tests and verify their assertions fail when each target call is removed.**

Run: `uv run python -m unittest tests.test_validation_rules -v`

- [ ] **Step 3: Add smoke CLI tests with temporary workbooks and patched `sys.argv`.**

Cover missing input, successful analysis/history output, and analyzer failure propagation while asserting exit behavior and user-visible output.

- [ ] **Step 4: Run the CLI tests.**

Run: `uv run python -m unittest tests.test_smoke -v`

Expected: all repository and CLI tests pass.

### Task 3: GUI controller and widget callbacks

**Files:**

- Modify: `som_analyzer/tests/test_gui_projects.py`

**Interfaces:**

- Consumes: the existing offscreen `QApplication`, `MainWindow`, worker classes, dialogs, and controller functions.
- Produces: coverage for GUI initialization, file selection, analysis lifecycle, history actions, worker success/failure, navigation, and app bootstrap branches.

- [ ] **Step 1: Add one focused test per uncovered callback group.**

Use real widgets and Qt signals. Patch file dialogs, message boxes, process exit, filesystem selection, and worker dependencies only where interacting with the desktop or OS would be unsafe.

- [ ] **Step 2: Run every new GUI test individually before completing its assertions.**

Run: `uv run python -m unittest tests.test_gui_projects.ProjectNavigationTests.<test_name> -v`

Expected: each new test fails for its intended uncovered behavior before becoming green.

- [ ] **Step 3: Run the complete GUI module.**

Run: `uv run python -m unittest tests.test_gui_projects -v`

Expected: all GUI tests pass in offscreen mode.

### Task 4: Close the gate and verify

**Files:**

- Modify only the test files named above if the coverage report identifies residual executable branches.

**Interfaces:**

- Consumes: the coverage configuration and complete unittest suite.
- Produces: a reproducible 100% statement and branch coverage result.

- [ ] **Step 1: Run the coverage gate and inspect every remaining line/partial branch.**

Run: `uv run coverage run -m unittest discover -s tests`

Run: `uv run coverage report --show-missing`

- [ ] **Step 2: Add the smallest behavior assertion for each residual executable gap.**

Do not add production abstractions or duplicate tests. Use a justified `# pragma: no cover` only when the branch cannot execute under supported Python/platform behavior.

- [ ] **Step 3: Run final verification.**

Run: `uv run coverage run -m unittest discover -s tests`

Run: `uv run coverage report --fail-under=100`

Run: `uv run python -m unittest discover -s tests -v`

Expected: coverage reports 100% statements and branches, the gate exits zero, and the full suite passes.
