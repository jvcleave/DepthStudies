# Core ML Compute-Plan Findings

**Completed:** 2026-09-28

These reports use Core ML's public `MLComputePlan` API to inspect anticipated
device placement on a Mac Studio with an M1 Max (`Mac13,1`), macOS 27.0 build
26A428, and Xcode 27.0 build 27A266a. The command did not run MESS or make model
predictions.

## Result

The current Core ML packages already have high Neural Engine placement when
configured for CPU plus Neural Engine. The data does not support removing
ZipDepth's StripPooling or GlobalContext blocks to fix presumed CPU fallback.
That experiment is deferred.

| Model | `.all` preferred estimated cost | CPU + Neural Engine preferred estimated cost | CPU + Neural Engine non-ANE operations |
| --- | --- | --- | --- |
| ZipDepth 384 x 384 | 95.76% Neural Engine, 4.24% CPU | 95.76% Neural Engine, 4.24% CPU | FP32 input scale and FP16 cast |
| ZipDepth 896 x 512 | 95.76% Neural Engine, 4.24% CPU | 95.76% Neural Engine, 4.24% CPU | FP32 input scale and FP16 cast |
| ZipDepth 1536 x 864 | 89.52% Neural Engine, 10.48% GPU | 95.76% Neural Engine, 4.24% CPU | FP32 input scale and FP16 cast |
| DA2 Small 448 x 336 | 94.87% Neural Engine, 5.13% GPU | 98.03% Neural Engine, 1.97% CPU | Initial preprocessing and patch convolution |
| DA3 Small 392 x 392 | 96.74% Neural Engine, 3.26% GPU | 97.66% Neural Engine, 2.34% CPU | Initial preprocessing, reshape, expand, and patch convolution |
| DA3 Small 518 x 518 | 94.42% Neural Engine, 5.58% GPU | 97.02% Neural Engine, 2.98% CPU | Initial preprocessing, reshape, expand, and patch convolution |

Estimated cost weights are normalized within each compute plan. They describe
anticipated placement and relative work; they are not comparable latency
measurements across models or configurations.

## Interpretation

### ZipDepth

All 120 nonconstant operations after the two input-conversion operations prefer
the Neural Engine under CPU plus Neural Engine. This includes StripPooling,
spatial softmax, and the global-context matrix multiplication. Their tensor
shapes may be less than ideal according to general authoring guidance, but the
current compute plan does not identify a fallback boundary for them.

At 1536 x 864, `.all` moves nine operations to the GPU and assigns them 10.48%
of its estimated cost. Those operations are a mix of add, batch normalization,
cast, ReLU, bilinear upsampling, multiplication, and subtraction. Forcing CPU
plus Neural Engine moves the graph back to the same placement proportions as
the smaller ZipDepth packages. Runtime benchmarks are still required to decide
whether `.all` or a fixed compute-unit choice is faster at that shape.

### Depth Anything V2

The CPU plus Neural Engine plan assigns 352 nonconstant operations and 98.03%
of estimated cost to the Neural Engine. Five operations prefer CPU. The largest
is the initial patch convolution; the others are input scaling, cast, subtract,
and reciprocal scaling.

This changes the explanation for the measured 23.01 ms CPU plus Neural Engine
result. The slowdown is not explained by wholesale CPU fallback. Likely factors
now include model-specific Neural Engine kernel performance, transfer and
partition overhead, and behavior not represented by the planning estimate.
Core ML CPU plus GPU remains the appropriate app choice based on measured time.

Under `.all`, Core ML sends 30 operations and 5.13% of estimated cost to the
GPU. Most of that GPU work is the first transformer block's softmax, matrix
multiplications, transposes, slicing, and related preparation. The remaining
blocks prefer the Neural Engine.

### Depth Anything 3

Native `scaled_dot_product_attention` is supported by all three compute-device
types in these packages. Under `.all`, the first attention operation prefers
the GPU and the remaining eleven prefer the Neural Engine. The compute plan
therefore does not support a blanket claim that native SDPA is GPU-only or
Neural Engine-hostile in the current Core ML runtime.

DA3 remains a control in this work. Its 392 x 392 MPSGraph path measured close
to Core ML, while its 518 x 518 MPSGraph path measured substantially slower.
Compute placement alone does not explain that shape-dependent MPSGraph result.

## Decisions

1. Defer the ZipDepth `balanced`/`light`/`none` structural ablation. Reopen it
   only if runtime profiling identifies one of those blocks as a material cost
   or if a quality-oriented experiment justifies changing the network.
2. Continue with the graph-specific FP16-input experiment. It targets known
   FP32 pack traffic and a cast in the MPSGraph path, independent of Core ML's
   Neural Engine placement.
3. Continue with DA2 fused attention as a GPU experiment, while treating it as
   speculative until the converter preserves the fused operator and an actual
   benchmark improves.
4. Keep measured runtime results authoritative when they disagree with
   compute-plan implications.

## Reports

Each Markdown summary links conceptually to an adjacent JSON file containing
all operations, bindings, preferred and supported devices, and estimated cost.

- [ZipDepth 384 x 384](compute-plans/zipdepth-384x384.md)
- [ZipDepth 896 x 512](compute-plans/zipdepth-896x512.md)
- [ZipDepth 1536 x 864](compute-plans/zipdepth-1536x864.md)
- [Depth Anything V2 Small 448 x 336](compute-plans/depth-anything-v2-small-448x336.md)
- [Depth Anything 3 Small 392 x 392](compute-plans/depth-anything-3-small-392x392.md)
- [Depth Anything 3 Small 518 x 518](compute-plans/depth-anything-3-small-518x518.md)

The public `MLModelStructure.Program.ValueType` API does not expose
per-operation tensor shape or data type. The reporter records stable operation
paths and output names for correlation with the source MIL inventory and avoids
private Core ML APIs.
