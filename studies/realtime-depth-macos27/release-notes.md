Experimental fixed-shape Core ML source packages and their derived MPSGraph depth packages used by the MESS macOS 27 depth study.

Each model is available as both `.mlpackage.zip` and `.mpsgraphpackage.zip`. The
four MPSGraph packages were generated with Xcode 27.0 `mpsgraphtool`, package
format 7.0.63, and a macOS 27.0 deployment target. They were executed on an Apple
M1 Max running macOS 27.0. The Depth Anything graphs cannot currently be
serialized for macOS 26 or earlier; ZipDepth can be rebuilt for macOS 15, but the
attached graph asset matches the macOS 27 benchmark build.

## Compatibility

The `.mlpackage` and `.mpsgraphpackage` assets have different OS requirements:

| Model | Core ML `.mlpackage` | Attached `.mpsgraphpackage` | Lower graph conversion |
| --- | --- | --- | --- |
| DA2 Small 448 x 336 | Supports macOS 15; declared floor is macOS 13 | Requires macOS 27 | Targets 26 and 15 fail |
| DA3 Small 518 x 518 | Supports macOS 15 | Requires macOS 27 | Targets 26 and 15 fail |
| DA3 Small 392 x 392 | Supports macOS 15 | Requires macOS 27 | Targets 26 and 15 fail |
| ZipDepth Base NPU 384 x 384 | Supports macOS 15; declared floor is macOS 13 | Attached build requires macOS 27 | Targets 26 and 15 convert successfully |

The Depth Anything graph conversion fails below macOS 27 because its generated
`mps.instance_norm` operation has explicit `gamma`, `beta`, `mean`, and
`variance` operands. Those operands require graph-package target 1.3.8;
`mpsgraphtool` selects 1.3.3 for macOS 26 and 1.2.1 for macOS 15. This is a graph
serialization restriction and does not apply to the Core ML packages.

The released graph packages were runtime-tested only on macOS 27. ZipDepth's
successful lower-target conversion has not yet been runtime-tested on macOS 15.
An app targeting macOS 15 can continue to compile and use all four Core ML
packages; Xcode 27 is the tested conversion toolchain for reproducing the
attached graph packages. See the
[deployment compatibility report](https://github.com/jvcleave/DepthStudies/blob/main/studies/realtime-depth-macos27/compatibility.md)
for the complete diagnostics, build-versus-runtime distinction, and reproduction
command.

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
