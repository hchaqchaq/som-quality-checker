# eDCT Sidebar Design

## Goal

Make the eDCT checker use the same navigable shell as the SOM checker instead of stacking analysis and history on one oversized page.

## Considered approaches

1. **Reuse the SOM shell pattern for eDCT (selected).** Add an eDCT sidebar and separate stacked Welcome and History pages. This is the smallest change that fixes navigation and clipping while preserving behavior.
2. **Create a generic checker-shell abstraction.** This removes some duplicated layout code, but adds an abstraction for only two screens and increases regression risk.
3. **Only add scrolling to the current eDCT page.** This reduces clipping but does not provide the requested sidebar or separate analysis from history.

## Layout

- The eDCT checker has a left sidebar matching SOM's logo, width, colors, spacing, and selected-item styling.
- The sidebar title is `eDCT Checker`.
- The sidebar contains `Welcome`, `History`, and `Back to projects`.
- `Welcome` and `History` switch between separate pages in the existing main window.
- The Welcome page uses the same white page surface and card-oriented visual language as SOM.

## Welcome page

The eDCT Welcome page retains:

- input workbook selection;
- output-folder selection;
- Run Analysis action and progress indicator;
- run status and exported-workbook path;
- preview of the current analysis result.

The page remains scrollable at the application's supported minimum window size.

## History page

The existing `HistoryPage` remains the source of eDCT history behavior and is shown only when `History` is selected. Its project filter remains `eDCT`.

## Behavior preserved

The change does not alter eDCT validation, export, worker-thread execution, result preview data, run-history persistence, or project selection behavior.

## Verification

- Add one focused GUI regression test proving that eDCT has its own sidebar navigation and separate Welcome and History pages.
- Run that test red before implementation and green afterward.
- Run the existing automated test suite.
