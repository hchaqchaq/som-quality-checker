# 01 — Add eDCT sidebar navigation and separate pages

**What to build:** Give eDCT the same user-facing navigation pattern as SOM: a matching left sidebar with Welcome, History, and Back to projects. Welcome must retain the current analysis workflow and preview, while History must display the existing eDCT-filtered run history on a separate page.

**Blocked by:** None — can start immediately.

**Status:** resolved

- [x] Selecting eDCT from project selection opens the eDCT shell with Welcome selected.
- [x] The sidebar title is `eDCT Checker` and the visible destinations are Welcome and History.
- [x] The sidebar includes a Back to projects action.
- [x] Selecting Welcome displays the existing eDCT input, output, Run Analysis, status, exported-path, and preview controls.
- [x] Selecting History displays the existing run-history component filtered to the eDCT checker project.
- [x] Welcome and History do not appear stacked on the same page.
- [x] Back to projects returns to the existing project-selection screen.
- [x] Re-entering eDCT from project selection opens Welcome.
- [x] A focused offscreen GUI regression test exercises the real navigation controls and visible-page changes.
- [x] Existing eDCT validation, export, worker-thread, preview-data, and history-persistence behavior remains unchanged.

## Answer

Implemented the eDCT shell with a SOM-matching sidebar, separate Welcome and History pages, eDCT-filtered history refresh, Welcome reset on entry, and Back to projects navigation. The focused offscreen GUI test covers the complete navigation flow and preserved Welcome controls.
