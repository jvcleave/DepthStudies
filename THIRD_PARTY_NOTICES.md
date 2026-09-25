# Third-party notices

The release archives contain converted parameters from third-party depth models.
This repository does not change their upstream ownership or license terms.

## Depth Anything V2 Small

- Upstream: https://github.com/DepthAnything/Depth-Anything-V2
- Reviewed source revision: `a561b849ebae10a6f5ef49e26c83cbbcd36c71bf`
- License: Apache License 2.0
- Included license: `licenses/Depth-Anything-V2-Apache-2.0.txt`

The released graph was converted from the MESS fixed-shape realtime Core ML
export at 448 x 336.

## Depth Anything 3 Small

- Upstream: https://github.com/ByteDance-Seed/Depth-Anything-3
- Conversion fork: https://github.com/jvcleave/Depth-Anything-3
- License: Apache License 2.0
- Included license: `licenses/Depth-Anything-3-Apache-2.0.txt`

The 518 x 518 and 392 x 392 graphs preserve the learned camera token and
alternating attention in the single-view depth path. Details of the Core ML
rewrite are maintained in the conversion fork.

## ZipDepth Base NPU

- Upstream: https://github.com/fabiotosi92/ZipDepth
- Reviewed source revision: `91f3fd21e131641f51e8d35736d1958350180e3a`
- Checkpoint SHA-256: `627c04fda584133ead4310074884a4a037061b4c01ba86e73e492ea30fab570d`
- License: MIT
- Included license: `licenses/ZipDepth-MIT.txt`
