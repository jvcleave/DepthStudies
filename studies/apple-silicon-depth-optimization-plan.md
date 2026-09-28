# Apple Silicon Depth Optimization Plan

**Status:** In progress. The baseline exporters, packages, MPSGraph conversion,
MESS variants, and initial measurements exist. Milestone 1 is complete. Its
[compute-plan findings](apple-silicon-depth-optimization/compute-plan-findings.md)
defer the ZipDepth structural ablation because the current packages already
show high Neural Engine placement. Milestone 3 passed isolated validation and
has an optional MESS engine; its [realtime comparison is pending](apple-silicon-depth-optimization/fp16-input-findings.md).

## Objective

Find changes that improve delivered realtime depth in MESS without hiding a
quality, memory, synchronization, or CPU-fallback cost. Treat Core ML on the
Neural Engine and MPSGraph on the GPU as separate targets with separate model
representations.

The immediate priorities are:

1. prove where every important Core ML operation runs;
2. test smaller ZipDepth global-context variants for Neural Engine residency;
3. remove avoidable FP32 input traffic from the MPSGraph path; and
4. test fused scaled dot-product attention in Depth Anything V2 for the GPU.

App integration follows only after an isolated experiment passes its numerical,
quality, and performance gates.

## Current evidence

The existing [realtime findings](realtime-depth-macos27/findings.md) establish
useful baselines, but they do not yet identify per-operation compute placement.

| Model | Current observation | Implication |
| --- | --- | --- |
| ZipDepth 384 x 384 | Core ML `.all` measured 2.56 ms, Core ML CPU + Neural Engine 3.48 ms, and MPSGraph 3.48 ms in the standalone comparison. | ZipDepth is the first Neural Engine residency study. Requesting Neural Engine compute is not proof that the whole program resides there. |
| DA2 448 x 336 | Core ML CPU + GPU measured 14.86 ms and MPSGraph measured 14.50 ms. Core ML CPU + Neural Engine was slower at 23.01 ms. | Keep CPU + GPU as the current app choice. Investigate the attention graph before attempting another Neural Engine variant. |
| DA3 392 x 392 | Core ML measured 16.69 ms and MPSGraph 15.22 ms. | Retain as a useful small-shape comparison. |
| DA3 518 x 518 | Core ML measured 23.94 ms and MPSGraph 40.40 ms. | Do not assume MPSGraph wins at larger shapes. |
| ZipDepth high-resolution variants | 1536 x 864 processes 2.89 times as many pixels as 896 x 512; 1920 x 1088 processes 4.55 times as many. | The high-resolution slowdown is primarily activation, compute, and bandwidth growth. The eight extra rows in 1088 are not the main cost. |

Static inspection gives these hypotheses:

- All current packages have fixed input shapes and mostly FP16 nonconstant
  values. Each package still has one FP32 preprocessing multiplication that
  needs a compute-plan check before it is treated as a problem.
- ZipDepth's balanced configuration creates strip tensors with singleton last
  axes and includes spatial-softmax global context. Both patterns conflict with
  Apple's preferred Neural Engine shapes and partitioning behavior.
- DA2 expresses attention as separate linear, matrix-multiply, softmax, and
  matrix-multiply operations. Its 769-token attention dimension is not aligned
  to 64 bytes, and the graph includes rank-five QKV tensors.
- DA3 already preserves native `scaled_dot_product_attention`. The compute-plan
  audit found that the operation is supported on CPU, GPU, and Neural Engine in
  the current runtime; `.all` places the first block on GPU and the other eleven
  on Neural Engine.
- The current MPSGraph depth package accepts planar FP32 RGB and casts to FP16
  internally. The Metal pack stage can potentially write FP16 directly.
- Current model weights are small enough that activation and execution cost are
  higher priorities than weight compression. Revisit compression only if a
  profiler shows weight loading is material.

