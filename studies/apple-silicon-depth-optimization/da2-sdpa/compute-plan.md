# DepthAnythingV2SmallRealtimeSDPA Core ML Compute Plan

Generated: `2026-09-28T07:20:09Z`

- Hardware: `Mac13,1`
- OS: `Version 27.0 (Build 26A428)`
- Architecture: `arm64`
- Developer tools: `Xcode 27.0; Build version 27A266a`
- Source tree SHA-256: `04aa5ba4bee92dd4b11e8b08caefdcb7b1712859629667e41ceec101433e078b`
- Available devices: `CPU`, `GPU`, `Neural Engine`

## All

| Preferred device | Operation count | Estimated cost weight |
| --- | ---: | ---: |
| GPU | 28 | 0.041790 |
| Neural Engine | 305 | 0.958210 |
| Unreported | 599 | — |

Operations without an estimated cost: 599.

### Highest-cost non-primary operations

| Path | Operator | Preferred device | Estimated cost weight | Outputs |
| --- | --- | --- | ---: | --- |
| `main.49` | `ios18.transpose` | GPU | 0.004497 | `qkv_3_cast_fp16` |
| `main.16` | `ios18.conv` | GPU | 0.003295 | `x_3_cast_fp16` |
| `main.64` | `ios18.linear` | GPU | 0.003265 | `linear_1_cast_fp16` |
| `main.45` | `ios18.reshape` | GPU | 0.003018 | `qkv_1_cast_fp16` |
| `main.4` | `ios18.cast` | GPU | 0.002308 | `image_to_fp16` |
| `main.50` | `split` | GPU | 0.002012 | `var_152_cast_fp16_0`, `var_152_cast_fp16_1`, `var_152_cast_fp16_2` |
| `main.57` | `ios18.scaled_dot_product_attention` | GPU | 0.002012 | `x_11_cast_fp16` |
| `main.43` | `ios18.linear` | GPU | 0.001790 | `linear_0_cast_fp16` |
| `main.34` | `ios18.concat` | GPU | 0.001539 | `var_124_cast_fp16` |
| `main.23` | `ios18.concat` | GPU | 0.001539 | `x_7_cast_fp16` |
| `main.60` | `ios18.transpose` | GPU | 0.001499 | `var_157_cast_fp16` |
| `main.31` | `ios18.transpose` | GPU | 0.001497 | `var_119_cast_fp16` |
| `main.22` | `ios18.transpose` | GPU | 0.001497 | `x_5_cast_fp16` |
| `main.61` | `ios18.reshape` | GPU | 0.001006 | `input_5_cast_fp16` |
| `main.56` | `ios18.squeeze` | GPU | 0.001006 | `squeeze_2_cast_fp16` |
| `main.54` | `ios18.squeeze` | GPU | 0.001006 | `squeeze_1_cast_fp16` |
| `main.52` | `ios18.squeeze` | GPU | 0.001006 | `squeeze_0_cast_fp16` |
| `main.71` | `ios18.layer_norm` | GPU | 0.001006 | `input_11_cast_fp16` |
| `main.40` | `ios18.layer_norm` | GPU | 0.001006 | `x_9_cast_fp16` |
| `main.32` | `ios18.reshape` | GPU | 0.001005 | `patch_pos_embed_cast_fp16` |
| `main.18` | `ios18.reshape` | GPU | 0.001005 | `var_99_cast_fp16` |
| `main.28` | `ios16.upsample_bilinear` | GPU | 0.000949 | `patch_pos_embed_3_cast_fp16` |
| `main.67` | `ios18.add` | GPU | 0.000684 | `input_9_cast_fp16` |
| `main.35` | `ios18.add` | GPU | 0.000684 | `input_3_cast_fp16` |
| `main.5` | `ios18.sub` | GPU | 0.000523 | `var_6_cast_fp16` |

## CPU + GPU

| Preferred device | Operation count | Estimated cost weight |
| --- | ---: | ---: |
| GPU | 333 | 1.000000 |
| Unreported | 599 | — |

Operations without an estimated cost: 599.

### Highest-cost non-primary operations

None reported.

## CPU + Neural Engine

| Preferred device | Operation count | Estimated cost weight |
| --- | ---: | ---: |
| CPU | 5 | 0.025656 |
| Neural Engine | 328 | 0.974344 |
| Unreported | 599 | — |

Operations without an estimated cost: 599.

### Highest-cost non-primary operations

| Path | Operator | Preferred device | Estimated cost weight | Outputs |
| --- | --- | --- | ---: | --- |
| `main.16` | `ios18.conv` | CPU | 0.012276 | `x_3_cast_fp16` |
| `main.7` | `ios18.mul` | CPU | 0.004002 | `_inversed_x_1_cast_fp16` |
| `main.1` | `ios18.mul` | CPU | 0.004002 | `image__scaled__` |
| `main.4` | `ios18.cast` | CPU | 0.002708 | `image_to_fp16` |
| `main.5` | `ios18.sub` | CPU | 0.002668 | `var_6_cast_fp16` |

## Limitations

- Core ML's public MLModelStructure.Program.ValueType API does not expose per-operation tensor shapes or data types. Correlate operation paths and output names with the source MIL inventory.
- MLComputePlan reports anticipated device usage and estimated relative cost; it is not a runtime trace.

The adjacent JSON file is the authoritative machine-readable report.
