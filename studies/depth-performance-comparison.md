# Depth performance comparison

**Updated:** 2026-09-28

This page collects every performance result currently checked into
DepthStudies. Results are separated by harness because absolute times from the
MESS realtime session, synchronous MPSGraph harness, and Python/Core ML bridge
are not interchangeable. Compare variants within the same row or capture pair
before comparing values across sections.

## Realtime MESS captures

### Earlier loaded MPSGraph captures

The earlier 11 realtime captures used MPSGraph and contained active
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
and [test TODO list](../TEST_TODO_LIST.md) for the test protocol and follow-ups.

### Controlled depth-only captures

These twenty-three accepted captures used the 20-second CLEAN contract. Every
run ended normally with zero dropped events, recorded no foreground or face
timing, and linked a valid 1920 x 1080 snapshot. Timing values are
`median / p90 / p99`.

#### Top performers

The winner for each model and input shape is the backend with the lowest median
complete depth-source latency. Latency is rounded to one decimal place. The
macOS column gives the supported MESS app target for the selected artifact;
all captures were measured on macOS 27. The [compatibility note](realtime-depth-macos27/compatibility.md)
separates model declarations, graph targets, and tested runtime versions.

| Variant | Backend | Minimum macOS target | Latency | Example |
| --- | --- | ---: | ---: | --- |
| [Depth Anything V2 448 x 336](realtime-depth-macos27/captures/DA2_448x336_MPSGRAPH_FP32_CLEAN) | MPSGraph FP32 | 27+ | 15.4 ms | <img src="../images/examples/da2-448x336-mpsgraph-fp32-clean.png" width="240" alt="Depth Anything V2 448 x 336 MPSGraph FP32"> |
| [Depth Anything 3 Small 392 x 392](realtime-depth-macos27/captures/DA3_392x392_MPSGRAPH_FP32_CLEAN) | MPSGraph FP32 | 27+ | 15.5 ms | <img src="../images/examples/da3-392x392-mpsgraph-fp32-clean.png" width="240" alt="Depth Anything 3 Small 392 x 392 MPSGraph FP32"> |
| [Depth Anything 3 Small 518 x 518](realtime-depth-macos27/captures/DA3_518x518_COREML_CLEAN) | Core ML | 15+ | 48.6 ms | <img src="../images/examples/da3-518x518-coreml-clean.png" width="240" alt="Depth Anything 3 Small 518 x 518 Core ML"> |
| [ZipDepth 384 x 384](realtime-depth-macos27/captures/ZIP_384x384_MPSGRAPH_FP32_CLEAN) | MPSGraph FP32 | 27+ | 5.8 ms | <img src="../images/examples/zipdepth-384x384-mpsgraph-fp32-clean.png" width="240" alt="ZipDepth 384 x 384 MPSGraph FP32"> |
| [ZipDepth 512 x 512](realtime-depth-macos27/captures/ZIP_512x512_MPSGRAPH_FP32_CLEAN) | MPSGraph FP32 | 27+ | 7.8 ms | <img src="../images/examples/zipdepth-512x512-mpsgraph-fp32-clean.png" width="240" alt="ZipDepth 512 x 512 MPSGraph FP32"> |
| [ZipDepth 672 x 384](realtime-depth-macos27/captures/ZIP_672x384_MPSGRAPH_FP32_CLEAN) | MPSGraph FP32 | 27+ | 8.3 ms | <img src="../images/examples/zipdepth-672x384-mpsgraph-fp32-clean.png" width="240" alt="ZipDepth 672 x 384 MPSGraph FP32"> |
| [ZipDepth 896 x 512](realtime-depth-macos27/captures/ZIP_896x512_COREML_CLEAN) | Core ML | 15+ | 10.9 ms | <img src="../images/examples/zipdepth-896x512-coreml-clean.png" width="240" alt="ZipDepth 896 x 512 Core ML"> |
| [ZipDepth 1536 x 864](realtime-depth-macos27/captures/ZIP_1536x864_MPSGRAPH_FP16_CLEAN) | MPSGraph FP16 | 27+ | 15.3 ms | <img src="../images/examples/zipdepth-1536x864-mpsgraph-fp16-clean.png" width="240" alt="ZipDepth 1536 x 864 MPSGraph FP16"> |
| [ZipDepth 1920 x 1088](realtime-depth-macos27/captures/ZIP_1920x1088_MPSGRAPH_FP32_CLEAN) | MPSGraph FP32 | 27+ | 44.3 ms | <img src="../images/examples/zipdepth-1920x1088-mpsgraph-fp32-clean.png" width="240" alt="ZipDepth 1920 x 1088 MPSGraph FP32"> |

