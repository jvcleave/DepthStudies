# Depth Anything V2 FP16 MPSGraph Input Findings

**Status:** Isolated validation passed on 2026-09-28. Graph execution was tied,
the input buffer was halved, and the first loaded MESS capture pair was also
tied. A controlled clean comparison remains pending.

## Change

The candidate keeps the pinned Depth Anything V2 Small checkpoint, classic
decomposed attention, optimized depth head, 448 x 336 shape, FP16 compute
precision, ImageNet normalization, and output scale. It changes the graph input
from planar FP32 RGB to planar FP16 RGB while retaining the 0...255 range.

| Property | Baseline | Candidate |
| --- | --- | --- |
| Input | FP32 `[1, 3, 336, 448]` | FP16 `[1, 3, 336, 448]` |
| Output | FP16 `[1, 1, 336, 448]` | FP16 `[1, 1, 336, 448]` |
| Input-buffer bytes | 1,806,336 | 903,168 |
| Leading graph operations | FP32 scale, cast to FP16 | FP16 scale |
| Attention | 24 matmul, 12 softmax | Same |
| Weights | Pinned DA2 Small checkpoint | Same checkpoint |

The exporter removes one input cast without changing the 24-matmul/12-softmax
attention graph. See the [raw MIL inventory](da2-fp16-input/mil-operation-inventory.json)
and [experiment metadata](da2-fp16-input/experiment.json).
Rebuilding the original image-input branch through the refactored exporter also
produced exact output on all three fixtures; see the
[control report](da2-fp16-input/image-control-validation.json).

## Numerical validation

The Core ML candidate was compared with the image-input baseline using CPU plus
GPU on three deterministic inputs. It passed a maximum absolute-error threshold
of `0.02` and normalized-RMSE threshold of `0.002`.

| Input | Maximum absolute error | Normalized RMSE | PSNR |
| --- | ---: | ---: | ---: |
| Gradient | 0.004883 | 0.000497 | 61.86 dB |
| Checker | 0 | 0 | exact |
| Random seed 0 | 0.005859 | 0.000706 | 55.36 dB |

The paired MPSGraph comparison also passed: maximum absolute error was
`0.005859`, normalized RMSE was `0.000601`, and PSNR was `56.78 dB` for its
fixed planar input.

## MPSGraph timing

The standalone macOS 27 harness used `.level0`, 20 warmups, alternating package
order, and synchronous GPU completion on an M1 Max. These timings include graph
encoding, submission, and completion. They exclude texture resizing, RGB
packing, depth unpacking, and output upscale.

| Run | Iterations | FP32 median | FP16 median | FP16 change | FP32 p90 | FP16 p90 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [1](da2-fp16-input/mpsgraph-comparison-run1.json) | 200 | 11.89 ms | 11.93 ms | 0.3% slower | 12.12 ms | 12.17 ms |
| [2](da2-fp16-input/mpsgraph-comparison-run2.json) | 100 | 11.89 ms | 11.91 ms | 0.2% slower | 12.14 ms | 12.22 ms |
| [3](da2-fp16-input/mpsgraph-comparison-run3.json) | 100 | 11.96 ms | 11.95 ms | 0.1% faster | 12.09 ms | 12.15 ms |

Graph execution is effectively tied. The candidate's remaining hypothesis is
lower Metal pack cost and input-buffer traffic in the complete MESS path.

## Initial loaded MESS comparison

A user-run pair with active foreground and face analysis measured `29.56 ms`
median complete depth-source latency for FP32 input and `29.62 ms` for FP16.
Model medians were `29.19 ms` and `29.37 ms`, respectively, while median
presentation was `57.88 fps` and `57.91 fps`. The candidate did not demonstrate
an application-level speed improvement in this pair.

Both captures ran longer than 34 seconds, ended normally, and dropped no log
events. They did not record the exact source segment or effect workload, and
face count varied. See the [full comparison and raw captures](../realtime-depth-macos27/loaded-fp16-comparison-2026-09-28.md).

## Core ML timing and compute plan

The tensor-input package was 13.8–14.0% slower by median in the Python Core ML
comparison. That comparison uses different host bridges: PIL image input for the
baseline and an `MLMultiArray`-compatible NumPy tensor for the candidate. MESS
does not offer the candidate as a Core ML engine, so this result is recorded as
context rather than an adoption metric. Raw reports are adjacent to the graph
reports.

The [candidate compute plan](da2-fp16-input/compute-plan.md) removes the input
cast and estimates 98.24% Neural Engine cost under CPU plus Neural Engine,
similar to the baseline's 98.03%. CPU plus GPU places all reported-cost
operations on the GPU. These estimates are not runtime traces.

## Qualitative example

This MESS-rendered frame confirms that the optional 448 x 336 FP16-input
MPSGraph engine produces a useful depth-driven contour treatment. It is a
qualitative example, not a matched raw-depth comparison or performance result;
the surrounding effect chain contributes to the rendered image.

![MESS frame using Depth Anything V2 Small at 448 x 336 with an FP16 MPSGraph input](../../images/examples/da2-448x336-fp16-mpsgraph.png)

## Required realtime comparison

Use a Release build, the same prerecorded source, and the same effect settings
for separate app launches:

1. Run `DEPTH V2 GRAPH` without competing foreground or face analysis.
2. Run `DEPTH DA2 F16 GRAPH` with the same unloaded configuration.
3. Repeat both with the normal foreground-mask and face workload if a
   controlled confirmation of the initial tied loaded pair is needed.
4. Let warmup finish and capture at least 30 seconds per run.
5. Compare median/p90 depth model time, complete depth-source time, delivered
   depth completions, presentation rate, superseded requests, and working-set
   memory.

Retain the candidate only if complete depth-source time or delivered cadence
improves without a visible depth regression. The graph-only result does not
justify changing the default.
