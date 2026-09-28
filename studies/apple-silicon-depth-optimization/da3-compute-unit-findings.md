# Depth Anything 3 Core ML Compute-Unit Findings

**Status:** Completed on 2026-09-28. CPU plus GPU won all three paired trials
at 392 x 392. CPU plus Neural Engine and `all` do not advance to MESS options.

## Question

DA3 preserves twelve native scaled-dot-product-attention operations, and its
compute plan estimates 97.66% Neural Engine cost under CPU plus Neural Engine.
This experiment tests whether that anticipated placement produces a runtime
advantage over the current CPU-plus-GPU application route.

## Protocol

The harness loaded the same validated
`DepthAnything3SmallCameraToken392x392ImageF16.mlpackage` three times with fixed
Core ML compute units:

- `CPU_AND_GPU` (`.cpuAndGPU`);
- `CPU_AND_NE` (`.cpuAndNeuralEngine`); and
- `ALL` (`.all`).

All three model instances remained loaded. Each received 20 warmup predictions
and 100 timed predictions of the same reused, bicubic-resized PIL image. The
prediction order rotated on every warmup and timed iteration. Timing covers the
synchronous Core ML `predict` call and its Python/PIL bridge.

The runs used an M1 Max, macOS 27.0, Xcode 27.0 build 27A266a, Python 3.11.15,
and Core ML Tools 9.0. The package tree SHA-256 was
`a09859410ea749280043437dca028e7e800b247b9ed66c46d302467d276a44b1`; the input
image SHA-256 was
`ea78c3b872b1e8b27de48cadf1d4a692cd42ddf5f72fcab78e2be2937935fb79`.

## Timing

| Run | Core ML compute units | Median | p90 | p99 | Median versus CPU + GPU |
| --- | --- | ---: | ---: | ---: | ---: |
| [1](da3-compute-units/run1.json) | CPU + GPU | 24.15 ms | 27.42 ms | 28.58 ms | baseline |
| 1 | CPU + Neural Engine | 30.12 ms | 30.99 ms | 32.86 ms | 24.7% slower |
| 1 | All | 29.61 ms | 31.09 ms | 32.62 ms | 22.6% slower |
| [2](da3-compute-units/run2.json) | CPU + GPU | 24.42 ms | 27.95 ms | 29.83 ms | baseline |
| 2 | CPU + Neural Engine | 30.01 ms | 31.09 ms | 34.29 ms | 22.9% slower |
| 2 | All | 29.77 ms | 31.21 ms | 32.19 ms | 21.9% slower |
| [3](da3-compute-units/run3.json) | CPU + GPU | 24.14 ms | 27.32 ms | 29.96 ms | baseline |
| 3 | CPU + Neural Engine | 30.23 ms | 31.26 ms | 32.52 ms | 25.2% slower |
| 3 | All | 29.85 ms | 31.14 ms | 33.16 ms | 23.6% slower |

The median of the three run medians was 24.15 ms for CPU plus GPU, 30.12 ms
for CPU plus Neural Engine, and 29.77 ms for `all`. The two non-GPU choices
were therefore 24.7% and 23.3% slower, respectively, by that aggregate.

## Output agreement

Each route's final output was compared with CPU plus GPU. The values were
stable across all three runs.

| Compute units | Cosine similarity | Mean absolute error | Maximum absolute error | Gate |
| --- | ---: | ---: | ---: | --- |
| CPU + GPU | 1.000000000 | 0 | 0 | Passed |
| CPU + Neural Engine | 0.999994579 | 0.009573 | 0.063477 | Passed |
| All | 0.999998958 | 0.003832 | 0.024414 | Passed |

The gate required cosine similarity of at least `0.999` and mean absolute error
of at most `0.01`. Passing it establishes usable output agreement; it does not
offset the measured latency regression.

## Decision

Keep DA3 Core ML on CPU plus GPU. Do not add CPU-plus-Neural-Engine or `all`
settings to MESS from this result. The high anticipated Neural Engine placement
did not translate into lower latency, matching the broader lesson from DA2.

The 518 x 518 compute-unit sweep does not advance. Its gate required a
competitive non-GPU route at 392 x 392 or a separate quality reason to pay for
the larger model; neither condition is present. The next independent DA3
experiment remains planar FP16 graph input at 392 x 392.

## Limits

These are paired standalone Python/Core ML measurements, not complete MESS
depth-source timings. All three configured model instances were resident during
the trial. Compare routes within a run; do not compare the absolute values with
the earlier 16.69 ms DA3 result from a different harness and runtime state.

## Reproduction

After the pinned DA3 build has produced its 392 x 392 package, run:

```sh
build/depth-anything-3/venv/bin/python \
  scripts/models/depth-anything-3/benchmark_compute_units.py \
  --model build/depth-anything-3/coreml/DepthAnything3SmallCameraToken392x392ImageF16.mlpackage \
  --image build/depth-anything-3/source/assets/examples/SOH/000.png \
  --compute-units CPU_AND_GPU,CPU_AND_NE,ALL \
  --warmups 20 \
  --iterations 100 \
  --output build/depth-anything-3/compute-unit-run.json
```

Rotate the `--compute-units` order across repeated trials. The harness rotates
prediction order internally; changing the initial list order also rotates model
construction and the first call in each cycle.
