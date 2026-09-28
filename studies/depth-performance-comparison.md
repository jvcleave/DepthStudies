# Depth performance comparison

**Updated:** 2026-09-28

This page collects every performance result currently checked into
DepthStudies. Results are separated by harness because absolute times from the
MESS realtime session, synchronous MPSGraph harness, and Python/Core ML bridge
are not interchangeable. Compare variants within the same row or capture pair
before comparing values across sections.

## Realtime MESS captures

All 11 checked-in realtime captures used MPSGraph and contained active
foreground and face-analysis timing. None is a CLEAN run under the current test
contract. The table converts each sampled fps-equivalent depth metric back to
milliseconds and then calculates percentiles. Model and complete depth-source
fields are sampled independently.

Values in the two latency columns are `median / p90 / p99`. `n` excludes the
initial sample before one second. Every capture ended normally with zero
dropped diagnostic events.

| Capture | Shape | Input | Duration / n | Model latency | Complete depth-source latency | Presentation median | Foreground / face median |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| [DA2 legacy](realtime-depth-macos27/captures/DA2_MPS)† | Not recorded | Not recorded | 29.78 s / 30 | 17.01 / 20.42 / 55.41 ms | 17.23 / 21.04 / 56.25 ms | 60.02 fps | 19.71 / 21.52 ms |
| [DA2 FP32](realtime-depth-macos27/captures/DA2_448x336_MPSGRAPH_FP32_LOADED) | 448 x 336 | FP32 | 35.45 s / 36 | 29.19 / 31.50 / 32.38 ms | 29.56 / 31.50 / 32.86 ms | 57.88 fps | 18.01 / 34.81 ms |
| [DA2 FP16](realtime-depth-macos27/captures/DA2_448x336_MPSGRAPH_FP16_LOADED) | 448 x 336 | FP16 | 34.89 s / 35 | 29.37 / 31.45 / 33.29 ms | 29.62 / 31.72 / 33.77 ms | 57.91 fps | 18.02 / 34.70 ms |
| [DA3 Small legacy](realtime-depth-macos27/captures/DA3_SM_MPS)† | Not recorded | Not recorded | 15.24 s / 16 | 33.77 / 39.10 / 41.82 ms | 32.17 / 39.33 / 41.99 ms | 56.71 fps | 17.78 / 38.86 ms |
| [ZipDepth legacy](realtime-depth-macos27/captures/ZIP_MPS)† | Not recorded | Not recorded | 13.52 s / 14 | 5.29 / 5.32 / 5.33 ms | 5.44 / 5.49 / 5.62 ms | 60.00 fps | 18.01 / 9.13 ms |
| [ZipDepth FP32](realtime-depth-macos27/captures/ZIP_512x512_MPSGRAPH_FP32_LOADED) | 512 x 512 | FP32 | 34.49 s / 35 | 6.49 / 7.40 / 8.46 ms | 6.69 / 7.54 / 8.62 ms | 60.01 fps | 21.73 / 10.89 ms |
| [ZipDepth FP32](realtime-depth-macos27/captures/ZIP_672x384_MPSGRAPH_FP32_LOADED) | 672 x 384 | FP32 | 37.57 s / 38 | 5.82 / 7.57 / 8.10 ms | 5.97 / 7.84 / 8.24 ms | 60.00 fps | 17.55 / 10.59 ms |
| [ZipDepth FP32](realtime-depth-macos27/captures/ZIP_896x512_MPSGRAPH_FP32_LOADED) | 896 x 512 | FP32 | 35.12 s / 36 | 8.61 / 8.98 / 9.34 ms | 8.72 / 9.24 / 9.49 ms | 60.00 fps | 17.66 / 12.35 ms |
| [ZipDepth FP16](realtime-depth-macos27/captures/ZIP_896x512_MPSGRAPH_FP16_LOADED) | 896 x 512 | FP16 | 37.59 s / 38 | 8.00 / 8.95 / 12.01 ms | 8.18 / 9.58 / 12.90 ms | 60.00 fps | 19.47 / 11.83 ms |
| [ZipDepth FP32](realtime-depth-macos27/captures/ZIP_1536x864_MPSGRAPH_FP32_LOADED) | 1536 x 864 | FP32 | 35.67 s / 36 | 26.55 / 30.69 / 31.65 ms | 29.46 / 31.80 / 32.48 ms | 50.79 fps | 18.98 / 39.56 ms |
| [ZipDepth FP16](realtime-depth-macos27/captures/ZIP_1536x864_MPSGRAPH_FP16_LOADED) | 1536 x 864 | FP16 | 42.12 s / 42 | 26.31 / 30.84 / 31.66 ms | 28.27 / 31.76 / 32.35 ms | 51.03 fps | 18.41 / 39.07 ms |

† The three 2026-09-25 legacy captures predate `capture.configuration`.
Their engine identities come from user-assigned directory names, and their
shape and graph-input type cannot be recovered from the logs. The eight
2026-09-28 captures embed the exact variant, backend, input type, and shape.

The configured pair observations so far are:

- DA2 448 x 336 FP16 was tied with FP32 at the complete-path median.
- ZipDepth 896 x 512 FP16 improved the complete-path median by `6.2%`, but its
  p90 and p99 were worse.
- ZipDepth 1536 x 864 FP16 improved the complete-path median by `4.1%`, with an
  effectively tied p90 and p99.
- The 512 x 512 and 672 x 384 rows are separate loaded observations. Their
  foreground timings differ enough that they do not establish a shape-only
  performance difference.

