# MPSGraph deployment compatibility

This note separates three requirements that are easy to conflate:

1. the Core ML feature target used when exporting an `.mlpackage`;
2. the Xcode toolchain used to convert that model into an `.mpsgraphpackage`; and
3. the minimum macOS target encoded into the generated MPSGraph package.

The macOS 27 restriction in this study belongs to the third item for the Depth
Anything graph packages. **All fourteen released Core ML `.mlpackage` files
support macOS 15.** DA2 and ZipDepth were exported with `ct.target.iOS16`, which
Core ML Tools aliases to macOS 13. DA3 was exported with `ct.target.iOS18`, which
Core ML Tools aliases to macOS 15.

## Tested configuration

The conversion probes were run on 2026-09-25 with:

- macOS 27.0, build 26A428;
- Xcode 27.0, build 27A266a;
- `/usr/bin/mpsgraphtool` from that installation;
- MPSGraph package format 7.0.63; and
- device specialization disabled.

The probes used the exact Core ML inputs identified by the weight hashes in the
release manifest. A successful conversion means `mpsgraphtool` serialized a
package. Runtime execution was performed on an Apple M1 Max running macOS 27.
The macOS 15-targeted ZipDepth 896 x 512 package was tested on that host for
loading and output parity, not on its oldest encoded deployment target.

| Model | Core ML export target | Core ML macOS floor | Graph target 27 | Graph target 26 | Graph target 15 | Lower-target graph runtime tested |
| --- | --- | ---: | --- | --- | --- | --- |
| Depth Anything V2 Small, 448 x 336 | `ct.target.iOS16` | macOS 13 | Passed | Failed | Failed | No |
| Depth Anything 3 Small, 518 x 518 | `ct.target.iOS18` | macOS 15 | Passed | Failed | Failed | No |
| Depth Anything 3 Small, 392 x 392 | `ct.target.iOS18` | macOS 15 | Passed | Failed | Failed | No |
| ZipDepth Base NPU, 384 x 384 | `ct.target.iOS16` | macOS 13 | Passed | Passed | Passed | No |
| ZipDepth Base NPU, 896 x 512 | `ct.target.iOS16` | macOS 13 | Passed | Not probed | Passed | On macOS 27 only; macOS 15 remains untested |

The Core ML feature-target names above come directly from the exporters. Core ML
Tools defines the iOS 16 specification version as the macOS 13 specification
version and the iOS 18 specification version as the macOS 15 specification
version. The `.mlpackage` files therefore remain usable on macOS 15 and do not
inherit the macOS 27 target passed later to `mpsgraphtool`. The release study ran
on macOS 27; the table's Core ML floors describe declared model compatibility,
not a fresh runtime test on each older OS release.

## Build requirement versus runtime requirement

- An application targeting macOS 15 can compile and use these Core ML
  `.mlpackage` assets through Core ML. Their declared Core ML floors are macOS 13
  for DA2 and ZipDepth and macOS 15 for DA3.
- Xcode 27 is the tested toolchain required by this repository to reproduce the
  attached MPSGraph packages. That is a conversion-time requirement.
- The attached Depth Anything `.mpsgraphpackage` assets encode a macOS 27
  minimum and must not be loaded on macOS 26 or earlier. That is a runtime
  requirement of these serialized graph artifacts.
- ZipDepth can instead be serialized with a macOS 15 graph target. The release
  includes a separate macOS 15-targeted 896 x 512 package; the standard
  ZipDepth graph assets retain the macOS 27 benchmark configuration.

An application's Debug or Release configuration does not change these model
targets. An app that continues to deploy to macOS 15 can use the Core ML assets
there and expose the attached Depth Anything graph assets only when running on
macOS 27 or later.

## Why the Depth Anything graphs need target 27

For DA2 and both DA3 sizes, `mpsgraphtool` lowers part of the Core ML program to
an `mps.instance_norm` operation with explicit `gamma`, `beta`, `mean`, and
`variance` operands. That form cannot be serialized to the graph-package
versions selected for the tested older macOS targets.

Targeting macOS 26 selected package target 1.3.3 and produced:

```text
error: 'mps.instance_norm' op failed to downgrade: requested target version is
1.3.3, but gamma/beta/mean/variance operands are only supported from version
1.3.8
```

Targeting macOS 15 selected package target 1.2.1 and produced the same failure,
with 1.2.1 as the requested version. The tool then asserted that the MPSGraph
module could not be serialized to the desired deployment target and exited with
status 134. DA2 reported the operation at generated graph location 46:12; both
DA3 variants reported it at location 41:12.

The same Core ML inputs serialize successfully when the minimum deployment
target is macOS 27. Therefore the observed boundary is an MPSGraph serialization
and downgrade constraint in this toolchain. It is not a camera-token issue, an
input-resolution limit, or proof that the model's other operators need macOS 27.
Reducing DA3 from 518 x 518 to 392 x 392 improves its workload but retains the
same instance-normalization representation and deployment restriction.

## Why ZipDepth is different

ZipDepth 384 x 384 converted successfully when `-minimumDeploymentTarget` was
set to both 26.0.0 and 15.0.0. ZipDepth 896 x 512 also converted successfully
with target 15.0.0. It does not encounter the incompatible
instance-normalization form in these conversions. The standard release graphs
retain target 27 so benchmark artifacts share one build configuration; that
choice is not a ZipDepth requirement.

The target-15 ZipDepth 896 x 512 graph loaded on macOS 27 and produced output
bit-identical to the target-27 graph for the comparison harness input: maximum
absolute error and normalized RMSE were both zero. Median graph-only execution
was 5.88 ms for target 15 and 5.84 ms for target 27 over 30 alternating measured
iterations after five warmups. This small single-run difference is not treated
as a performance result. See the
[raw comparison](compatibility/zipdepth-896x512-macos15-vs-macos27.json).

The target-15 package still needs execution testing on macOS 15 and appropriate
hardware before it should be described as runtime-tested on its oldest target.

## Reproducing the conversion boundary

After unpacking one of the release's `.mlpackage.zip` assets, run:

```sh
/usr/bin/env -i \
  PATH=/usr/bin:/bin:/usr/sbin:/sbin \
  TMPDIR="${TMPDIR:-/tmp}" \
  /usr/bin/mpsgraphtool convert \
    -coremlpackage /path/to/Model.mlpackage \
    -path /path/to/output \
    -packageName Model \
    -deploymentPlatform macOS \
    -minimumDeploymentTarget 26.0.0
```

Use `15.0.0` or `27.0.0` for the other tested targets. The repository's shared
conversion helper invokes the same command and the model-specific build scripts
default to 27.0.0.

## Options for supporting older systems

The evidence supports four possible directions:

- continue using the Core ML packages on the application's existing Core ML
  path and validate their own runtime floors separately;
- use the attached lower-target ZipDepth graph and complete runtime testing on
  macOS 15;
- change the Depth Anything conversion so instance normalization is decomposed
  into older supported primitive operations before serialization; or
- implement the affected normalization and surrounding graph directly with an
  older-target-compatible MPSGraph formulation.

The last two options may change numerical behavior or performance and have not
been implemented or validated in this study. A future Xcode release may also
change lowering behavior, so the matrix should be rerun when the conversion
toolchain changes.
