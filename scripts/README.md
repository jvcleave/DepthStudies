# Model build workflows

Each model family owns its Core ML export and MPSGraph conversion entry point:

- `models/depth-anything-v2/build.sh`
- `models/depth-anything-3/build_518.sh`
- `models/depth-anything-3/build_392.sh`
- `models/zipdepth/build.sh`

All three use `common/convert_coreml_to_mpsgraph.sh` only for the final conversion
of one named `.mlpackage`. Source revisions, weights, patches, dependencies,
shapes, validation, and supported variants stay in the owning model directory.

Generated files go under the ignored `build/` directory by default. Scripts
refuse to replace existing model outputs so a previous validated artifact is not
silently destroyed. Use a new model-specific build root for a clean rebuild.
