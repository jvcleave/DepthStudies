#!/bin/bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
    echo "usage: $0 COREML_PACKAGE OUTPUT_DIRECTORY PACKAGE_NAME MINIMUM_TARGET" >&2
    exit 64
fi

source_package=$1
output_directory=$2
package_name=$3
minimum_target=$4
output_package="$output_directory/$package_name.mpsgraphpackage"

if [[ $(uname -s) != Darwin ]]; then
    echo "mpsgraphtool is available only on macOS" >&2
    exit 69
fi
if [[ ! -x /usr/bin/mpsgraphtool ]]; then
    echo "mpsgraphtool was not found; install Xcode 27 or later" >&2
    exit 69
fi
if [[ ! -d "$source_package" ]]; then
    echo "missing Core ML package: $source_package" >&2
    exit 66
fi
if [[ -e "$output_package" ]]; then
    echo "refusing to replace existing graph package: $output_package" >&2
    exit 73
fi

mkdir -p "$output_directory"
/usr/bin/env -i \
    PATH=/usr/bin:/bin:/usr/sbin:/sbin \
    TMPDIR="${TMPDIR:-/tmp}" \
    /usr/bin/mpsgraphtool convert \
    -coremlpackage "$source_package" \
    -path "$output_directory" \
    -packageName "$package_name" \
    -deploymentPlatform macOS \
    -minimumDeploymentTarget "$minimum_target"

echo "MPSGraph package: $output_package"
