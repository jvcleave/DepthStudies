# Realtime Depth Test TODO List

**Status:** Prepared on 2026-09-28 for later user-run MESS Release batches.

Use this checklist to compare the depth options already exposed by MESS and to
track promising experiments that still need implementation. Check off a run
only after its exported diagnostic capture and visual reference have been
saved.

## Test contract

- [ ] Use a Release build from MESS app commit `d73f27976` and bundle commit
  `3a30326`, or a later revision that retains the depth capture metadata.
- [ ] Record the Mac model, macOS build, Xcode build, MESS app commit, bundle
  commit, output size, target FPS, source identity, source segment, and effect
  preset once for the batch.
- [ ] Use the same prerecorded source, source segment, output size, target FPS,
  and effect settings for every run in a comparison.
- [ ] Select the engine in App Settings and relaunch MESS before each run. The
  active depth model and backend are fixed during app startup.
- [ ] Let the depth output and stats overlay stabilize before starting
  `CAPTURE LOG`.
- [ ] Capture at least 30 seconds. Prefer 60 seconds when comparing p90 or p99.
- [ ] Avoid changing effects, playback position, windows, or analysis settings
  during a capture.
- [ ] Stop `CAPTURE LOG`, use `EXPORT LOG`, and save the exported directory
  immediately.
- [ ] Save one matched MESS frame for qualitative review.
- [ ] Record peak working-set memory separately; the current diagnostic stream
  does not capture it.

Use a run name with enough information to survive outside this repository:

```text
YYYYMMDD-MODEL-SHAPE-BACKEND-INPUT-WORKLOAD-RELEASE
```

Example:

```text
20260928-DA2-448x336-MPSGRAPH-FP16-CLEAN-RELEASE
```

New captures contain a `capture.configuration` event in `events.jsonl` with:

- `depth_backend`;
- `depth_model_variant` and `depth_model_display_name`;
- `depth_input_data_type`;
- depth input and output dimensions;
- face backend; and
- session target FPS.

The selected model must match the intended run before accepting the capture.
Summarize a capture with:

```sh
python3 scripts/summarize_capture.py /absolute/path/to/capture
```

The current summarizer reports sampled medians. Before the final batch, extend
it to print the configuration event, p90/p99, missing metrics without failing,
and the number of usable samples.

## Workload definitions

Use these names consistently in run directories and notes.

- **CLEAN:** depth is active without foreground-mask, person-segmentation, or
  face-analysis work.
- **LOADED:** the fixed representative foreground/person and face workload is
  active. Record the exact enabled filters once and reuse them.

Run CLEAN first. Repeat only the leading candidates and their direct baselines
under LOADED. This keeps the batch small while still exposing GPU contention.

## Batch A: optimized FP16 graph input

These are the highest-priority application measurements. Each pair uses the
same weights and graph shape; only planar FP32 versus FP16 graph input changes.

### Depth Anything V2 at 448 x 336

- [ ] **A01** — `DEPTH V2 GRAPH`, CLEAN. FP32-input MPSGraph baseline.
- [ ] **A02** — `DEPTH DA2 F16 GRAPH`, CLEAN. Optimized FP16-input candidate.
- [ ] **A03** — `DEPTH V2 CORE ML`, CLEAN. Current CPU-plus-GPU application
  baseline.

Decision: retain DA2 FP16 only if complete depth-source latency, presentation
rate, or delivered cadence improves. Its isolated MPSGraph execution was tied
with FP32, so the remaining hypothesis is cheaper packing and buffer traffic.

### ZipDepth at 384 x 384

- [ ] **A04** — `DEPTH ZIP 384 GRAPH`, CLEAN.
- [ ] **A05** — `DEPTH ZIP 384 F16 GRAPH`, CLEAN.

This is the strongest isolated FP16 candidate: graph-only median time improved
by 27.8–36.3% across three paired runs.

### ZipDepth at 896 x 512

- [ ] **A06** — `DEPTH ZIP 896 GRAPH`, CLEAN.
- [ ] **A07** — `DEPTH ZIP 896 F16 GRAPH`, CLEAN.

