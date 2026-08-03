# 02 — Align eDCT Welcome layout and responsive presentation

**What to build:** Make the eDCT Welcome page visually consistent with SOM by using the same sidebar presentation, white content surface, and card-oriented grouping while keeping the complete eDCT analysis workflow and current-result preview usable at supported window sizes.

**Blocked by:** 01 — Add eDCT sidebar navigation and separate pages.

**Status:** resolved

- [x] The eDCT sidebar matches SOM's logo, width, colors, spacing, and selected-item styling, with only the checker title changed.
- [x] The eDCT Welcome content uses the same white page surface and visual hierarchy as SOM.
- [x] Input selection, output selection, Run Analysis, progress, status, exported path, and current-result preview are grouped clearly without changing their behavior.
- [x] The current-result preview retains Index, Supplier Punch code, Supplier name, Check, and Comment.
- [x] Welcome content can scroll vertically when it does not fit within the supported minimum window size.
- [x] The eDCT History page retains its existing stored-run list, details, rule totals, and actions.
- [x] SOM navigation, layout, analysis, and history behavior remains unchanged.
- [x] No new dependency, generic checker framework, validation change, export change, or database change is introduced.
- [x] The focused GUI navigation test and the full automated test suite pass.

## Answer

Implemented the SOM visual pattern for eDCT using the existing sidebar, page-surface, hero, card, table, and scroll-area styling. The preview contract and history capabilities remain intact; focused GUI checks, compilation, and all 32 automated tests pass.
