# ZipDepth FP16 MPSGraph Input Findings

**Status:** Isolated validation passed at 384 x 384 and 896 x 512 on 2026-09-28.
The optional MESS variants build successfully; realtime app comparison remains
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
which require the complete MESS measurement. See the
[raw Core ML report](fp16-input-896x512/coreml-validation.json) and adjacent
MPSGraph reports.

## MESS integration

MESS now has optional graph-only `ZIP 384 F16` and `ZIP 896 F16` engines. Their
Metal pack kernel writes FP16 planar values directly. `MessDepthEngineKit`
allocates each input buffer and constructs its graph tensor from the model's
declared input data type. The candidates are not offered as Core ML engines
because the existing Core ML backend accepts image input.

The workspace Debug build passed and generated the candidate
`.mpsgraphpackage`; the app was not launched during implementation.

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

For each run, allow warmup to finish and collect at least 30 seconds of the
diagnostic stream. Record median/p90 depth model time, complete depth-source
time, delivered depth completions, presentation rate, superseded requests, and
working-set memory. Also capture a matched frame for qualitative review.

Retain the candidate when complete depth-source time and delivered cadence
improve without a visible depth regression. The standalone graph result alone
does not justify replacing the baseline default.
