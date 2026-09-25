#!/bin/bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "usage: $0 COREML_PACKAGE_DIRECTORY OUTPUT_DIRECTORY" >&2
    exit 64
fi

source_directory=$1
output_directory=$2
minimum_target=27.0.0
models=(
    DepthAnythingV2SmallRealtime
    DepthAnything3SmallCameraTokenImageF16
    DepthAnything3SmallCameraToken392x392ImageF16
    ZipDepthBaseNPU384x384
)

if [[ $(uname -s) != Darwin ]]; then
    echo "mpsgraphtool is available only on macOS" >&2
    exit 69
fi
if [[ ! -x /usr/bin/mpsgraphtool ]]; then
    echo "mpsgraphtool was not found; install Xcode 27 or later" >&2
    exit 69
fi

mkdir -p "$output_directory"
for model in "${models[@]}"; do
    source_package="$source_directory/$model.mlpackage"
    if [[ ! -d "$source_package" ]]; then
        echo "missing Core ML package: $source_package" >&2
        exit 66
    fi
    rm -rf "$output_directory/$model.mpsgraphpackage"
    /usr/bin/env -i \
        PATH=/usr/bin:/bin:/usr/sbin:/sbin \
        TMPDIR="${TMPDIR:-/tmp}" \
        /usr/bin/mpsgraphtool convert \
        -coremlpackage "$source_package" \
        -path "$output_directory" \
        -packageName "$model" \
        -deploymentPlatform macOS \
        -minimumDeploymentTarget "$minimum_target"
done
