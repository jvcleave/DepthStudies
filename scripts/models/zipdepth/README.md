# ZipDepth workflow

`build.sh` reproduces the fixed 384 x 384 ZipDepth Base NPU Core ML source and
its MPSGraph package. It pins and validates the upstream revision, NPU checkpoint
SHA-256, Python versions, tensor shape, and conversion target.

The release-compatible default target is macOS 27. ZipDepth also converts for
macOS 15:

```sh
MPSGRAPH_MINIMUM_TARGET=15.0.0 scripts/models/zipdepth/build.sh
```

A macOS 15 package still needs execution testing on the oldest claimed system
before being published with that compatibility claim.
