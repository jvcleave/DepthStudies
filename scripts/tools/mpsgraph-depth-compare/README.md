# MPSGraph depth comparison

This macOS 27 command compares the output and graph-only execution time of two
fixed-shape depth graph packages. It defaults to a planar FP32 0...255 baseline
and a planar FP16 0...255 candidate. Use `--candidate-input-data-type float32`
when both graph packages retain the image-input conversion contract.

```sh
swift build \
  --package-path scripts/tools/mpsgraph-depth-compare \
  --scratch-path "$HOME/Library/Developer/Xcode/DerivedData/MESS-LocalBuilds/depthstudies-mpsgraph-depth-compare" \
  -c release

"$HOME/Library/Developer/Xcode/DerivedData/MESS-LocalBuilds/depthstudies-mpsgraph-depth-compare/release/mpsgraph-depth-compare" \
  --baseline /path/to/ZipDepthBaseNPU384x384.mpsgraphpackage \
  --candidate /path/to/ZipDepthBaseNPU384x384TensorF16.mpsgraphpackage \
  --width 384 \
  --height 384 \
  --output /path/to/mpsgraph-comparison.json
```

Pass the corresponding 896 x 512 baseline and FP16 packages with
`--width 896 --height 512` to repeat the larger-model comparison.

The timing includes executable encoding, submission, and GPU completion. It
does not include texture resizing, RGB packing, depth unpacking, or upscaling,
so an app decision still requires complete depth-source measurements.
