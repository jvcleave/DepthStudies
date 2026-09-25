Experimental fixed-shape MPSGraph depth packages used by the MESS macOS 27 depth study.

All four packages were generated with Xcode 27.0 `mpsgraphtool`, package format
7.0.63, and a macOS 27.0 deployment target. They were executed on an Apple M1 Max
running macOS 27.0. The Depth Anything graphs cannot currently be serialized for
macOS 26 or earlier; ZipDepth can be rebuilt for macOS 15 but the attached asset
matches the macOS 27 benchmark build.

## Realtime MESS medians

| Engine | Model time | Complete depth-source time | 60-frame presentation rate |
| --- | ---: | ---: | ---: |
| DA3 Small capture | 33.77 ms | 32.17 ms | 56.71 fps |
| Depth Anything V2 | 17.01 ms | 17.23 ms | 60.02 fps |
| ZipDepth Base NPU | 5.29 ms | 5.44 ms | 60.00 fps |

These captures used different live workloads. See the tagged study source for raw
captures, full caveats, build instructions, provenance, and licenses. The DA3
capture metadata does not identify whether 392 x 392 or 518 x 518 was active.

Verify all downloaded archives with `SHA256SUMS.txt` before unpacking.
