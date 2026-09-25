# Depth Anything 3 workflow

`build.sh` checks out the tagged DA3 conversion fork, downloads the pinned DA3
Small weights, validates their SHA-256, and exports, validates, and converts the
camera-token variants. Use the artifact-specific entry points for one package:

```sh
scripts/models/depth-anything-3/build_518.sh
scripts/models/depth-anything-3/build_392.sh
```

Running `build.sh` directly builds both variants. `DA3_VARIANT` accepts `518`,
`392`, or `all`.

The model-specific exporter and numerical validator remain versioned in the
[DA3 conversion fork](https://github.com/jvcleave/Depth-Anything-3). This wrapper
pins that implementation and supplies immutable weights rather than duplicating
the exporter.

Both generated MPSGraph packages require a macOS 27 target with the current
operator lowering. The Core ML exports use `ct.target.iOS18`, which Core ML Tools
aliases to macOS 15, so both `.mlpackage` files support macOS 15. The later
macOS 27 constraint belongs to MPSGraph serialization. Both sizes retain an
instance-normalization form that cannot be downgraded to the tested macOS 26 or
15 graph-package targets. See the
[deployment compatibility report](../../../studies/realtime-depth-macos27/compatibility.md)
for the exact diagnostic and compatibility matrix.
