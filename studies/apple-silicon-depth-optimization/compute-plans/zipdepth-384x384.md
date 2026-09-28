# ZipDepthBaseNPU384x384 Core ML Compute Plan

Generated: `2026-09-28T04:26:53Z`

- Hardware: `Mac13,1`
- OS: `Version 27.0 (Build 26A428)`
- Architecture: `arm64`
- Developer tools: `Xcode 27.0; Build version 27A266a`
- Source tree SHA-256: `a6a49cc1e082a429512868725451cc0f54bddd1565b3489ba8294957567c756a`
- Available devices: `CPU`, `GPU`, `Neural Engine`

## All

| Preferred device | Operation count | Estimated cost weight |
| --- | ---: | ---: |
| CPU | 2 | 0.042419 |
| Neural Engine | 120 | 0.957581 |
| Unreported | 365 | — |

Operations without an estimated cost: 365.

### Highest-cost non-primary operations

| Path | Operator | Preferred device | Estimated cost weight | Outputs |
| --- | --- | --- | ---: | --- |
| `main.1` | `ios16.mul` | CPU | 0.025301 | `image__scaled__` |
| `main.4` | `ios16.cast` | CPU | 0.017118 | `image_to_fp16` |

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
| CPU | 2 | 0.042419 |
| Neural Engine | 120 | 0.957581 |
| Unreported | 365 | — |

Operations without an estimated cost: 365.

### Highest-cost non-primary operations

| Path | Operator | Preferred device | Estimated cost weight | Outputs |
| --- | --- | --- | ---: | --- |
| `main.1` | `ios16.mul` | CPU | 0.025301 | `image__scaled__` |
| `main.4` | `ios16.cast` | CPU | 0.017118 | `image_to_fp16` |

## Limitations

- Core ML's public MLModelStructure.Program.ValueType API does not expose per-operation tensor shapes or data types. Correlate operation paths and output names with the source MIL inventory.
- MLComputePlan reports anticipated device usage and estimated relative cost; it is not a runtime trace.

The adjacent JSON file is the authoritative machine-readable report.
