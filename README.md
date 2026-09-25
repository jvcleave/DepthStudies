# DepthStudies

DepthStudies collects reproducible Apple-platform depth-model conversions,
runtime artifacts, and measurements used while evaluating depth engines for
MESS.

The first study compares four fixed-shape Core ML models executed through
MPSGraph on Apple silicon. Its tagged release provides the Core ML source
packages and ready-to-load `.mpsgraphpackage` archives for:

- Depth Anything V2 Small, 448 x 336;
- Depth Anything 3 Small, 518 x 518;
- Depth Anything 3 Small, 392 x 392; and
- ZipDepth Base NPU, 384 x 384.

See [the macOS 27 realtime study](studies/realtime-depth-macos27/findings.md) for
results and limitations, [the artifact manifest](manifests/mpsgraph-depth-models-macos27-v0.1.0.json)
for exact contracts and provenance, and [the model build workflows](scripts/README.md)
for end-to-end export and conversion commands.

Each model family has its own entry point. Depth Anything V2 carries its fixed
source patch and exporter, DA3 pins the tagged conversion fork and its numerical
validator, and ZipDepth carries its pinned exporter. They share only the final
one-package `mpsgraphtool` helper.

## Compatibility

The v0.1.0 graph packages were created by Xcode 27.0's `mpsgraphtool`, package
format 7.0.63, with a macOS 27.0 deployment target. They have only been executed
on an Apple M1 Max running macOS 27.0. The corresponding `.mlpackage` archives
are included as the exact Core ML inputs used to create those graph packages.

## Repository scope

Large generated models live in GitHub releases. Git tracks the conversion recipe,
provenance, checksums, licenses, raw diagnostic captures, and derived findings.
MESS continues to generate the graph resources it embeds from its own Core ML
source packages; it does not download this repository's release assets at build
or runtime.

## Licensing

Each model remains subject to its upstream terms. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and the files under `licenses/`.
