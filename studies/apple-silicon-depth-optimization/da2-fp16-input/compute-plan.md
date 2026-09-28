# DepthAnythingV2SmallRealtimeTensorF16 Core ML Compute Plan

Generated: `2026-09-28T07:46:02Z`

- Hardware: `Mac13,1`
- OS: `Version 27.0 (Build 26A428)`
- Architecture: `arm64`
- Developer tools: `Xcode 27.0; Build version 27A266a`
- Source tree SHA-256: `ac8ca0e16801c5112cc26a08874a2d3fe90fc55d9d676f92b3be69723011f0d2`
- Available devices: `CPU`, `GPU`, `Neural Engine`

## All

| Preferred device | Operation count | Estimated cost weight |
| --- | ---: | ---: |
| GPU | 29 | 0.049628 |
| Neural Engine | 327 | 0.950372 |
| Unreported | 743 | — |

Operations without an estimated cost: 743.

### Highest-cost non-primary operations

| Path | Operator | Preferred device | Estimated cost weight | Outputs |
| --- | --- | --- | ---: | --- |
| `main.67` | `ios16.softmax` | GPU | 0.009237 | `input_5_cast_fp16` |
| `main.70` | `ios16.matmul` | GPU | 0.005387 | `var_164_cast_fp16` |
| `main.66` | `ios16.matmul` | GPU | 0.005387 | `attn_1_cast_fp16` |
| `main.50` | `transpose` | GPU | 0.003436 | `qkv_1_cast_fp16` |
| `main.15` | `ios16.conv` | GPU | 0.002518 | `x_3_cast_fp16` |
| `main.77` | `ios16.linear` | GPU | 0.002495 | `linear_1_cast_fp16` |
| `main.44` | `ios16.reshape` | GPU | 0.002306 | `var_152_cast_fp16` |
| `main.63` | `slice_by_index` | GPU | 0.001538 | `v_1_cast_fp16` |
| `main.58` | `slice_by_index` | GPU | 0.001538 | `k_1_cast_fp16` |
| `main.51` | `slice_by_index` | GPU | 0.001538 | `var_155_cast_fp16` |
| `main.42` | `ios16.linear` | GPU | 0.001368 | `linear_0_cast_fp16` |
| `main.33` | `concat` | GPU | 0.001176 | `var_127_cast_fp16` |
| `main.22` | `concat` | GPU | 0.001176 | `x_7_cast_fp16` |
| `main.73` | `transpose` | GPU | 0.001145 | `var_165_cast_fp16` |
| `main.30` | `transpose` | GPU | 0.001144 | `var_122_cast_fp16` |
| `main.21` | `transpose` | GPU | 0.001144 | `x_5_cast_fp16` |
| `main.74` | `ios16.reshape` | GPU | 0.000769 | `input_7_cast_fp16` |
| `main.84` | `ios16.layer_norm` | GPU | 0.000769 | `input_13_cast_fp16` |
| `main.39` | `ios16.layer_norm` | GPU | 0.000769 | `x_9_cast_fp16` |
| `main.31` | `ios16.reshape` | GPU | 0.000768 | `patch_pos_embed_cast_fp16` |
| `main.17` | `ios16.reshape` | GPU | 0.000768 | `var_102_cast_fp16` |
| `main.27` | `ios16.upsample_bilinear` | GPU | 0.000725 | `patch_pos_embed_3_cast_fp16` |
| `main.80` | `ios16.add` | GPU | 0.000523 | `input_11_cast_fp16` |
| `main.34` | `ios16.add` | GPU | 0.000523 | `input_3_cast_fp16` |
| `main.5` | `ios16.sub` | GPU | 0.000400 | `var_33_cast_fp16` |

## CPU + GPU

| Preferred device | Operation count | Estimated cost weight |
| --- | ---: | ---: |
| GPU | 356 | 1.000000 |
| Unreported | 743 | — |

Operations without an estimated cost: 743.

### Highest-cost non-primary operations

None reported.

## CPU + Neural Engine

| Preferred device | Operation count | Estimated cost weight |
| --- | ---: | ---: |
| CPU | 4 | 0.017628 |
| Neural Engine | 352 | 0.982372 |
| Unreported | 743 | — |

Operations without an estimated cost: 743.

### Highest-cost non-primary operations

| Path | Operator | Preferred device | Estimated cost weight | Outputs |
| --- | --- | --- | ---: | --- |
| `main.15` | `ios16.conv` | CPU | 0.009430 | `x_3_cast_fp16` |
| `main.7` | `ios16.mul` | CPU | 0.003074 | `_inversed_x_1_cast_fp16` |
| `main.1` | `ios16.mul` | CPU | 0.003074 | `image_cast_fp16` |
| `main.5` | `ios16.sub` | CPU | 0.002050 | `var_33_cast_fp16` |

## Limitations

- Core ML's public MLModelStructure.Program.ValueType API does not expose per-operation tensor shapes or data types. Correlate operation paths and output names with the source MIL inventory.
- MLComputePlan reports anticipated device usage and estimated relative cost; it is not a runtime trace.

The adjacent JSON file is the authoritative machine-readable report.
