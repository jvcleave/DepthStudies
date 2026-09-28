# Loaded ZipDepth MPSGraph batch 2, 2026-09-28

Four user-run MESS diagnostic captures add 512 x 512 and 672 x 384 FP32
MPSGraph observations and a paired 896 x 512 FP32/FP16 comparison. Foreground
and face analysis were active in every run. Each capture ran for at least 34
seconds, ended normally, and reported zero dropped diagnostic events.

The embedded configuration identifies the exact depth variant, input type,
fixed shape, MPSGraph backend, MPSMediaPipe face backend, and 60 fps session
target. It does not identify the source segment, effect preset, complete
enabled-analysis set, build, host, or working-set memory. The captures are
directional observations rather than completion of the controlled test
contract.

## Results

The table excludes the initial sample before one second. Depth latency is
recovered from each sampled fps-equivalent value before calculating the
percentiles.

| Fixed shape and graph input | Duration | Samples | Model median / p90 / p99 | Complete depth-source median / p90 / p99 | Median presentation |
| --- | ---: | ---: | ---: | ---: | ---: |
| 512 x 512 FP32 | 34.49 s | 35 | 6.49 / 7.40 / 8.46 ms | 6.69 / 7.54 / 8.62 ms | 60.01 fps |
| 672 x 384 FP32 | 37.57 s | 38 | 5.82 / 7.57 / 8.10 ms | 5.97 / 7.84 / 8.24 ms | 60.00 fps |
| 896 x 512 FP32 | 35.12 s | 36 | 8.61 / 8.98 / 9.34 ms | 8.72 / 9.24 / 9.49 ms | 60.00 fps |
| 896 x 512 FP16 | 37.59 s | 38 | 8.00 / 8.95 / 12.01 ms | 8.18 / 9.58 / 12.90 ms | 60.00 fps |

At 896 x 512, FP16 reduced median model latency by `0.61 ms` (`7.1%`) and
median complete depth-source latency by `0.54 ms` (`6.2%`). Both variants held
the 60 fps presentation median. The FP16 tail was less consistent: complete
depth-source p90 increased from `9.24 ms` to `9.58 ms`, and p99 increased from
`9.49 ms` to `12.90 ms`. The median result supports retaining the option, but
this single pair does not support making FP16 the default.

The nearly equal-pixel 512 x 512 and 672 x 384 observations measured `6.69 ms`
and `5.97 ms` median complete depth-source latency, respectively. They came
from separate loaded runs, and foreground time was materially higher in the
512 capture, so the difference cannot be attributed to tensor shape alone.
Both maintained the 60 fps presentation target.

## Workload context

| Fixed shape and graph input | Foreground model median | Face latency median | Observed face count |
| --- | ---: | ---: | ---: |
| 512 x 512 FP32 | 21.73 ms | 10.89 ms | 0–4 |
| 672 x 384 FP32 | 17.55 ms | 10.59 ms | 0–4 |
| 896 x 512 FP32 | 17.66 ms | 12.35 ms | 0–4 |
| 896 x 512 FP16 | 19.47 ms | 11.83 ms | 0–4 |

The 896 FP16 capture had a heavier foreground median than its FP32 pair while
still improving median depth time. Its foreground and face tails also differed,
so the depth-tail regression needs a controlled repeat before interpretation.
The current stream lacks delivered-depth completion and superseded-request
counts and cannot establish delivered cadence or scheduling behavior.

## Raw captures

- [ZipDepth 512 x 512 FP32 MPSGraph, loaded](captures/ZIP_512x512_MPSGRAPH_FP32_LOADED)
- [ZipDepth 672 x 384 FP32 MPSGraph, loaded](captures/ZIP_672x384_MPSGRAPH_FP32_LOADED)
- [ZipDepth 896 x 512 FP32 MPSGraph, loaded](captures/ZIP_896x512_MPSGRAPH_FP32_LOADED)
- [ZipDepth 896 x 512 FP16 MPSGraph, loaded](captures/ZIP_896x512_MPSGRAPH_FP16_LOADED)

Reproduce a summary with:

```sh
python3 scripts/summarize_capture.py \
  studies/realtime-depth-macos27/captures/ZIP_896x512_MPSGRAPH_FP16_LOADED
```