#### Complete results

| Capture | Shape | Backend / input | Duration / n | Model latency | Complete depth-source latency | Presentation median | Example |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| [DA2 448](realtime-depth-macos27/captures/DA2_448x336_COREML_CLEAN) | 448 x 336 | Core ML image | 32.60 s / 33 | 15.93 / 16.32 / 16.61 ms | 16.68 / 17.95 / 21.26 ms | 59.996 fps | [PNG](../images/examples/da2-448x336-coreml-clean.png) |
| [DA2 448](realtime-depth-macos27/captures/DA2_448x336_MPSGRAPH_FP32_CLEAN) | 448 x 336 | MPSGraph FP32 | 35.47 s / 36 | 15.17 / 15.46 / 15.65 ms | 15.35 / 15.69 / 15.86 ms | 60.000 fps | [PNG](../images/examples/da2-448x336-mpsgraph-fp32-clean.png) |
| [DA2 448](realtime-depth-macos27/captures/DA2_448x336_MPSGRAPH_FP16_CLEAN) | 448 x 336 | MPSGraph FP16 | 34.81 s / 35 | 15.22 / 15.62 / 15.93 ms | 15.38 / 15.76 / 15.88 ms | 60.008 fps | [PNG](../images/examples/da2-448x336-mpsgraph-fp16-clean.png) |
| [DA3 392](realtime-depth-macos27/captures/DA3_392x392_COREML_CLEAN) | 392 x 392 | Core ML image | 23.47 s / 24 | 15.18 / 15.74 / 17.52 ms | 16.43 / 16.86 / 19.00 ms | 60.006 fps | [PNG](../images/examples/da3-392x392-coreml-clean.png) |
| [DA3 392](realtime-depth-macos27/captures/DA3_392x392_MPSGRAPH_FP32_CLEAN) | 392 x 392 | MPSGraph FP32 | 32.54 s / 33 | 15.40 / 15.67 / 16.41 ms | 15.54 / 15.75 / 18.49 ms | 59.998 fps | [PNG](../images/examples/da3-392x392-mpsgraph-fp32-clean.png) |
| [DA3 518](realtime-depth-macos27/captures/DA3_518x518_COREML_CLEAN) | 518 x 518 | Core ML image | 32.18 s / 32 | 44.73 / 53.55 / 58.00 ms | 48.61 / 54.71 / 61.09 ms | 60.003 fps | [PNG](../images/examples/da3-518x518-coreml-clean.png) |
| [DA3 518](realtime-depth-macos27/captures/DA3_518x518_MPSGRAPH_FP32_CLEAN) | 518 x 518 | MPSGraph FP32 | 34.37 s / 35 | 48.71 / 50.07 / 50.31 ms | 49.79 / 52.66 / 53.77 ms | 60.077 fps | [PNG](../images/examples/da3-518x518-mpsgraph-fp32-clean.png) |
| [ZipDepth 384](realtime-depth-macos27/captures/ZIP_384x384_COREML_CLEAN) | 384 x 384 | Core ML image | 33.90 s / 34 | 7.44 / 7.62 / 7.70 ms | 8.24 / 8.62 / 11.24 ms | 60.007 fps | [PNG](../images/examples/zipdepth-384x384-coreml-clean.png) |
| [ZipDepth 384](realtime-depth-macos27/captures/ZIP_384x384_MPSGRAPH_FP32_CLEAN) | 384 x 384 | MPSGraph FP32 | 33.33 s / 34 | 5.63 / 6.09 / 6.35 ms | 5.78 / 6.44 / 7.20 ms | 59.995 fps | [PNG](../images/examples/zipdepth-384x384-mpsgraph-fp32-clean.png) |
| [ZipDepth 384](realtime-depth-macos27/captures/ZIP_384x384_MPSGRAPH_FP16_CLEAN) | 384 x 384 | MPSGraph FP16 | 33.98 s / 34 | 6.14 / 6.91 / 7.28 ms | 6.37 / 6.80 / 7.01 ms | 59.996 fps | [PNG](../images/examples/zipdepth-384x384-mpsgraph-fp16-clean.png) |
| [ZipDepth 512](realtime-depth-macos27/captures/ZIP_512x512_COREML_CLEAN) | 512 x 512 | Core ML image | 33.85 s / 34 | 9.65 / 10.33 / 10.58 ms | 11.29 / 12.27 / 12.52 ms | 60.003 fps | [PNG](../images/examples/zipdepth-512x512-coreml-clean.png) |
| [ZipDepth 512](realtime-depth-macos27/captures/ZIP_512x512_MPSGRAPH_FP32_CLEAN) | 512 x 512 | MPSGraph FP32 | 34.36 s / 35 | 7.67 / 8.24 / 8.91 ms | 7.84 / 8.49 / 9.34 ms | 59.991 fps | [PNG](../images/examples/zipdepth-512x512-mpsgraph-fp32-clean.png) |
| [ZipDepth 672](realtime-depth-macos27/captures/ZIP_672x384_COREML_CLEAN) | 672 x 384 | Core ML image | 32.62 s / 33 | 9.69 / 10.11 / 10.61 ms | 10.80 / 11.59 / 12.26 ms | 59.996 fps | [PNG](../images/examples/zipdepth-672x384-coreml-clean.png) |
| [ZipDepth 672](realtime-depth-macos27/captures/ZIP_672x384_MPSGRAPH_FP32_CLEAN) | 672 x 384 | MPSGraph FP32 | 34.47 s / 35 | 8.07 / 8.54 / 8.82 ms | 8.26 / 8.86 / 9.30 ms | 59.989 fps | [PNG](../images/examples/zipdepth-672x384-mpsgraph-fp32-clean.png) |
| [ZipDepth 896](realtime-depth-macos27/captures/ZIP_896x512_COREML_CLEAN) | 896 x 512 | Core ML image | 34.20 s / 35 | 9.57 / 10.02 / 11.04 ms | 10.86 / 11.65 / 12.32 ms | 60.007 fps | [PNG](../images/examples/zipdepth-896x512-coreml-clean.png) |
| [ZipDepth 896](realtime-depth-macos27/captures/ZIP_896x512_MPSGRAPH_FP32_CLEAN) | 896 x 512 | MPSGraph FP32 | 32.10 s / 32 | 12.11 / 12.93 / 13.23 ms | 12.67 / 13.36 / 16.81 ms | 59.999 fps | [PNG](../images/examples/zipdepth-896x512-mpsgraph-fp32-clean.png) |
| [ZipDepth 896](realtime-depth-macos27/captures/ZIP_896x512_MPSGRAPH_FP16_CLEAN) | 896 x 512 | MPSGraph FP16 | 32.82 s / 33 | 11.55 / 12.59 / 12.82 ms | 11.55 / 12.75 / 13.30 ms | 59.993 fps | [PNG](../images/examples/zipdepth-896x512-mpsgraph-fp16-clean.png) |
| [ZipDepth 1536](realtime-depth-macos27/captures/ZIP_1536x864_COREML_CLEAN) | 1536 x 864 | Core ML image | 34.63 s / 35 | 34.24 / 34.83 / 35.49 ms | 35.54 / 36.03 / 36.90 ms | 60.002 fps | [PNG](../images/examples/zipdepth-1536x864-coreml-clean.png) |
| [ZipDepth 1536](realtime-depth-macos27/captures/ZIP_1536x864_MPSGRAPH_FP32_CLEAN) | 1536 x 864 | MPSGraph FP32 | 34.93 s / 35 | 15.29 / 19.61 / 22.56 ms | 15.47 / 20.58 / 25.19 ms | 60.007 fps | [PNG](../images/examples/zipdepth-1536x864-mpsgraph-fp32-clean.png) |
| [ZipDepth 1536](realtime-depth-macos27/captures/ZIP_1536x864_MPSGRAPH_FP16_CLEAN) | 1536 x 864 | MPSGraph FP16 | 33.81 s / 34 | 15.17 / 15.40 / 16.72 ms | 15.32 / 15.61 / 16.95 ms | 59.999 fps | [PNG](../images/examples/zipdepth-1536x864-mpsgraph-fp16-clean.png) |
| [ZipDepth 1920](realtime-depth-macos27/captures/ZIP_1920x1088_COREML_CLEAN) | 1920 x 1088 | Core ML image | 33.80 s / 34 | 60.68 / 61.07 / 61.41 ms | 61.70 / 61.98 / 62.29 ms | 60.000 fps | [PNG](../images/examples/zipdepth-1920x1088-coreml-clean.png) |
| [ZipDepth 1920](realtime-depth-macos27/captures/ZIP_1920x1088_MPSGRAPH_FP32_CLEAN) | 1920 x 1088 | MPSGraph FP32 | 33.47 s / 34 | 43.23 / 45.91 / 55.91 ms | 44.27 / 46.60 / 53.21 ms | 59.906 fps | [PNG](../images/examples/zipdepth-1920x1088-mpsgraph-fp32-clean.png) |
| [ZipDepth 1920](realtime-depth-macos27/captures/ZIP_1920x1088_MPSGRAPH_FP16_CLEAN) | 1920 x 1088 | MPSGraph FP16 | 34.18 s / 34 | 43.63 / 46.09 / 47.73 ms | 44.86 / 46.44 / 47.17 ms | 59.429 fps | [PNG](../images/examples/zipdepth-1920x1088-mpsgraph-fp16-clean.png) |

