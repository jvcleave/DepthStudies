# Depth Anything V2 Native SDPA Findings

**Disposition:** Rejected as a MESS variant on 2026-09-28. The conversion and
quality gates passed, but native scaled dot-product attention was consistently
slower than the existing decomposed attention through both Core ML CPU plus GPU
and MPSGraph on the test Mac.

## Change

The candidate keeps the pinned Depth Anything V2 Small checkpoint, optimized
depth head, 448 x 336 input, preprocessing, FP16 compute precision, and output
contract. During export, it replaces the twelve explicit QK matrix
multiplication, scale, softmax, and AV sequences in memory with PyTorch
`scaled_dot_product_attention`. It does not modify the pinned upstream checkout.

PyTorch validation found a maximum absolute difference of `0.000005007` and a
normalized RMSE of `0.000000530` before conversion. The exporter now fails if
Core ML does not preserve all twelve native attention operations.

| MIL operation | Existing DA2 | SDPA candidate |
| --- | ---: | ---: |
| `scaled_dot_product_attention` | 0 | 12 |
| `matmul` | 24 | 0 |
| `softmax` | 12 | 0 |
| `linear` | 48 | 48 |
| `reshape` | 30 | 30 |
| `transpose` | 30 | 30 |

The candidate requires the iOS 18 Core ML operator set, corresponding to macOS
15. Its generated MPSGraph package retains the study's macOS 27 requirement.
The [raw operation inventory](da2-sdpa/mil-operation-inventory.json) and
[experiment metadata](da2-sdpa/experiment.json) record the exact packages,
hashes, source revision, checkpoint, and conversion environment.

## Numerical validation

Core ML CPU plus GPU produced identical FP16 depth values for the
gradient, checker, and seeded-random fixtures. The paired MPSGraph package also
produced exact output for its fixed planar input. These results establish that
the timing difference is not caused by a changed depth result in the tested
inputs.

## Core ML CPU plus GPU timing

The Python validator reused one 448 x 336 PIL image, performed 20 warmups, and
alternated package order for 100 synchronous predictions per package. These
numbers include Core ML prediction and Python/Pillow bridging, so they support
the paired comparison only.

| Run | Classic median | SDPA median | SDPA change | Classic p90 | SDPA p90 |
| --- | ---: | ---: | ---: | ---: | ---: |
| [1](da2-sdpa/coreml-comparison-run1.json) | 16.50 ms | 17.01 ms | 3.1% slower | 17.49 ms | 17.88 ms |
| [2](da2-sdpa/coreml-comparison-run2.json) | 16.82 ms | 17.38 ms | 3.4% slower | 18.11 ms | 18.32 ms |
| [3](da2-sdpa/coreml-comparison-run3.json) | 16.86 ms | 17.24 ms | 2.2% slower | 18.51 ms | 18.90 ms |

## MPSGraph timing

The standalone macOS 27 harness used `.level0`, 20 warmups, alternating package
order, and synchronous GPU completion. It measured 200 iterations in the first
run and 100 in the other two. The timing includes graph encoding, submission,
and completion; it excludes texture resize, RGB packing, depth unpacking, and
output upscale.

| Run | Classic median | SDPA median | SDPA change | Classic p90 | SDPA p90 |
| --- | ---: | ---: | ---: | ---: | ---: |
| [1](da2-sdpa/mpsgraph-comparison-run1.json) | 11.90 ms | 12.43 ms | 4.5% slower | 12.14 ms | 12.67 ms |
| [2](da2-sdpa/mpsgraph-comparison-run2.json) | 11.90 ms | 12.37 ms | 4.0% slower | 12.13 ms | 12.58 ms |
| [3](da2-sdpa/mpsgraph-comparison-run3.json) | 11.89 ms | 12.39 ms | 4.2% slower | 12.12 ms | 12.62 ms |

## Compute-plan context

The [candidate compute plan](da2-sdpa/compute-plan.md) estimates 95.82% of
`.all` cost on the Neural Engine and 4.18% on the GPU, compared with 94.87% and
5.13% for the classic package. Under CPU plus Neural Engine, it estimates
97.43% on the Neural Engine, slightly below the classic package's 98.03%.
These estimates did not predict the paired CPU plus GPU result, reinforcing
that compute plans describe anticipated placement rather than runtime speed.

Core ML package size remained effectively unchanged at about 47.3 MiB, and the
two MPSGraph package disk sizes were equal. Initialization timing was not
collected after both primary execution paths failed the performance gate.

## Decision

Keep classic decomposed attention as the DA2 implementation. Do not add the
SDPA package to MESS settings or a release. The retained exporter option and raw
results make the negative result reproducible and provide a useful control if a
future Core ML or MPSGraph runtime changes native-attention performance.

The next independent DA2 experiment is FP16 tensor ingress for the MPSGraph
path. It targets input packing and buffer traffic rather than changing the
attention graph, so this SDPA result does not determine its outcome.
