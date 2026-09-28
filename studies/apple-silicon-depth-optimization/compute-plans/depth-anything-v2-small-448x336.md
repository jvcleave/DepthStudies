# DepthAnythingV2SmallRealtime Core ML Compute Plan

Generated: `2026-09-28T04:27:14Z`

- Hardware: `Mac13,1`
- OS: `Version 27.0 (Build 26A428)`
- Architecture: `arm64`
- Developer tools: `Xcode 27.0; Build version 27A266a`
- Source tree SHA-256: `93a1789bfb8c5f7c1830b4d704cf4056a1c6cf1f67404b12a4283411095deb5b`
- Available devices: `CPU`, `GPU`, `Neural Engine`

## All

| Preferred device | Operation count | Estimated cost weight |
| --- | ---: | ---: |
| GPU | 30 | 0.051301 |
| Neural Engine | 327 | 0.948699 |
| Unreported | 744 | — |

Operations without an estimated cost: 744.

### Highest-cost non-primary operations

| Path | Operator | Preferred device | Estimated cost weight | Outputs |
| --- | --- | --- | ---: | --- |
| `main.69` | `ios16.softmax` | GPU | 0.009221 | `input_5_cast_fp16` |
| `main.72` | `ios16.matmul` | GPU | 0.005378 | `var_162_cast_fp16` |
| `main.68` | `ios16.matmul` | GPU | 0.005378 | `attn_1_cast_fp16` |
| `main.52` | `transpose` | GPU | 0.003430 | `qkv_1_cast_fp16` |
| `main.17` | `ios16.conv` | GPU | 0.002513 | `x_3_cast_fp16` |
| `main.79` | `ios16.linear` | GPU | 0.002491 | `linear_1_cast_fp16` |
| `main.46` | `ios16.reshape` | GPU | 0.002302 | `var_150_cast_fp16` |
| `main.4` | `ios16.cast` | GPU | 0.001760 | `image_to_fp16` |
| `main.65` | `slice_by_index` | GPU | 0.001535 | `v_1_cast_fp16` |
| `main.60` | `slice_by_index` | GPU | 0.001535 | `k_1_cast_fp16` |
| `main.53` | `slice_by_index` | GPU | 0.001535 | `var_153_cast_fp16` |
| `main.44` | `ios16.linear` | GPU | 0.001365 | `linear_0_cast_fp16` |
| `main.35` | `concat` | GPU | 0.001174 | `var_125_cast_fp16` |
| `main.24` | `concat` | GPU | 0.001174 | `x_7_cast_fp16` |
| `main.75` | `transpose` | GPU | 0.001143 | `var_163_cast_fp16` |
| `main.32` | `transpose` | GPU | 0.001142 | `var_120_cast_fp16` |
| `main.23` | `transpose` | GPU | 0.001142 | `x_5_cast_fp16` |
| `main.76` | `ios16.reshape` | GPU | 0.000767 | `input_7_cast_fp16` |
| `main.86` | `ios16.layer_norm` | GPU | 0.000767 | `input_13_cast_fp16` |
| `main.41` | `ios16.layer_norm` | GPU | 0.000767 | `x_9_cast_fp16` |
| `main.33` | `ios16.reshape` | GPU | 0.000766 | `patch_pos_embed_cast_fp16` |
| `main.19` | `ios16.reshape` | GPU | 0.000766 | `var_100_cast_fp16` |
| `main.29` | `ios16.upsample_bilinear` | GPU | 0.000724 | `patch_pos_embed_3_cast_fp16` |
| `main.82` | `ios16.add` | GPU | 0.000522 | `input_11_cast_fp16` |
| `main.36` | `ios16.add` | GPU | 0.000522 | `input_3_cast_fp16` |

## CPU + GPU

| Preferred device | Operation count | Estimated cost weight |
| --- | ---: | ---: |
| GPU | 357 | 1.000000 |
| Unreported | 744 | — |

Operations without an estimated cost: 744.

### Highest-cost non-primary operations

None reported.

## CPU + Neural Engine

| Preferred device | Operation count | Estimated cost weight |
| --- | ---: | ---: |
| CPU | 5 | 0.019667 |
| Neural Engine | 352 | 0.980333 |
| Unreported | 744 | — |

Operations without an estimated cost: 744.

### Highest-cost non-primary operations

| Path | Operator | Preferred device | Estimated cost weight | Outputs |
| --- | --- | --- | ---: | --- |
| `main.17` | `ios16.conv` | CPU | 0.009410 | `x_3_cast_fp16` |
| `main.7` | `ios16.mul` | CPU | 0.003068 | `_inversed_x_1_cast_fp16` |
| `main.1` | `ios16.mul` | CPU | 0.003068 | `image__scaled__` |
| `main.4` | `ios16.cast` | CPU | 0.002076 | `image_to_fp16` |
| `main.5` | `ios16.sub` | CPU | 0.002045 | `var_6_cast_fp16` |

## Limitations

- Core ML's public MLModelStructure.Program.ValueType API does not expose per-operation tensor shapes or data types. Correlate operation paths and output names with the source MIL inventory.
- MLComputePlan reports anticipated device usage and estimated relative cost; it is not a runtime trace.

The adjacent JSON file is the authoritative machine-readable report.
