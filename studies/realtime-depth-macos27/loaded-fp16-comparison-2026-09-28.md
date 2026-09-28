# Loaded FP16 MPSGraph comparison, 2026-09-28

Four user-run MESS diagnostic captures compare planar FP32 and FP16 MPSGraph
inputs under an active foreground and face-analysis workload. Every capture ran
for at least 34 seconds, ended normally, and reported zero dropped diagnostic
events.

The embedded configuration identifies the exact depth variant, input type,
fixed shape, MPSGraph backend, MPSMediaPipe face backend, and 60 fps session
target. The capture format does not record the source segment, effect preset,
complete enabled-analysis set, build identity, host identity, or working-set
memory. These are useful paired observations, but they do not complete the
controlled test contract in `TEST_TODO_LIST.md`.

## Results

The table excludes the initial sample before one second. Depth latency is
recovered from each sampled fps-equivalent value before calculating the
percentiles.

| Model and graph input | Duration | Samples | Model median / p90 / p99 | Complete depth-source median / p90 / p99 | Median presentation |
| --- | ---: | ---: | ---: | ---: | ---: |
| DA2 448 x 336 FP32 | 35.45 s | 36 | 29.19 / 31.50 / 32.38 ms | 29.56 / 31.50 / 32.86 ms | 57.88 fps |
| DA2 448 x 336 FP16 | 34.89 s | 35 | 29.37 / 31.45 / 33.29 ms | 29.62 / 31.72 / 33.77 ms | 57.91 fps |
| ZipDepth 1536 x 864 FP32 | 35.67 s | 36 | 26.55 / 30.69 / 31.65 ms | 29.46 / 31.80 / 32.48 ms | 50.79 fps |
| ZipDepth 1536 x 864 FP16 | 42.12 s | 42 | 26.31 / 30.84 / 31.66 ms | 28.27 / 31.76 / 32.35 ms | 51.03 fps |

DA2 was tied. FP16 changed median model latency by `+0.19 ms` and median
complete depth-source latency by `+0.05 ms`, both slightly slower. Median
presentation changed by `+0.03 fps`. These differences are too small to
support selecting either graph input from this run.

ZipDepth FP16 reduced median model latency by `0.24 ms` (`0.9%`) and median
complete depth-source latency by `1.19 ms` (`4.1%`). Median presentation was
`0.24 fps` higher. The larger change in complete depth-source time is
consistent with the reduced packing and input-traffic hypothesis, although the
capture does not time packing separately. The complete depth-source p90 values
were effectively tied at `31.80 ms` for FP32 and `31.76 ms` for FP16.

## Workload context

| Model and graph input | Foreground model median | Face latency median | Observed face count |
| --- | ---: | ---: | ---: |
| DA2 448 x 336 FP32 | 18.01 ms | 34.81 ms | 0–4 |
| DA2 448 x 336 FP16 | 18.02 ms | 34.70 ms | 1–4 |
| ZipDepth 1536 x 864 FP32 | 18.98 ms | 39.56 ms | 0–4 |
| ZipDepth 1536 x 864 FP16 | 18.41 ms | 39.07 ms | 0–4 |

Median competing-work timings were close within each pair, while face count
varied during the captures. The results remain directional until the same
prerecorded source segment and exact workload settings are recorded. The
current stream also lacks delivered-depth completion and superseded-request
counts, so these captures cannot establish delivered depth cadence or
scheduling behavior.

## Raw captures

- [DA2 448 x 336 FP32 MPSGraph, loaded](captures/DA2_448x336_MPSGRAPH_FP32_LOADED)
- [DA2 448 x 336 FP16 MPSGraph, loaded](captures/DA2_448x336_MPSGRAPH_FP16_LOADED)
- [ZipDepth 1536 x 864 FP32 MPSGraph, loaded](captures/ZIP_1536x864_MPSGRAPH_FP32_LOADED)
- [ZipDepth 1536 x 864 FP16 MPSGraph, loaded](captures/ZIP_1536x864_MPSGRAPH_FP16_LOADED)

Reproduce the summaries with:

```sh
python3 scripts/summarize_capture.py \
  studies/realtime-depth-macos27/captures/DA2_448x336_MPSGRAPH_FP32_LOADED
```