The graph-only result was tied, while an initial application observation
favored FP16. This pair confirms whether packing or input traffic explains it.

### ZipDepth at 1536 x 864

- [ ] **A08** — `DEPTH ZIP 1536 GRAPH`, CLEAN.
- [ ] **A09** — `DEPTH ZIP 1536 F16 GRAPH`, CLEAN.

### ZipDepth at 1920 x 1088

- [ ] **A10** — `DEPTH ZIP 1080 GRAPH`, CLEAN.
- [ ] **A11** — `DEPTH ZIP 1080 F16 GRAPH`, CLEAN.

The `ZIP 1080` label refers to the fixed 1920 x 1088 tensor. The graph-only
1536 and 1920 pairs were tied; test them to quantify full-pipeline input traffic
and the presentation cost of the large activations.

## Batch B: backend and resolution controls

Run these after Batch A. They establish the baseline needed to decide whether a
fast graph variant is also the best application option.

### Depth Anything 3

- [ ] **B01** — `DEPTH DA3 392 CORE ML`, CLEAN.
- [ ] **B02** — `DEPTH DA3 392 GRAPH`, CLEAN.
- [ ] **B03** — `DEPTH DA3 518 CORE ML`, CLEAN.
- [ ] **B04** — `DEPTH DA3 518 GRAPH`, CLEAN.

The standalone 392 routes were close, while 518 MPSGraph was substantially
slower than Core ML. These captures also replace the older DA3 run whose exact
shape was not recorded.

### ZipDepth Core ML controls

- [ ] **B05** — `DEPTH ZIP 384 CORE ML`, CLEAN.
- [ ] **B06** — `DEPTH ZIP 896 CORE ML`, CLEAN.
- [ ] **B07** — `DEPTH ZIP 1536 CORE ML`, CLEAN.
- [ ] **B08** — `DEPTH ZIP 1080 CORE ML`, CLEAN.

ZipDepth Core ML retains the existing priority policy: it may use the
CPU-plus-Neural-Engine model when depth is prioritized and the CPU-plus-GPU
model when competing foreground/person analysis changes that priority. Treat
these as application-policy measurements, not fixed-compute-unit benchmarks.

### ZipDepth resolution sweep

- [ ] **B09** — `DEPTH ZIP 512 GRAPH`, CLEAN.
- [ ] **B10** — `DEPTH ZIP 672 GRAPH`, CLEAN.
- [ ] **B11** — `DEPTH ZIP 512 CORE ML`, CLEAN, only if a full backend sweep is
  still useful after B09.
- [ ] **B12** — `DEPTH ZIP 672 CORE ML`, CLEAN, only if a full backend sweep is
  still useful after B10.

Compare 384 x 384, 512 x 512, 672 x 384, 896 x 512, 1536 x 864, and
1920 x 1088 using both performance and matched frames. The 512 and 672 shapes
do not currently have FP16-input graph variants.

## Batch C: representative loaded session

Choose finalists only after reviewing Batches A and B.

- [ ] **C01** — Repeat the winning DA2 route under LOADED.
- [ ] **C02** — Repeat its direct DA2 baseline under LOADED.
- [ ] **C03** — Repeat the winning low-resolution ZipDepth route under LOADED.
- [ ] **C04** — Repeat its direct ZipDepth baseline under LOADED.
- [ ] **C05** — Repeat the winning high-resolution ZipDepth route under LOADED.
- [ ] **C06** — Repeat its direct ZipDepth baseline under LOADED.
- [ ] **C07** — Repeat the preferred DA3 route under LOADED only if DA3 remains
  a product candidate.
- [ ] **C08** — Repeat its direct DA3 baseline under LOADED.

Keep the foreground, person-segmentation, and face settings identical across
every C run. Record their sampled timing fields as contention context.

## Experiments that are not app buttons yet

Do not look for these in App Settings. They require isolated validation or app
integration before a realtime batch.

### DA2 FP16 Core ML and Neural Engine

- [ ] Add a compute-unit option to
  `scripts/models/depth-anything-v2/validate_tensor_f16.py`.
