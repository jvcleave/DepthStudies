# ZipDepth FP16 MPSGraph Input Findings

**Status:** Isolated validation passed at 384 x 384, 896 x 512, 1536 x 864, and
1920 x 1088 on 2026-09-28. The optional MESS variants build successfully.
Logged loaded pairs favor FP16 by `6.2%` at 896 x 512 and `4.1%` at 1536 x 864
in median complete depth-source latency; controlled clean captures remain
pending.

## 384 x 384 change

The candidate `ZipDepthBaseNPU384x384TensorF16` package changes the graph input
from planar FP32 RGB to planar FP16 RGB while retaining the 0...255 range. Pixel
scaling and ImageNet normalization remain inside the model.

| Property | Baseline | Candidate |
| --- | --- | --- |
| Input | FP32 `[1, 3, 384, 384]` | FP16 `[1, 3, 384, 384]` |
| Output | FP16 `[1, 1, 384, 384]` | FP16 `[1, 1, 384, 384]` |
| Input-buffer bytes | 1,769,472 | 884,736 |
| Leading graph operations | FP32 scale, cast to FP16 | FP16 scale |
| Weights | Pinned ZipDepth Base NPU checkpoint | Same checkpoint |

The graph-specific exporter and build entry point are under
`scripts/models/zipdepth/`. The original image-input Core ML package remains
unchanged.

## Numerical validation

The Core ML candidate was compared with the image-input Core ML baseline using
CPU plus GPU on three deterministic 384 x 384 inputs. It passed a maximum
absolute error of `0.0005` and normalized RMSE of `0.002`.

| Input | Maximum absolute error | Normalized RMSE | PSNR |
| --- | ---: | ---: | ---: |
| Gradient | 0.000290 | 0.001662 | 54.14 dB |
| Checker | 0 | 0 | exact |
| Random seed 0 | 0.000183 | 0.000487 | 65.29 dB |

The paired MPSGraph comparison also passed: maximum absolute error was
`0.000244`, normalized RMSE was `0.000840`, and PSNR was `60.45 dB` for its
fixed planar input. See [the raw Core ML report](fp16-input/coreml-validation.json)
and the adjacent MPSGraph run reports.

## Graph-only timing

The standalone macOS 27 harness used `.level0`, 20 warmups, alternating package
order, and synchronous completion on an M1 Max. These timings include graph
encoding, submission, and completion. They exclude texture resize, Metal RGB
packing, depth unpacking, and output upscale.

| Run | Iterations | FP32 median | FP16 median | Median reduction | FP32 p90 | FP16 p90 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [1](fp16-input/mpsgraph-comparison-run1.json) | 200 | 8.04 ms | 5.53 ms | 31.1% | 13.36 ms | 8.13 ms |
| [2](fp16-input/mpsgraph-comparison-run2.json) | 100 | 8.25 ms | 5.25 ms | 36.3% | 13.44 ms | 7.65 ms |
| [3](fp16-input/mpsgraph-comparison-run3.json) | 100 | 7.75 ms | 5.59 ms | 27.8% | 13.41 ms | 7.15 ms |

Absolute times differ from the earlier study harness, so this result supports
only the paired comparison. Across all three runs, the FP16 package reduced the
median and p90 and halved input memory traffic.

## 896 x 512 result

The same export was repeated as `ZipDepthBaseNPU896x512TensorF16`. It retains
the baseline shape and weights while changing only the planar graph input from
FP32 to FP16.

| Property | Baseline | Candidate |
| --- | --- | --- |
| Input | FP32 `[1, 3, 512, 896]` | FP16 `[1, 3, 512, 896]` |
| Output | FP16 `[1, 1, 512, 896]` | FP16 `[1, 1, 512, 896]` |
| Input-buffer bytes | 5,505,024 | 2,752,512 |
| Weights | Pinned ZipDepth Base NPU checkpoint | Same checkpoint |

The Core ML comparison passed the same `0.0005` maximum absolute-error and
`0.002` normalized-RMSE thresholds:

| Input | Maximum absolute error | Normalized RMSE | PSNR |
| --- | ---: | ---: | ---: |
| Gradient | 0.000397 | 0.000921 | 60.72 dB |
| Checker | 0 | 0 | exact |
| Random seed 0 | 0.000153 | 0.000405 | 67.14 dB |

The paired graph comparison also passed with maximum absolute error `0.000305`,
normalized RMSE `0.000767`, and PSNR `59.34 dB`. Unlike the 384 experiment,
graph-only execution was effectively tied:

| Run | Iterations | FP32 median | FP16 median | FP32 p90 | FP16 p90 |
| --- | ---: | ---: | ---: | ---: | ---: |
| [1](fp16-input-896x512/mpsgraph-comparison-run1.json) | 200 | 6.00 ms | 5.98 ms | 10.00 ms | 9.84 ms |
| [2](fp16-input-896x512/mpsgraph-comparison-run2.json) | 100 | 5.86 ms | 5.84 ms | 6.04 ms | 6.08 ms |
| [3](fp16-input-896x512/mpsgraph-comparison-run3.json) | 100 | 6.42 ms | 6.42 ms | 9.29 ms | 8.76 ms |

The 896 candidate therefore has no demonstrated graph-inference advantage. Its
remaining hypotheses are lower Metal pack cost and lower input-buffer traffic,
which motivated the complete MESS measurement below. See the
[raw Core ML report](fp16-input-896x512/coreml-validation.json) and adjacent
MPSGraph reports.

### Initial loaded MESS comparison

