# 01 — Add checker-project selection and project-specific history

**What to build:** Add a project-selection entry screen so users can open SOM or eDCT in one application, return to project selection, and see history belonging only to the selected checker project. Preserve the existing SOM workflow and migrate existing history records to SOM.

**Blocked by:** None — can start immediately.

**Status:** resolved

- [ ] The application initially presents `SOM Quality Checker` and `eDCT Quality Checker`.
- [ ] Selecting SOM opens the existing SOM workflow without changing its validation behavior.
- [ ] Users can return from a checker to project selection without restarting the application.
- [ ] Run history stores a checker-project value using canonical values `SOM` and `eDCT`.
- [ ] Existing database rows migrate to `SOM` without losing run or rule-total data.
- [ ] SOM history excludes eDCT runs, and eDCT history excludes SOM runs.
- [ ] Failed runs can retain their project and error message.
- [ ] Project selection and history separation are covered through an offscreen GUI seam and repository-level migration tests.

## Answer

Implemented the project selector, back navigation, project-aware history migration/filtering, and offscreen GUI/repository coverage.