- [ ] Run three alternating comparisons using `cpuAndNeuralEngine` for the
  original image-input and new FP16 tensor-input packages.
- [ ] Record median, p90, p99, numerical error, and the host/runtime versions.
- [ ] Add a Core ML tensor-input backend and explicit diagnostic app option only
  if the FP16 package clearly wins.
- [ ] If integrated, compare fixed CPU-plus-GPU and CPU-plus-Neural-Engine
  options in separate Release launches.

The FP16 candidate's compute plan estimates 98.24% Neural Engine cost versus
98.03% for the original package. That is enough to justify one measurement,
but it does not predict an improvement.

### DA3 Core ML compute-unit sweep

- [ ] Benchmark the existing 392 x 392 image-input package with fixed
  `cpuAndGPU`, `cpuAndNeuralEngine`, and `all` configurations.
- [ ] Run three alternating comparisons and record median, p90, p99, numerical
  error, and host/runtime versions.
- [ ] Repeat the sweep at 518 x 518 only if a non-GPU route is competitive at
  392 x 392 or if the 518 quality difference justifies the extra work.
- [ ] Add an explicit app option only for a route that wins in isolation; do
  not restore workload-driven compute-unit switching.

The current compute plans estimate 97.66% Neural Engine cost at 392 x 392 and
97.02% at 518 x 518 under CPU plus Neural Engine. DA3's native SDPA is supported
by CPU, GPU, and Neural Engine in these packages, so this measurement is more
plausible than rewriting its attention graph. Placement estimates are not
runtime evidence; DA2 already demonstrated that high estimated ANE placement
can still be slower.

### DA3 FP16 graph input

- [ ] Export and validate a 392 x 392 planar-FP16 DA3 package.
- [ ] Measure it against the existing 392 x 392 FP32-input graph.
- [ ] Integrate an optional app button only if the isolated candidate passes.
- [ ] Try 518 x 518 only if the 392 x 392 experiment succeeds.
- [ ] Consider an intermediate 448 x 448 package only if the controlled 392 and
  518 results reveal a useful quality/performance gap.

### ZipDepth Neural Engine graph variants

- [ ] Export the planned `balanced`, `light`, and `none` unfold-replacement
  variants at 896 x 512 from the same pinned source and checkpoint.
- [ ] Validate each against PyTorch and run Core ML compute-plan reports.
- [ ] Compare `cpuAndNeuralEngine`, `cpuAndGPU`, and `all` in the same harness.
- [ ] Repeat only the winning variant at 1536 x 864.
- [ ] Add a realtime option only after an isolated winner exists.

## Do not repeat by default

- DA2 native SDPA was 2.2–3.4% slower through Core ML CPU plus GPU and
  4.0–4.5% slower through MPSGraph. Revisit it only after a material Core ML or
  MPSGraph runtime change.
- The original DA2 CPU-plus-Neural-Engine route measured 23.01 ms versus
  14.86 ms for CPU plus GPU in earlier standalone runs. Production DA2 should
  remain CPU plus GPU unless the new FP16 tensor experiment reverses that.
- Do not revive the old camera-token-disabled DA3 conversion. It removed the
  learned camera token and alternating global-attention behavior, and its
  output reached only `0.9293` Pearson correlation with the official path on
  the recorded sample. The current camera-token package is the valid baseline.

## Results to retain for every accepted run

- [ ] Exported capture directory with `manifest.json`, `events.jsonl`, and the
  `engine-stats` stream.
- [ ] Exact `capture.configuration` fields.
- [ ] Capture duration and usable sample count.
- [ ] Median, p90, and p99 depth-model and complete depth-source latency.
- [ ] Median presentation rate.
- [ ] Foreground and face timing for LOADED runs.
- [ ] Peak working-set memory.
- [ ] One matched rendered frame and a short visual-regression note.
- [ ] Final classification: `adopt`, `retain as optional`, or `reject`.

Delivered depth completions and superseded-request counts are part of the study
contract but are not yet emitted by the current one-second capture sampler. Add
those fields before using a batch to make a scheduling or delivered-cadence
claim. Until then, describe the captured depth values as sampled latency.