A user-run pair with active foreground and face analysis measured `8.72 ms`
median complete depth-source latency for FP32 input and `8.18 ms` for FP16, a
`0.54 ms` or `6.2%` reduction. Model latency changed from `8.61 ms` to
`8.00 ms`, while both variants held a `60.00 fps` presentation median.

The FP16 complete-path p90 increased from `9.24 ms` to `9.58 ms`, and p99
increased from `9.49 ms` to `12.90 ms`. Both captures ended normally and
dropped no log events, but the exact source and effect workload were not
recorded. Treat the median improvement as promising and repeat the pair under
the controlled contract before selecting a default. See the
[second-batch report and raw captures](../realtime-depth-macos27/loaded-zipdepth-batch-2-2026-09-28.md).

## High-resolution results

The FP16 input export was also applied at 1536 x 864 and 1920 x 1088. Both use
the same pinned weights as their FP32-input baselines.

| Shape | FP32 input bytes | FP16 input bytes | Core ML maximum absolute error | Core ML maximum normalized RMSE |
| --- | ---: | ---: | ---: | ---: |
| 1536 x 864 | 15,925,248 | 7,962,624 | 0.000259 | 0.000516 |
| 1920 x 1088 | 25,067,520 | 12,533,760 | 0.000305 | 0.000576 |

Both passed the established numerical thresholds. Their paired graph-only
execution was effectively tied, as it was at 896 x 512:

| Shape | Run | Iterations | FP32 median | FP16 median | FP32 p90 | FP16 p90 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1536 x 864 | [1](fp16-input-1536x864/mpsgraph-comparison-run1.json) | 200 | 14.95 ms | 14.95 ms | 18.36 ms | 18.76 ms |
| 1536 x 864 | [2](fp16-input-1536x864/mpsgraph-comparison-run2.json) | 100 | 15.29 ms | 15.46 ms | 20.15 ms | 18.78 ms |
| 1536 x 864 | [3](fp16-input-1536x864/mpsgraph-comparison-run3.json) | 100 | 14.78 ms | 14.68 ms | 18.13 ms | 18.01 ms |
| 1920 x 1088 | [1](fp16-input-1920x1088/mpsgraph-comparison-run1.json) | 200 | 21.93 ms | 21.90 ms | 24.74 ms | 25.29 ms |
| 1920 x 1088 | [2](fp16-input-1920x1088/mpsgraph-comparison-run2.json) | 100 | 21.85 ms | 22.00 ms | 24.87 ms | 25.82 ms |
| 1920 x 1088 | [3](fp16-input-1920x1088/mpsgraph-comparison-run3.json) | 100 | 22.19 ms | 21.91 ms | 25.61 ms | 25.52 ms |

The graph comparisons passed too. At 1536 x 864, maximum absolute error was
`0.000366` and normalized RMSE was `0.000681`. At 1920 x 1088, they were
`0.000397` and `0.000682`. See the raw Core ML reports in
[fp16-input-1536x864](fp16-input-1536x864/coreml-validation.json) and
[fp16-input-1920x1088](fp16-input-1920x1088/coreml-validation.json).

## Initial 1536 x 864 loaded MESS comparison

A user-run pair with active foreground and face analysis measured `29.46 ms`
median complete depth-source latency for FP32 input and `28.27 ms` for FP16, a
`1.19 ms` or `4.1%` reduction. Model latency changed from `26.55 ms` to
`26.31 ms`, while median presentation changed from `50.79 fps` to `51.03 fps`.
The larger complete-path improvement is consistent with reduced packing or
input traffic, although those stages are not timed separately. Complete-path
p90 remained tied near `31.8 ms`.

Both captures ran longer than 35 seconds, ended normally, and dropped no log
events. They did not record the exact source segment or effect workload, and
face count varied. Treat this as directional evidence for retaining the 1536
FP16 option. See the [full comparison and raw captures](../realtime-depth-macos27/loaded-fp16-comparison-2026-09-28.md).

## MESS integration

MESS now has optional graph-only `ZIP 384 F16`, `ZIP 896 F16`, `ZIP 1536 F16`,
and `ZIP 1080 F16` engines. Their Metal pack kernel writes FP16 planar values
directly. `MessDepthEngineKit` allocates each input buffer and constructs its
graph tensor from the model's declared input data type. The candidates are not
offered as Core ML engines because the existing Core ML backend accepts image
input.

The workspace Debug build passed and generated the candidate graph packages;
the app was not launched during implementation.

## Required realtime comparison

Run the following pairs in Release mode with the same prerecorded source and
effect settings, using a separate app launch for each engine:

1. `ZIP 384 GRAPH` with no competing foreground or face analysis.
2. `ZIP 384 F16 GRAPH` with the same unloaded configuration.
3. Repeat both with the normal foreground-mask and face workload if that is a
   representative session.
4. Repeat the same pair for `ZIP 896 GRAPH` and `ZIP 896 F16 GRAPH`; the 896
   graph-only result was tied, so this pair specifically tests pack cost and
   complete depth-source latency.
5. Compare `ZIP 1536 GRAPH` with `ZIP 1536 F16 GRAPH`, then `ZIP 1080 GRAPH`
   with `ZIP 1080 F16 GRAPH`. These larger pairs test whether the observed 896
   application-level improvement grows with input-buffer size.

For each run, allow warmup to finish and collect at least 30 seconds of the
diagnostic stream. Record median/p90 depth model time, complete depth-source
time, delivered depth completions, presentation rate, superseded requests, and
working-set memory. Also capture a matched frame for qualitative review.

Retain the candidate when complete depth-source time and delivered cadence
improve without a visible depth regression. The standalone graph result alone
does not justify replacing the baseline default.
