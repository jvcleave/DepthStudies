# Depth Anything V2 workflow

`build.sh` reproduces the 448 x 336 Depth Anything V2 Small Core ML source and
its macOS MPSGraph package. It pins the upstream Git revision, Hugging Face
weight revision and SHA-256, Python package versions, fixed source patch, tensor
shape, and macOS graph target.

By default it creates a disposable pinned checkout under
`build/depth-anything-v2/source`. To use the established local source home:

```sh
DA2_SOURCE_ROOT=/Users/jvcleave/Documents/WORK_IN_PROGRESS/MACHINE_LEARNING/Depth-Anything-V2 \
  scripts/models/depth-anything-v2/build.sh
```

That checkout must remain at the recorded upstream revision and its `dpt.py`
must match the checked-in Core ML patch. The script accepts the existing
untracked checkpoints and model artifacts without modifying them.

The Core ML export uses `ct.target.iOS16`, which Core ML Tools aliases to macOS
13, so the `.mlpackage` supports macOS 15. The derived graph defaults to macOS
27 because the tested `mpsgraphtool` cannot downgrade its generated
instance-normalization form to the package targets for macOS 26 or 15. See the
[deployment compatibility report](../../../studies/realtime-depth-macos27/compatibility.md)
for the exact diagnostic and compatibility matrix.
