# Model build workflows

Each model family owns its Core ML export and MPSGraph conversion entry point:

- `models/depth-anything-v2/build.sh`
- `models/depth-anything-3/build_518.sh`
- `models/depth-anything-3/build_392.sh`
- `models/zipdepth/build_384.sh`
- `models/zipdepth/build_512.sh`
- `models/zipdepth/build_672x384.sh`
- `models/zipdepth/build_896x512.sh`

All three use `common/convert_coreml_to_mpsgraph.sh` only for the final conversion
of one named `.mlpackage`. Source revisions, weights, patches, dependencies,
shapes, validation, and supported variants stay in the owning model directory.

`tools/coreml-compute-plan/` contains the Swift command used to audit Core ML's
anticipated per-operation compute placement for the optimization study. It is
independent of the model-family conversion environments.

Generated files go under the ignored `build/` directory by default. Scripts
refuse to replace existing model outputs so a previous validated artifact is not
silently destroyed. Use a new model-specific build root for a clean rebuild.
