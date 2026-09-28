# Codex Handoff: DA3 compute-unit benchmark

- Updated: 2026-09-28 04:55 EDT
- Owning repository: `/Users/jvcleave/Documents/WORK_IN_PROGRESS/GITHUB/PUBLIC/DepthStudies`
- Branch and HEAD: `main`; completed milestone is pending commit atop `3b4d1de`

## Objective

Determine whether the existing validated DA3 Small 392 x 392 Core ML package
runs better with fixed CPU plus GPU, CPU plus Neural Engine, or all compute
units before adding another MESS engine option.

## Definition of Done

A checked-in reproducible harness has run three alternating trials against the
same package and image; raw JSON and concise findings record latency and output
agreement; the result determines whether any compute-unit route should advance
to app integration.

## Current Bounded Milestone

Complete and document the isolated 392 x 392 Core ML compute-unit comparison.

## Non-Goals

Do not launch MESS, alter the DA3 model, build the FP16-input DA3 candidate, or
change an application default during this milestone.

## Repository State

DepthStudies was clean at `3b4d1de` before this milestone. The new harness, raw
reports, findings, workflow documentation, and updated test checklist are ready
to commit. The three trials all selected CPU plus GPU as the fastest route.

## Decisions and Constraints to Preserve

- Use the same loaded package and reused image input for all three routes.
- Alternate prediction order to reduce time-order bias.
- Report median, p90, and p99; do not infer runtime speed from the compute plan.
- Preserve the camera-token and native-SDPA model graph exactly.

## Relevant Files

- `TEST_TODO_LIST.md` — records the planned DA3 trials.
- `scripts/models/depth-anything-3/` — owns the reproducible DA3 workflow.
- `studies/apple-silicon-depth-optimization/compute-plans/depth-anything-3-small-392x392.md` — anticipated placement context.
- `/Users/jvcleave/Documents/WORK_IN_PROGRESS/MAC_APPS/MESS/MessApp/MessApp/MessApp/DepthAnything3SmallCameraToken392x392ImageF16.mlpackage` — package under test.
- `build/depth-anything-3/source/assets/examples/SOH/000.png` — pinned reference image.

## Verification

- Command: three runs of `benchmark_compute_units.py` with 20 warmups and 100
  timed predictions per compute-unit route, followed by JSON consistency checks.
- Latest result: Passed. All three reports passed output gates and contain 900
  total timed predictions. CPU plus GPU was 21.9–25.2% faster than the two
  alternatives by paired median comparison.

## Remaining Issues

None for this milestone. CPU plus Neural Engine and `all` are rejected for DA3
392 x 392; the 518 x 518 sweep does not advance.

## Next Exact Action

In a new bounded milestone, add planar FP16 graph input to DA3 392 x 392 and
validate it against the unchanged FP32-input graph before any app integration.

**Fresh-task startup:** Read `docs/internal/handoffs/da3-compute-unit-benchmark.md`, recover
current state from the repository, and continue with its **Next Exact Action**;
read the listed files first, follow directly referenced files or inspect narrowly
adjacent code as needed, and consult the previous conversation only if the
handoff and repository state lack a required decision, constraint, or
authorization.
