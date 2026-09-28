# ZipDepthBaseNPU1536x864 Core ML Compute Plan

Generated: `2026-09-28T04:26:58Z`

- Hardware: `Mac13,1`
- OS: `Version 27.0 (Build 26A428)`
- Architecture: `arm64`
- Developer tools: `Xcode 27.0; Build version 27A266a`
- Source tree SHA-256: `b839ebae546623746cb30e3fe423897a1891e22955dfe7d8d6d713b6e989c291`
- Available devices: `CPU`, `GPU`, `Neural Engine`

## All

| Preferred device | Operation count | Estimated cost weight |
| --- | ---: | ---: |
| GPU | 9 | 0.104815 |
| Neural Engine | 113 | 0.895185 |
| Unreported | 365 | — |

Operations without an estimated cost: 365.

### Highest-cost non-primary operations

| Path | Operator | Preferred device | Estimated cost weight | Outputs |
| --- | --- | --- | ---: | --- |
| `main.409` | `ios16.batch_norm` | GPU | 0.021274 | `input_151_cast_fp16` |
| `main.429` | `ios16.add` | GPU | 0.019289 | `input_157_cast_fp16` |
| `main.4` | `ios16.cast` | GPU | 0.015955 | `image_to_fp16` |
| `main.404` | `ios16.add` | GPU | 0.014467 | `input_149_cast_fp16` |
| `main.410` | `ios16.relu` | GPU | 0.013020 | `input_153_cast_fp16` |
| `main.414` | `ios16.upsample_bilinear` | GPU | 0.011275 | `input_155_cast_fp16` |
| `main.5` | `ios16.sub` | GPU | 0.003617 | `var_7_cast_fp16` |
| `main.7` | `ios16.mul` | GPU | 0.002959 | `_inversed_input_1_cast_fp16` |
| `main.1` | `ios16.mul` | GPU | 0.002959 | `image__scaled__` |

## CPU + GPU

| Preferred device | Operation count | Estimated cost weight |
| --- | ---: | ---: |
| GPU | 122 | 1.000000 |
| Unreported | 365 | — |

Operations without an estimated cost: 365.

### Highest-cost non-primary operations

None reported.

## CPU + Neural Engine

| Preferred device | Operation count | Estimated cost weight |
| --- | ---: | ---: |
| CPU | 2 | 0.042431 |
| Neural Engine | 120 | 0.957569 |
| Unreported | 365 | — |

Operations without an estimated cost: 365.

### Highest-cost non-primary operations

| Path | Operator | Preferred device | Estimated cost weight | Outputs |
| --- | --- | --- | ---: | --- |
| `main.1` | `ios16.mul` | CPU | 0.025309 | `image__scaled__` |
| `main.4` | `ios16.cast` | CPU | 0.017123 | `image_to_fp16` |

## Limitations

- Core ML's public MLModelStructure.Program.ValueType API does not expose per-operation tensor shapes or data types. Correlate operation paths and output names with the source MIL inventory.
- MLComputePlan reports anticipated device usage and estimated relative cost; it is not a runtime trace.

The adjacent JSON file is the authoritative machine-readable report.
