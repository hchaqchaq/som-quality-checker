# Align eDCT Navigation and Layout with SOM

Status: ready-for-agent

## Problem Statement

The eDCT checker currently places its analysis controls, current-result preview, and run history in one vertically stacked page. At normal application dimensions, the result is visually inconsistent with the SOM checker and parts of the history interface become crowded or clipped. Users expect both checker projects to share the established left-sidebar navigation and page structure.

## Solution

Give eDCT the same visual shell and navigation behavior as SOM. The eDCT checker will have a matching left sidebar with separate Welcome and History destinations plus a Back to projects action. Its Welcome page will retain the complete eDCT analysis workflow and current-result preview. Its History page will contain only prior eDCT analysis runs and related actions.

The change is limited to GUI composition and styling. eDCT validation rules, analysis scope, analysis workbook export, worker-thread execution, preview data, and run-history persistence remain unchanged.

## User Stories

1. As an eDCT user, I want the eDCT checker to use the same navigation pattern as SOM, so that I do not need to learn two interfaces.
2. As an eDCT user, I want a persistent left sidebar, so that the available eDCT sections are immediately visible.
3. As an eDCT user, I want the sidebar title to read `eDCT Checker`, so that the active checker project is unambiguous.
4. As an eDCT user, I want the eDCT sidebar to use the same logo as SOM, so that both projects have consistent application branding.
5. As an eDCT user, I want the eDCT sidebar to match SOM's width, colors, spacing, and selected-item styling, so that the application looks cohesive.
6. As an eDCT user, I want a Welcome destination in the sidebar, so that I can return to the current analysis workflow at any time.
7. As an eDCT user, I want a History destination in the sidebar, so that prior analysis runs do not crowd the current workflow.
8. As an eDCT user, I want a Back to projects action in the sidebar, so that I can switch checker projects without restarting the application.
9. As an eDCT user, I want Welcome selected when I enter the eDCT checker, so that I can begin an analysis immediately.
10. As an eDCT user, I want the selected sidebar destination visibly highlighted, so that I know which page is active.
11. As an eDCT user, I want selecting Welcome to display only the current eDCT workflow, so that historical information does not distract from analysis.
12. As an eDCT user, I want selecting History to display only eDCT history, so that current controls and previous runs are clearly separated.
13. As an eDCT user, I want the Welcome content presented on the same white page surface used by SOM, so that both checker projects share the same visual hierarchy.
14. As an eDCT user, I want card-oriented grouping consistent with SOM, so that related controls are easier to scan.
15. As an eDCT user, I want to keep selecting an eDCT input workbook from Welcome, so that the navigation redesign does not remove existing functionality.
16. As an eDCT user, I want to keep selecting an output folder from Welcome, so that I control where the analysis workbook is saved.
17. As an eDCT user, I want to keep running analysis from Welcome, so that the core workflow remains in one place.
18. As an eDCT user, I want to see analysis progress and status on Welcome, so that I know whether an analysis run is active or finished.
19. As an eDCT user, I want the exported-workbook path shown on Welcome, so that I can locate the latest result.
20. As an eDCT user, I want the current result preview beneath the run controls, so that I can inspect the latest assessed rows without opening History.
21. As an eDCT user, I want the preview to retain Index, Supplier Punch code, Supplier name, Check, and Comment, so that the redesign preserves useful result information.
22. As an eDCT user, I want the Welcome page to remain usable at the supported minimum window size, so that controls and preview content are not clipped.
23. As an eDCT user, I want Welcome content to scroll vertically when necessary, so that smaller windows remain usable without compressing every component.
24. As an eDCT user, I want History to retain its existing stored-run list, details, rule totals, and actions, so that navigation changes do not reduce history capabilities.
25. As a quality manager, I want the History page filtered to eDCT, so that SOM and eDCT analysis runs are never mixed.
26. As a SOM user, I want the existing SOM sidebar and pages to remain unchanged, so that improving eDCT does not regress the established workflow.
27. As a user, I want Back to projects to return to the existing project-selection screen, so that project switching remains predictable.
28. As a user, I want returning to eDCT to show Welcome, so that the checker opens at its primary task rather than an old navigation state.
29. As a maintainer, I want the eDCT shell to reuse the existing SOM layout pattern and stylesheet rules, so that the change stays small and consistent.
30. As a maintainer, I want the existing eDCT Welcome widget to retain responsibility for analysis controls and result preview, so that validation behavior is not coupled to navigation.
31. As a maintainer, I want the existing history widget reused for eDCT History, so that history behavior has one implementation.
32. As a maintainer, I want GUI navigation tested through observable window behavior, so that tests remain stable when internal layout code changes.

## Implementation Decisions

- Reuse the established SOM shell pattern for eDCT rather than introducing a generic checker-shell framework.
- Give eDCT its own horizontal shell containing a fixed-width sidebar and a stacked content area.
- Match the SOM sidebar's logo, width calculation, colors, spacing, menu styling, and Back to projects placement.
- Use `eDCT Checker` as the sidebar title.
- Use exactly two menu destinations: `Welcome` and `History`.
- Default the eDCT menu to Welcome whenever the user enters the checker from project selection.
- Keep the eDCT analysis widget as the Welcome page and remove embedded history from that widget.
- Reuse the existing history component as a separate page configured for the eDCT checker project.
- Wrap eDCT Welcome and History content using the existing scrollable page pattern and white page surface.
- Preserve the current project-selection screen and Back to projects behavior.
- Preserve the existing preview columns and current-result population behavior.
- Preserve worker-thread execution so workbook loading, validation, and export do not block the UI.
- Make no changes to validation rules, analysis scope, export behavior, database schema, run-history repository behavior, or dependencies.

## Testing Decisions

- Use one highest-level offscreen GUI seam through the main application window.
- Extend the existing project-navigation test rather than adding a new lower-level layout test suite.
- Exercise real button and menu interactions without mocking the GUI widgets.
- Verify that selecting eDCT opens an eDCT shell whose visible menu contains Welcome and History and whose Back to projects action is available.
- Verify that Welcome is initially selected and exposes the existing eDCT analysis controls and preview contract.
- Verify that selecting History changes the visible eDCT content to the eDCT-configured history page.
- Verify that selecting Welcome returns to the analysis page.
- Verify that Back to projects returns to project selection.
- Assert user-observable navigation, labels, visible pages, and preserved controls rather than private layout construction details or exact pixel geometry.
- Use the repository's existing offscreen Qt project-navigation test as prior art.
- Run the focused GUI test red before implementation and green afterward, then run the full automated test suite.

## Out of Scope

- Changing eDCT validation rules or required workbook structure.
- Changing which rows form the eDCT analysis scope.
- Changing analysis workbook naming, preservation, or export behavior.
- Changing the eDCT preview fields or result aggregation.
- Changing run-history storage, schema, filtering semantics, or actions.
- Redesigning the project-selection screen.
- Redesigning the existing SOM checker.
- Adding a generic plugin system, checker-shell abstraction, or new dependency.
- Adding new checker projects or sidebar destinations.
- Persisting the last selected eDCT destination between application launches.
- Applying exact pixel-level screenshot comparison tests.

## Further Notes

- The observed screenshot shows analysis and history stacked on a single eDCT page, with lower content crowded and clipped.
- Canonical project spelling is `eDCT`.
- `Check` remains the number of validation failures on an assessed row; `Comment` remains the human-readable explanation.
- This focused specification supplements the broader eDCT checker specification and supersedes no business-rule requirements.
