Experimental fixed-shape Core ML source packages and their derived MPSGraph
depth packages used by the MESS macOS 27 depth study and follow-up optimization
work.

Each model variant is available as both `.mlpackage.zip` and
`.mpsgraphpackage.zip`. The MPSGraph packages were generated with Xcode 27.0
`mpsgraphtool`, package format 7.0.63, and a macOS 27.0 deployment target.
Runtime evidence was collected on an Apple M1 Max running macOS 27.0; the
artifact manifest records which individual variants were exercised. The Depth
Anything graphs cannot currently be serialized for macOS 26 or earlier. The
attached ZipDepth graph assets also use the macOS 27 study configuration.

## Included variants

- DA2 Small 448 x 336 with image/FP32 and planar-FP16 graph inputs.
- DA3 Small at 518 x 518 and 392 x 392.
- ZipDepth Base NPU with image/FP32 graph inputs at 384 x 384, 512 x 512,
  672 x 384, 896 x 512, 1536 x 864, and 1920 x 1088.
- ZipDepth Base NPU with planar-FP16 graph inputs at 384 x 384, 896 x 512,
  1536 x 864, and 1920 x 1088.

## Compatibility

The `.mlpackage` and `.mpsgraphpackage` assets have different OS requirements:

| Model | Core ML `.mlpackage` | Attached `.mpsgraphpackage` | Lower graph conversion |
| --- | --- | --- | --- |
| DA2 Small 448 x 336, both input variants | Supports macOS 15; declared floor is macOS 13 | Requires macOS 27 | Targets 26 and 15 fail |
| DA3 Small 518 x 518 | Supports macOS 15 | Requires macOS 27 | Targets 26 and 15 fail |
| DA3 Small 392 x 392 | Supports macOS 15 | Requires macOS 27 | Targets 26 and 15 fail |
| ZipDepth Base NPU, all attached variants | Supports macOS 15; declared floor is macOS 13 | Attached builds require macOS 27 | The original 384 x 384 variant converts for targets 26 and 15; the expanded variants were packaged only for target 27 |

The Depth Anything graph conversion fails below macOS 27 because its generated
`mps.instance_norm` operation has explicit `gamma`, `beta`, `mean`, and
`variance` operands. Those operands require graph-package target 1.3.8;
`mpsgraphtool` selects 1.3.3 for macOS 26 and 1.2.1 for macOS 15. This is a graph
serialization restriction and does not apply to the Core ML packages.

The released graph packages were tested only on macOS 27 where the manifest
marks `runtime_tested` as true. ZipDepth's successful lower-target conversion
has not yet been runtime-tested on macOS 15. An app targeting macOS 15 can
continue to compile and use all fourteen Core ML packages; Xcode 27 is the
tested conversion toolchain for reproducing the attached graph packages. See the
[deployment compatibility report](https://github.com/jvcleave/DepthStudies/blob/main/studies/realtime-depth-macos27/compatibility.md)
for the complete diagnostics, build-versus-runtime distinction, and reproduction
command.

## Realtime MESS MPSGraph medians

| Engine | Model time | Complete depth-source time | 60-frame presentation rate |
| --- | ---: | ---: | ---: |
| DA3 Small capture | 33.77 ms | 32.17 ms | 56.71 fps |
| Depth Anything V2 | 17.01 ms | 17.23 ms | 60.02 fps |
| ZipDepth Base NPU | 5.29 ms | 5.44 ms | 60.00 fps |

These captures used different live workloads. See the tagged study source for raw
captures, full caveats, build instructions, provenance, and licenses. The DA3
capture metadata does not identify whether 392 x 392 or 518 x 518 was active.

## Standalone DA2 compute-unit medians

These synchronous still-image measurements used the same custom DA2 Small
448 x 336 package. Input preparation and output readback were outside the timed
calls. The two rows used different sampling protocols and should be read as
separate comparisons.

| Core ML compute units | Core ML | Paired MPSGraph | Sampling |
| --- | ---: | ---: | --- |
| `.cpuAndGPU` | 14.86 ms | 14.50 ms | Eight images; seven interleaved calls per backend per image, first two discarded; median of per-image medians |
| `.cpuAndNeuralEngine` | 23.01 ms | 15.51 ms | One image; 32 interleaved calls per backend, first 12 discarded |

The compute-unit setting identifies the devices Core ML may use; it does not
prove that every operation ran on the named accelerator. These standalone
measurements predate the macOS 27 realtime captures and are not directly
comparable with the table above.

Verify all downloaded archives with `SHA256SUMS.txt` before unpacking.