MPSGraph reduced median complete-path latency versus Core ML by `8.0%` for
DA2, `29.9%` at ZipDepth 384 x 384, `30.6%` at ZipDepth 512 x 512, `23.5%` at
ZipDepth 672 x 384, `56.9%` at ZipDepth 1536 x 864 using FP16, and `28.3%` at
ZipDepth 1920 x 1088. Core ML instead won at ZipDepth 896 x 512 with a
`10.86 ms` median. DA2 FP16 was tied with FP32, ZipDepth 384 FP16 was `10.2%`
slower, ZipDepth 896 FP16 was `8.9%` faster, ZipDepth 1536 FP16 materially
improved tail latency, and ZipDepth 1920 FP16 was effectively tied with a lower
presentation median. The duplicate 672 x 384 Core ML run was discarded.

DA3 MPSGraph improved the 392 x 392 median by `5.5%` versus Core ML. At
518 x 518, Core ML improved the median by `2.4%`, while MPSGraph had better p90
and p99 latency.

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

## Clean realtime coverage

The planned CLEAN realtime matrix is complete. Every exposed DA2, DA3, and
ZipDepth Core ML/MPSGraph variant has an accepted capture and snapshot. The
[test TODO list](../TEST_TODO_LIST.md) retains optional loaded-session repeats
and experiments that are not app buttons.
