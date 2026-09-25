# ZipDepth workflow

`build.sh` reproduces the fixed 384 x 384 ZipDepth Base NPU Core ML source and
its MPSGraph package. It pins and validates the upstream revision, NPU checkpoint
SHA-256, Python versions, tensor shape, and conversion target.

The Core ML export uses `ct.target.iOS16`, which Core ML Tools aliases to macOS
13, so the `.mlpackage` supports macOS 15.

The release-compatible default target is macOS 27. ZipDepth also converts for
macOS 15:

```sh
MPSGRAPH_MINIMUM_TARGET=15.0.0 scripts/models/zipdepth/build.sh
```

A macOS 15 package still needs execution testing on the oldest claimed system
before being published with that compatibility claim. The released graph uses
the macOS 27 benchmark configuration, but ZipDepth conversion itself does not
require 27. See the
[deployment compatibility report](../../../studies/realtime-depth-macos27/compatibility.md)
for the tested conversion matrix.
