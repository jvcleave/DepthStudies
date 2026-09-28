# Realtime depth through MPSGraph on macOS 27

Recorded 2026-09-25 on an Apple M1 Max running macOS 27.0 with Xcode 27.0
(build 27A266a). The MESS realtime session targeted 60 fps and used the
MPSMediaPipe face backend.

## Realtime MPSGraph capture results

ZipDepth had the lowest depth cost in the captured MESS sessions. Depth Anything
V2 held the 60 fps presentation target with a median complete depth-source cost
of 17.23 ms. The user-labelled DA3 Small run was the heaviest and presented at a
56.71 fps median over its 60-frame window. All three rows below used the
MPSGraph backend; this table contains no Core ML measurements.

| MPSGraph engine | Capture duration | Samples | Median model time | Median depth-source time | Median presentation rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| DA3 Small (`DA3_SM_MPS`) | 15.24 s | 16 | 33.77 ms | 32.17 ms | 56.71 fps |
| Depth Anything V2 (`DA2_MPS`) | 29.78 s | 30 | 17.01 ms | 17.23 ms | 60.02 fps |
| ZipDepth Base NPU (`ZIP_MPS`) | 13.52 s | 14 | 5.29 ms | 5.44 ms | 60.00 fps |

Compared with the captured DA3 run, ZipDepth's median model time was about 6.4x
faster and its median complete depth-source time was about 5.9x faster. DA2's
complete depth-source median was about 1.9x faster than captured DA3 and 3.2x
slower than ZipDepth.

## How the realtime capture was measured

MESS instrumented each completed depth request while its diagnostic capture was
active. For MPSGraph, model time spans graph encoding through the graph completion
callback and can include queued preprocessing dependencies. Complete depth-source
time runs from the app worker's request start through the completed graph result;
the graph realtime path reports only after its final GPU command buffer finishes.

The capture wrote the latest timing values approximately once per second as fps
equivalents computed by `1000 / operation_ms`. The summarizer:

1. reads `streams/engine-stats.jsonl`;
2. excludes the initial sample where `elapsed_s < 1`;
3. converts each operation's sampled fps equivalent back to milliseconds; and
4. takes the median of those per-sample milliseconds. Presentation rate remains
   the median of its sampled fps values.

These values describe sampled operation latency. They are not counts of delivered
depth frames. The presentation rate is MESS's rolling 60-frame presentation
average sampled at the same interval. Model and depth-source fields are updated
by adjacent callbacks and sampled independently, so their medians can appear
slightly out of order.

Run the checked-in summarizer against a raw capture with:

```sh
python3 scripts/summarize_capture.py \
  studies/realtime-depth-macos27/captures/DA2_MPS
```

## Limits on comparison

This was not a controlled replay. The DA3 capture saw zero to four faces per
sample with 38.86 ms median face latency. DA2 saw zero to two faces with 21.52 ms
median face latency. ZipDepth saw one to two faces with 9.13 ms median face
latency. DA2 and DA3 each recorded one source-frame decode failure.

Foreground model time remained in the same range: 17.78 ms for DA3, 19.71 ms for
DA2, and 18.01 ms for ZipDepth. That supports attributing the large depth timing
differences to the depth backends, while the presentation-rate difference remains
directional.

Capture metadata did not record the selected depth model or backend. The row
identities therefore come from the user-assigned directory names. In particular,
the DA3 capture does not prove whether the 392 x 392 or 518 x 518 variant was
active.

## Qualitative fixed-shape samples

These user-supplied 1920 x 1080 MESS renders show the current fixed-shape model
options. The five ZipDepth rows use ZipDepth Base NPU. The DA2 and DA3 rows use
Depth Anything V2 Small and Depth Anything 3 Small, respectively. The rendered
treatment, source material, and surrounding effect chain contribute to the
visible result, so these are qualitative samples rather than controlled
raw-depth accuracy comparisons.

The original six capture filenames record the model family and fixed shape, but
not the selected Core ML or MPSGraph backend. The later 1920 x 1088 sample was
explicitly recorded as MPSGraph. No backend comparison should be inferred from
these rendered samples alone.

| Model | Fixed shape | Model pixels | Backend | Sample |
| --- | ---: | ---: | --- | --- |
| ZipDepth Base NPU | 384 x 384 | 147,456 | Not recorded | ![ZipDepth 384 x 384 sample](../../images/examples/zipdepth-384x384.png) |
| ZipDepth Base NPU | 512 x 512 | 262,144 | Not recorded | ![ZipDepth 512 x 512 sample](../../images/examples/zipdepth-512x512.png) |
| ZipDepth Base NPU | 672 x 384 | 258,048 | Not recorded | ![ZipDepth 672 x 384 sample](../../images/examples/zipdepth-672x384.png) |
| ZipDepth Base NPU | 896 x 512 | 458,752 | Not recorded | ![ZipDepth 896 x 512 sample](../../images/examples/zipdepth-896x512.png) |
| ZipDepth Base NPU | 1920 x 1088 | 2,088,960 | MPSGraph | ![ZipDepth 1920 x 1088 MPSGraph sample](../../images/examples/zipdepth-1920x1088-mpsgraph.png) |
| Depth Anything V2 Small | 448 x 336 | 150,528 | Not recorded | ![Depth Anything V2 448 x 336 sample](../../images/examples/da2-448x336.png) |
| Depth Anything 3 Small | 518 x 518 | 268,324 | Not recorded | ![Depth Anything 3 518 x 518 sample](../../images/examples/da3-518x518.png) |

