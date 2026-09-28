# ZipDepth workflow

The artifact-specific entry points reproduce fixed ZipDepth Base NPU Core ML
sources and their MPSGraph packages:

```sh
scripts/models/zipdepth/build_384.sh
scripts/models/zipdepth/build_512.sh
scripts/models/zipdepth/build_672x384.sh
scripts/models/zipdepth/build_896x512.sh
scripts/models/zipdepth/build_1536x864.sh
scripts/models/zipdepth/build_1920x1088.sh
```

The graph-specific FP16-input experiments have separate entry points:

```sh
scripts/models/zipdepth/build_384_tensor_f16.sh
scripts/models/zipdepth/build_896x512_tensor_f16.sh
```

They create `ZipDepthBaseNPU384x384TensorF16` and
`ZipDepthBaseNPU896x512TensorF16`: planar FP16 NCHW inputs in the 0...255 range
with pixel scaling represented inside each model. The baseline Core ML
image-input packages remain unchanged. These artifacts are experimental until
their Core ML and MPSGraph outputs and complete pack/inference/unpack time have
been compared with their corresponding baselines.

Validate the Core ML candidate against the image-input baseline on three fixed
inputs:

```sh
build/zipdepth/venv/bin/python scripts/models/zipdepth/validate_tensor_f16.py \
  --baseline /path/to/ZipDepthBaseNPU384x384.mlpackage \
  --candidate build/zipdepth-384-tensor-f16/coreml/ZipDepthBaseNPU384x384TensorF16.mlpackage \
  --width 384 \
  --height 384 \
  --output build/zipdepth-384-tensor-f16/coreml-validation.json
```

All workflows pin and validate the upstream revision, NPU checkpoint SHA-256,
Python versions, tensor shape, and conversion target. Running `build.sh`
directly defaults to 384 x 384; `ZIPDEPTH_VARIANT` accepts `384`, `512`,
`672x384`, `896x512`, `1536x864`, or `1920x1088`.

The 672 x 384 and 896 x 512 variants preserve a 16:9 source shape while using
the upstream inference policy's documented 384 and 512 short-side sizes,
rounded to multiples of 32. They use the same pinned checkpoint as the square
variants and are not separately trained models.

The 1536 x 864 option is an exact 16:9 high-resolution compromise. Its
1,327,104-pixel tensor has 36.5% fewer pixels than 1920 x 1088 while remaining
2.89 times the area of 896 x 512.

The 1920 x 1088 variant is the full-width 1080-class experiment. A literal
1920 x 1080 tensor is invalid because ZipDepth requires each dimension to be a
multiple of 32. MESS presents this option as `ZIP 1080` while retaining the
exact 1920 x 1088 shape in its model catalog.

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
