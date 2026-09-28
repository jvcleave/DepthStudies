# DepthAnything3SmallCameraToken392x392ImageF16 Core ML Compute Plan

Generated: `2026-09-28T04:27:38Z`

- Hardware: `Mac13,1`
- OS: `Version 27.0 (Build 26A428)`
- Architecture: `arm64`
- Developer tools: `Xcode 27.0; Build version 27A266a`
- Source tree SHA-256: `515f79a6d96d5ccc62c26e94290b6233c9e27cbf1cb06ef24f2c573e9fb0dff3`
- Available devices: `CPU`, `GPU`, `Neural Engine`

## All

| Preferred device | Operation count | Estimated cost weight |
| --- | ---: | ---: |
| GPU | 25 | 0.032619 |
| Neural Engine | 617 | 0.967381 |
| Unreported | 1116 | — |

Operations without an estimated cost: 1116.

### Highest-cost non-primary operations

| Path | Operator | Preferred device | Estimated cost weight | Outputs |
| --- | --- | --- | ---: | --- |
| `main.47` | `ios18.transpose` | GPU | 0.003588 | `qkv_1_cast_fp16` |
| `main.22` | `ios18.conv` | GPU | 0.002629 | `x_11_cast_fp16` |
| `main.66` | `ios18.linear` | GPU | 0.002605 | `linear_1_cast_fp16` |
| `main.41` | `ios18.reshape` | GPU | 0.002408 | `var_262_cast_fp16` |
| `main.4` | `ios18.cast` | GPU | 0.001841 | `image_to_fp16` |
| `main.58` | `ios18.slice_by_index` | GPU | 0.001605 | `v_1_cast_fp16` |
| `main.53` | `ios18.slice_by_index` | GPU | 0.001605 | `k_1_cast_fp16` |
| `main.48` | `ios18.slice_by_index` | GPU | 0.001605 | `q_1_cast_fp16` |
| `main.59` | `ios18.scaled_dot_product_attention` | GPU | 0.001605 | `x_29_cast_fp16` |
| `main.39` | `ios18.linear` | GPU | 0.001428 | `linear_0_cast_fp16` |
| `main.29` | `ios18.concat` | GPU | 0.001228 | `x_15_cast_fp16` |
| `main.14` | `ios18.reshape` | GPU | 0.001228 | `x_9_cast_fp16` |
| `main.9` | `ios18.expand_dims` | GPU | 0.001228 | `x_7_cast_fp16` |
| `main.62` | `ios18.transpose` | GPU | 0.001196 | `var_269_cast_fp16` |
| `main.28` | `ios18.transpose` | GPU | 0.001194 | `x_13_cast_fp16` |
| `main.63` | `ios18.reshape` | GPU | 0.000803 | `input_3_cast_fp16` |
| `main.73` | `ios18.layer_norm` | GPU | 0.000803 | `input_9_cast_fp16` |
| `main.36` | `ios18.layer_norm` | GPU | 0.000803 | `x_27_cast_fp16` |
| `main.24` | `ios18.reshape` | GPU | 0.000802 | `var_140_cast_fp16` |
| `main.69` | `ios18.add` | GPU | 0.000546 | `input_7_cast_fp16` |
| `main.31` | `ios18.add` | GPU | 0.000546 | `x_17_cast_fp16` |
| `main.5` | `ios18.sub` | GPU | 0.000417 | `var_14_cast_fp16` |
| `main.7` | `ios18.mul` | GPU | 0.000342 | `_inversed_x_5_cast_fp16` |
| `main.1` | `ios18.mul` | GPU | 0.000341 | `image__scaled__` |
| `main.68` | `ios18.mul` | GPU | 0.000224 | `var_277_cast_fp16` |

## CPU + GPU

| Preferred device | Operation count | Estimated cost weight |
| --- | ---: | ---: |
| GPU | 642 | 1.000000 |
| Unreported | 1116 | — |

Operations without an estimated cost: 1116.

### Highest-cost non-primary operations

None reported.

## CPU + Neural Engine

| Preferred device | Operation count | Estimated cost weight |
| --- | ---: | ---: |
| CPU | 7 | 0.023449 |
| Neural Engine | 635 | 0.976551 |
| Unreported | 1116 | — |

Operations without an estimated cost: 1116.

### Highest-cost non-primary operations

| Path | Operator | Preferred device | Estimated cost weight | Outputs |
| --- | --- | --- | ---: | --- |
| `main.22` | `ios18.conv` | CPU | 0.009836 | `x_11_cast_fp16` |
| `main.7` | `ios18.mul` | CPU | 0.003207 | `_inversed_x_5_cast_fp16` |
| `main.1` | `ios18.mul` | CPU | 0.003207 | `image__scaled__` |
| `main.4` | `ios18.cast` | CPU | 0.002170 | `image_to_fp16` |
| `main.5` | `ios18.sub` | CPU | 0.002138 | `var_14_cast_fp16` |
| `main.14` | `ios18.reshape` | CPU | 0.001446 | `x_9_cast_fp16` |
| `main.9` | `ios18.expand_dims` | CPU | 0.001446 | `x_7_cast_fp16` |

## Limitations

- Core ML's public MLModelStructure.Program.ValueType API does not expose per-operation tensor shapes or data types. Correlate operation paths and output names with the source MIL inventory.
- MLComputePlan reports anticipated device usage and estimated relative cost; it is not a runtime trace.

The adjacent JSON file is the authoritative machine-readable report.
