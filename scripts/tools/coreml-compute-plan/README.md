# Core ML compute-plan report

This command reports Core ML's anticipated per-operation compute-device usage
and relative estimated cost for an ML Program. It produces both machine-readable
JSON and a Markdown summary.

Build it outside the repository-local tree:

```sh
swift build \
  --package-path scripts/tools/coreml-compute-plan \
  --scratch-path "$HOME/Library/Developer/Xcode/DerivedData/MESS-LocalBuilds/depthstudies-coreml-compute-plan" \
  -c release
```

Run all three configurations used by the optimization study:

```sh
"$HOME/Library/Developer/Xcode/DerivedData/MESS-LocalBuilds/depthstudies-coreml-compute-plan/release/coreml-compute-plan-report" \
  --model /path/to/Model.mlpackage \
  --output studies/apple-silicon-depth-optimization/compute-plans/model.json
```

Use `--compute-units` to select a subset:

```sh
--compute-units cpu-and-neural-engine,cpu-and-gpu
```

`MLComputePlan` is an estimate of device placement rather than a runtime trace.
The public Core ML API also leaves each operation's value type opaque, so the
report records stable operation paths and value names for correlation with the
MIL program instead of using private APIs to extract tensor shapes.
