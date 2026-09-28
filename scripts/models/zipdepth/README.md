# ZipDepth workflow

The artifact-specific entry points reproduce fixed ZipDepth Base NPU Core ML
sources and their MPSGraph packages:

```sh
scripts/models/zipdepth/build_384.sh
scripts/models/zipdepth/build_512.sh
scripts/models/zipdepth/build_672x384.sh
scripts/models/zipdepth/build_896x512.sh
```

All workflows pin and validate the upstream revision, NPU checkpoint SHA-256,
Python versions, tensor shape, and conversion target. Running `build.sh`
directly defaults to 384 x 384; `ZIPDEPTH_VARIANT` accepts `384`, `512`,
`672x384`, or `896x512`.

The 672 x 384 and 896 x 512 variants preserve a 16:9 source shape while using
the upstream inference policy's documented 384 and 512 short-side sizes,
rounded to multiples of 32. They use the same pinned checkpoint as the square
variants and are not separately trained models.

The Core ML export uses `ct.target.iOS16`, which Core ML Tools aliases to macOS
13, so the `.mlpackage` supports macOS 15.

The release-compatible default target is macOS 27. ZipDepth also converts for
macOS 15:

```sh
MPSGRAPH_MINIMUM_TARGET=15.0.0 scripts/models/zipdepth/build_384.sh
```

A macOS 15 package still needs execution testing on the oldest claimed system
before being published with that compatibility claim. The released graph uses
the macOS 27 benchmark configuration, but ZipDepth conversion itself does not
require 27. See the
[deployment compatibility report](../../../studies/realtime-depth-macos27/compatibility.md)
for the tested conversion matrix.