Apple's `.aimodel` tools are not the packaging path used here. The hardware
principles in the [Neural Engine rules](https://github.com/apple/coreai-models/blob/main/skills/skills/model-authoring/references/neural_engine_rules.md),
[GPU rules](https://github.com/apple/coreai-models/blob/main/skills/skills/model-authoring/references/gpu_rules.md),
and [general guidance](https://github.com/apple/coreai-models/blob/main/skills/skills/working-with-coreai/references/guidance.md)
still apply. Current `.mlpackage` assets should be audited with Core ML's
`MLComputePlan` API.

## Measurement contract

Before changing a model, freeze the experiment conditions.

- [ ] Pin the Mac model, OS build, Xcode build, repository revisions, model
  checksum, backend, Core ML compute units, and tensor dimensions.
- [ ] Use a Release build for app measurements.
- [ ] Use the same prerecorded source frames and MESS effect configuration for
  every comparison.
- [ ] Warm each model before sampling and record the warmup policy.
- [ ] Report median, p90, and p99 latency instead of a single average.
- [ ] Record model time, complete depth-source time, delivered depth completions
  per second, presentation frame rate, working-set memory, and CPU/GPU use.
- [ ] Record pending or superseded realtime requests so a latest-wins scheduler
  cannot make a slow model look healthy by dropping more work.
- [ ] Run competing Vision workloads in a second controlled scenario. Keep an
  unloaded run as the primary model comparison.
- [ ] Add exact model, shape, backend, and compute-unit fields to saved capture
  metadata before collecting new app results.

Store raw machine-readable results beside derived tables. A prose result without
the raw run metadata is not sufficient to select an app default.

## Milestone 1: Core ML compute-residency audit

**Goal:** identify which operations actually prefer or support the Neural
Engine, GPU, and CPU before rewriting any model.

### Actionable steps

- [x] Add a small Swift command-line tool under `scripts/tools/` that compiles
  or loads a Core ML model and creates `MLComputePlan` instances for
  `.cpuAndNeuralEngine`, `.cpuAndGPU`, and `.all`.
- [x] Recursively enumerate functions, blocks, and operations in the compiled
  ML Program.
- [x] Emit JSON containing each operation's type, bindings, output names,
  preferred compute device, supported compute devices, and estimated cost when
  Core ML provides it. Core ML's public value-type API does not expose tensor
  shapes or data types, so correlate those through the source MIL inventory.
- [x] Generate a readable Markdown summary from the same JSON rather than
  maintaining a second hand-authored result.
- [x] Audit ZipDepth at 384 x 384, 896 x 512, and 1536 x 864 first.
- [x] Audit DA2 at 448 x 336 as the control for its observed slow Neural Engine
  configuration.
- [x] Audit DA3 only after the tool works for the first two families; DA3 is a
  diagnostic comparison rather than the first optimization target.
- [x] Correlate CPU-preferred or high-cost operations with the inspected MIL
  graph, including the remaining FP32 multiplication.
- [x] Check in the tool, exact invocation, JSON reports, and generated summary.

### Gate

Do not claim full Neural Engine residency from the requested Core ML compute
units. Proceed to a Neural Engine rewrite only when the compute plan identifies
a significant CPU/GPU partition, transfer boundary, or expensive unsupported
operation that the rewrite is intended to remove.

### Outcome

The audit found no significant ZipDepth CPU fallback after input conversion.
It also found high Neural Engine placement for DA2 and DA3. See the
[findings](apple-silicon-depth-optimization/compute-plan-findings.md) and raw
reports. Runtime measurements remain authoritative because `MLComputePlan` is
an anticipated placement and relative-cost estimate rather than a trace.

## Milestone 2: ZipDepth Neural Engine ablations

**Disposition:** Deferred after Milestone 1. The compute plan assigns every
ZipDepth operation after input scale/cast to the Neural Engine under CPU plus
Neural Engine. Do not create these variants unless new runtime profiling points
to a specific global-context cost or a quality experiment requires them.

**Goal:** determine whether ZipDepth's global-context blocks are responsible
for fallback or partition cost, and whether removing them retains acceptable
depth quality.

The existing exporter uses `global_mode="balanced"`, fused convolution/batch
normalization, FP16 compute precision, static shapes, and the non-unfold
upsampling path. Keep those controls fixed.

### Actionable steps

- [ ] Add explicit exporter choices for these three graph variants:
  - `balanced`: current StripPooling plus GlobalContext baseline;
  - `light`: omit StripPooling and retain GlobalContext; and
  - `none`: omit both global blocks.
- [ ] Handle checkpoint loading explicitly. Document the expected unused keys
  for omitted modules and fail on any unexpected mismatch.
- [ ] Start at 896 x 512. This shape is large enough to expose residency and
  bandwidth behavior while keeping iteration faster than 1536 x 864.
- [ ] Export all variants from the same pinned checkpoint and source revision.
- [ ] Compare each Core ML package with its own PyTorch variant using frozen
  sample inputs and the existing numerical validation method.
- [ ] Run the compute-residency report for all three packages.
- [ ] Measure `.cpuAndNeuralEngine`, `.cpuAndGPU`, and `.all` using the same
  harness and sampling policy.
- [ ] Produce raw depth maps and matched MESS renders for qualitative review.
- [ ] If a variant wins at 896 x 512, repeat only that variant and the balanced
  control at 1536 x 864.

These ablations intentionally change model semantics. Numerical equivalence is
required between PyTorch and Core ML for a given variant; it is not expected
between `balanced`, `light`, and `none`.

### Gate

A candidate advances only when:

- its Core ML output matches its PyTorch source within the established export
  tolerance;
- it produces no nonfinite output or structural depth failure;
- compute-plan evidence shows the intended partition improvement;
- end-to-end depth-source time improves beyond run-to-run noise; and
- the depth maps remain useful for the actual MESS effects.

Stop this branch if removing the context blocks causes unacceptable quality.
Recovering that quality would require training or fine-tuning, which is outside
this update plan.

## Milestone 3: FP16 input for the ZipDepth MPSGraph path

**Goal:** reduce input-buffer traffic and remove the graph's initial FP32-to-FP16
cast without changing the Core ML image-input package used by the Core ML path.

### Actionable steps

- [x] Create a graph-specific ZipDepth export with a fixed-shape FP16 tensor
  input and normalization represented in the graph.
- [x] Add a corresponding Metal pack kernel that writes planar FP16 RGB.
- [ ] Keep buffer layout, row order, color conversion, normalization constants,
  and texture orientation explicit in the artifact manifest. The experiment
  record and package metadata are complete; the release manifest remains.
- [x] Compare output with the current FP32-input MPSGraph package on frozen
  frames.
- [ ] Measure pack, graph, unpack/upscale, complete depth-source time, and peak
  working-set memory separately. Graph-only timing is complete; the app capture
  remains.
- [x] Test 384 x 384 first, then 896 x 512 if the small model shows a real
  improvement.

### Gate

Adopt the FP16 path only if output stays within the agreed tolerance, memory or
bandwidth falls as expected, and complete depth-source latency improves. A cast
removed from the graph is not by itself a successful result.

### Current result

The isolated candidate halved input-buffer bytes and reduced paired graph-only
median time by 27.8–36.3% across three runs. Core ML and MPSGraph output checks
passed. See the [FP16 input findings](apple-silicon-depth-optimization/fp16-input-findings.md).
The complete MESS depth-source gate remains open and requires the controlled
app runs above before the candidate can become a default or advance to
896 x 512.

## Milestone 4: Fused attention for DA2 on the GPU

**Goal:** test whether a native scaled dot-product attention operation gives
Core ML GPU or MPSGraph a better graph than DA2's decomposed attention sequence.

### Actionable steps

- [ ] Patch an exporter-owned model copy rather than modifying the upstream DA2
  checkout in place.
- [ ] Replace the explicit QK matrix multiplication, scaling, softmax, and AV
  matrix multiplication with PyTorch
  `scaled_dot_product_attention`, preserving QKV weights, head layout, scale,
  and inference-time dropout behavior.
- [ ] Verify the patched PyTorch result against the baseline before conversion.
- [ ] Convert the 448 x 336 model and inspect its MIL program.
- [ ] Confirm that conversion retains native `scaled_dot_product_attention`
  instead of recreating the decomposed 24-matmul/12-softmax pattern.
- [ ] Build the MPSGraph package and validate its output against Core ML and
  PyTorch.
- [ ] Measure complete depth-source time for Core ML CPU + GPU and MPSGraph.
- [ ] Record graph-package size and initialization time as secondary metrics.

### Gate

Advance only if the converted graph preserves fused attention, output quality
does not regress, and end-to-end GPU execution improves. If Core ML decomposes
the operator again or the fused graph does not win, record the result and stop
without adding an app variant.

## Milestone 5: Controlled MESS trials

**Goal:** validate isolated winners under the realtime session's actual
latest-wins scheduling and competing workloads.

### Actionable steps

- [ ] Add only successful isolated candidates as optional settings variants.
- [ ] Preserve the existing baseline variants during evaluation.
- [ ] Run each variant in a separate app launch using the measurement contract.
- [ ] Compare ZipDepth at 896 x 512 and 1536 x 864 first. Include the existing
  384 x 384 control and 1920 x 1088 only when answering a resolution question.
- [ ] Compare Core ML CPU + GPU, Core ML Neural Engine only when residency is
  supported by the compute plan, and MPSGraph.
- [ ] Repeat the finalists with the foreground-mask and face workloads enabled.
- [ ] Inspect delivered depth cadence and superseded work as well as model time.
- [ ] Classify each candidate as `adopt`, `retain as optional`, or `reject`, with
  the evidence linked from the findings.

### Gate

Change an app default only when a candidate improves the realtime metric that
matters for the effect and has acceptable image quality and memory use. A lower
isolated inference number is insufficient when delivered depth cadence or
presentation degrades.

## Milestone 6: Reproducibility and release

- [ ] Update the model-family build script and README for every retained
  artifact.
- [ ] Record the upstream source revision, local patch checksum, checkpoint
  checksum, conversion environment, input/output contract, and deployment
  target.
- [ ] Add package hashes and results to the artifact manifest.
- [ ] Update the findings with rejected experiments as well as winners.
- [ ] State separately which macOS version is required to build each graph,
  which version is declared by each Core ML package, and which systems were
  actually tested.
- [ ] Publish retained `.mlpackage` and `.mpsgraphpackage` artifacts together
  with their exact build and validation commands.

## Execution order

Run the work in this order:

1. measurement metadata and the compute-residency tool;
2. ZipDepth `balanced`/`light`/`none` at 896 x 512;
3. the winning ZipDepth Neural Engine candidate at 1536 x 864, if one exists;
4. ZipDepth MPSGraph FP16 input;
5. DA2 fused attention;
6. controlled app integration and release.

The order prevents app code and settings from multiplying before the model
experiment proves useful. It also separates Neural Engine authoring choices
from GPU authoring choices: singleton-axis removal and spatial splitting belong
to the former, while fused attention and FP16 tensor ingress belong to the
latter.

## Out of scope for this pass

- Retraining or fine-tuning ZipDepth after a structural ablation.
- Weight compression without profiling evidence that weight loading dominates.
- A new realtime scheduler or a change to latest-wins behavior.
- New Core Image work in the realtime path.
- Treating a `.cpuAndNeuralEngine` request as evidence of Neural Engine
  execution.
- Forcing one converted model representation to serve both the Neural Engine
  and GPU when their preferred graph structures conflict.
