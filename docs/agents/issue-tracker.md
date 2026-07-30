# Issue tracker: Local Markdown

Issues and specs for this repository live as Markdown files under `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- The spec is `.scratch/<feature-slug>/spec.md` when a feature-local copy is needed.
- Implementation tickets are separate files under `.scratch/<feature-slug>/issues/`.
- Ticket filenames use dependency order: `<NN>-<slug>.md`.
- Each ticket records its state on a `Status:` line.
- Each ticket records blocking edges on a `Blocked by:` line.
- Comments and conversation history append under a `## Comments` heading when needed.

## When a skill says "publish to the issue tracker"

Create a Markdown file under the appropriate `.scratch/<feature-slug>/` directory.

## When a skill says "fetch the relevant ticket"

Read the referenced file under `.scratch/`.

## Wayfinding operations

- **Map**: `.scratch/<effort>/map.md`
- **Child ticket**: `.scratch/<effort>/issues/NN-<slug>.md`
- **Blocking**: a ticket's `Blocked by:` line
- **Frontier**: tickets marked `ready-for-agent` whose blockers are resolved
- **Claim**: change `Status:` to `claimed` before work
- **Resolve**: append the result under `## Answer`, change `Status:` to `resolved`, and update the map when one exists