See the [first configured capture report](realtime-depth-macos27/loaded-fp16-comparison-2026-09-28.md),
[second ZipDepth report](realtime-depth-macos27/loaded-zipdepth-batch-2-2026-09-28.md),
and [test TODO list](../TEST_TODO_LIST.md) for the remaining controlled runs.

## Paired standalone experiments

These rows aggregate three alternating trials from each study. Each displayed
statistic is the median of that statistic across the three runs. The MPSGraph
harness uses synchronous completion and excludes texture resize, Metal packing,
unpacking, and output upscale. The Core ML rows include their documented host
bridge. Compare only within a row. Timing values are `median / p90 / p99`.

| Study | Runtime | Shape | Baseline timing | Candidate timing | Result |
| --- | --- | ---: | ---: | ---: | --- |
| [DA2 classic vs native SDPA](apple-silicon-depth-optimization/da2-sdpa-findings.md) | Core ML CPU + GPU | 448 x 336 | Classic 16.82 / 18.11 / 18.91 ms | SDPA 17.24 / 18.32 / 18.84 ms | SDPA slower; rejected |
| [DA2 classic vs native SDPA](apple-silicon-depth-optimization/da2-sdpa-findings.md) | MPSGraph | 448 x 336 | Classic 11.90 / 12.13 / 12.33 ms | SDPA 12.39 / 12.62 / 12.78 ms | SDPA slower; rejected |
| [DA2 FP32 vs FP16 graph input](apple-silicon-depth-optimization/da2-fp16-input-findings.md) | MPSGraph | 448 x 336 | FP32 11.89 / 12.12 / 12.28 ms | FP16 11.93 / 12.17 / 12.40 ms | Tied |
| [DA2 image vs FP16 tensor input](apple-silicon-depth-optimization/da2-fp16-input-findings.md) | Core ML CPU + GPU | 448 x 336 | Image 18.21 / 19.66 / 21.79 ms | Tensor 20.73 / 22.04 / 23.25 ms | Tensor slower; bridges differ |
| [ZipDepth FP32 vs FP16 graph input](apple-silicon-depth-optimization/fp16-input-findings.md) | MPSGraph | 384 x 384 | FP32 8.04 / 13.41 / 18.72 ms | FP16 5.53 / 7.65 / 13.56 ms | FP16 faster |
| [ZipDepth FP32 vs FP16 graph input](apple-silicon-depth-optimization/fp16-input-findings.md) | MPSGraph | 896 x 512 | FP32 6.00 / 9.29 / 10.92 ms | FP16 5.98 / 8.76 / 10.42 ms | Median tied |
| [ZipDepth FP32 vs FP16 graph input](apple-silicon-depth-optimization/fp16-input-findings.md) | MPSGraph | 1536 x 864 | FP32 14.95 / 18.36 / 22.41 ms | FP16 14.95 / 18.76 / 23.16 ms | Tied |
| [ZipDepth FP32 vs FP16 graph input](apple-silicon-depth-optimization/fp16-input-findings.md) | MPSGraph | 1920 x 1088 | FP32 21.93 / 24.87 / 31.04 ms | FP16 21.91 / 25.52 / 29.67 ms | Tied |

All conversion-quality gates for these candidates passed. Numerical-error
tables and individual-run links remain in the study pages.

## DA3 Core ML compute-unit sweep

This dedicated 392 x 392 harness loaded all three configured Core ML instances,
rotated their execution order, and collected 100 timed predictions after 20
warmups. Values are medians of the three reported run statistics.

| Compute units | Median | p90 | p99 | Decision |
| --- | ---: | ---: | ---: | --- |
| CPU + GPU | 24.15 ms | 27.42 ms | 29.83 ms | Retained |
| CPU + Neural Engine | 30.12 ms | 31.09 ms | 32.86 ms | 24.7% slower; rejected |
| All | 29.77 ms | 31.14 ms | 32.62 ms | 23.3% slower; rejected |

See the [DA3 compute-unit findings](apple-silicon-depth-optimization/da3-compute-unit-findings.md)
for per-run values, output agreement, and protocol details.

## Earlier standalone reference medians

These recorded medians came from earlier small harnesses. Some raw per-call
samples are unavailable, and the protocols differ, so the table preserves
historical route comparisons rather than forming a cross-model ranking.

| Model | Shape | Core ML route and median | MPSGraph median | Recorded conclusion |
| --- | ---: | --- | ---: | --- |
| ZipDepth Base NPU | 384 x 384 | All 2.56 ms; CPU + Neural Engine 3.48 ms; CPU + GPU 12.96 ms | 3.48 ms | Motivated the ZipDepth residency and graph studies |
| DA2 Small | 448 x 336 | CPU + GPU 14.86 ms | 14.50 ms | Similar GPU routes |
| DA2 Small | 448 x 336 | CPU + Neural Engine 23.01 ms | 15.51 ms | Keep Core ML on CPU + GPU |
| DA3 Small | 392 x 392 | CPU + GPU 16.69 ms | 15.22 ms | Similar small-shape routes in this harness |
| DA3 Small | 518 x 518 | CPU + GPU 23.94 ms | 40.40 ms | Core ML faster at the larger shape |

The newer DA3 compute-unit sweep supersedes the earlier 392 x 392 value for
choosing Core ML compute units. It does not replace that historical backend
comparison because its runtime state and protocol differ.

## Missing realtime rows

No configured realtime capture has yet been checked in for ZipDepth 384 x 384,
ZipDepth 1920 x 1088, either DA3 fixed shape, or any Core ML app route. CLEAN
FP32/FP16 pairs also remain pending. Those gaps stay explicit in the
[test TODO list](../TEST_TODO_LIST.md).