## Standalone DA2 compute-unit comparisons

The DA2 Core ML compute-unit results came from synchronous still-image harnesses,
not the realtime MESS captures above. Both comparisons used the same custom
`DepthAnythingV2SmallRealtime` package at 448 x 336 and an MPSGraph executable
compiled with `.level0`. Input preparation and output readback were outside the
timed calls.

| Comparison | Core ML compute units | Source and sampling | Core ML median | Paired MPSGraph median |
| --- | --- | --- | ---: | ---: |
| GPU | `.cpuAndGPU` | Eight images (`demo04`, `demo05`, `demo10`, `demo13`–`demo17`); seven interleaved predictions per backend per image, first two discarded; median of the eight per-image medians | 14.86 ms | 14.50 ms |
| Neural Engine | `.cpuAndNeuralEngine` | `demo02`; 32 interleaved predictions per backend, first 12 discarded | 23.01 ms | 15.51 ms |

The GPU comparison produced zero absolute output difference across all 11 images
used during its broader numerical validation, including the three initial images
that were not included in the timing aggregate. The Neural Engine comparison was
not bit-identical: MAE was 0.00425, RMSE was 0.00873, and maximum absolute
difference was 0.18555, with no nonfinite values.

`.cpuAndNeuralEngine` configures the devices Core ML may use; it does not prove
that every operation ran on the Neural Engine. These standalone comparisons were
performed on the M1 Max under macOS 26.5.2 with Xcode 26.6 and predate the macOS
27 realtime captures. They are useful evidence about the relative DA2 routes,
but are not directly comparable with the realtime table. Current MESS builds use
`.cpuAndGPU` for DA2 Core ML and no longer switch that model to
`.cpuAndNeuralEngine` when other Vision workloads change. The original harness
and raw per-call timing samples are not included in this repository; the table
preserves its recorded protocol and aggregate results.

## Other standalone conversion measurements

These warm medians came from different small harnesses and exclude the full MESS
pipeline. Compare routes within a row more strongly than values between rows.

| Model | Fixed input | Core ML CPU + GPU | MPSGraph `.level0` | Context |
| --- | ---: | ---: | ---: | --- |
| ZipDepth Base NPU | 384 x 384 | 12.96 ms | 3.48 ms | Preliminary raw-model probes |
| DA3 Small native | 518 x 518 | 23.94 ms | 40.4 ms | Core ML validator and separate graph probe |
| DA3 Small reduced | 392 x 392 | 16.69 ms | 15.22 ms | Core ML validator and separate graph probe |

## Deployment-target finding

The three Depth Anything Core ML sources fail `mpsgraphtool` conversion for
macOS 26 and earlier. Their generated instance-normalization operation uses
mean, variance, gamma, and beta operands available from MPSGraph package target
version 1.3.8; Xcode 27 maps macOS 26 to 1.3.3 and macOS 15 to 1.2.1. They convert
successfully with a macOS 27 target. This restriction applies to the generated
MPSGraph packages. All four Core ML source packages support macOS 15: DA2 and
ZipDepth use the Core ML specification target corresponding to macOS 13, and DA3
uses the target corresponding to macOS 15.

ZipDepth converts successfully with a macOS 15 target. The release keeps its
macOS 27 build so every artifact matches the benchmark configuration. A future
lower-target ZipDepth release should be tested on the oldest claimed system.

See [MPSGraph deployment compatibility](compatibility.md) for the full tested
matrix, reproduced diagnostics, build-versus-runtime distinction, reproduction
command, and possible lower-target approaches.

## Next measurement

A controlled DA2 comparison should use three separate launches:

1. Core ML with `.cpuAndGPU`;
2. Core ML with an explicit diagnostic `.cpuAndNeuralEngine` selection; and
3. MPSGraph `.level0`.

Each launch should replay the same source segment at the same output size and
target frame rate, with identical foreground-mask, face, and effect settings.
Allow the model to warm up before starting a capture, then record the same
duration for every route. Capture metadata should include the exact model,
backend, Core ML compute units, source identity, output dimensions, and enabled
analysis workloads. The stats stream should also record depth request and
completion deltas so delivered depth fps can be measured directly. Production
DA2 should remain fixed to `.cpuAndGPU`; the Neural Engine route should be an
explicit diagnostic choice rather than workload-driven switching.
