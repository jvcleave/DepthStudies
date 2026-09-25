#!/bin/bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"
source_revision=91f3fd21e131641f51e8d35736d1958350180e3a
source_url=https://github.com/fabiotosi92/ZipDepth.git
checkpoint_sha256=627c04fda584133ead4310074884a4a037061b4c01ba86e73e492ea30fab570d
build_root="${ZIPDEPTH_BUILD_ROOT:-$repo_root/build/zipdepth}"
source_root="${ZIPDEPTH_SOURCE_ROOT:-$build_root/source}"
python_bin="${PYTHON_BIN:-python3.9}"
venv_dir="${ZIPDEPTH_VENV_DIR:-$build_root/venv}"
coreml_dir="$build_root/coreml"
graph_dir="$build_root/mpsgraph"
download_dir="$build_root/downloads"
model_name=ZipDepthBaseNPU384x384
model_path="$coreml_dir/$model_name.mlpackage"
checkpoint_path="${ZIPDEPTH_CHECKPOINT:-$download_dir/zipdepth_base_npu.pth}"

if [[ ! -d "$source_root/.git" ]]; then
    if [[ -e "$source_root" ]]; then
        echo "ZipDepth source path exists but is not a Git checkout: $source_root" >&2
        exit 66
    fi
    mkdir -p "$(dirname "$source_root")"
    git clone "$source_url" "$source_root"
    git -C "$source_root" checkout --detach "$source_revision"
fi
actual_revision=$(git -C "$source_root" rev-parse HEAD)
if [[ "$actual_revision" != "$source_revision" ]]; then
    echo "expected ZipDepth revision $source_revision, got $actual_revision" >&2
    exit 65
fi
if [[ -n $(git -C "$source_root" status --porcelain) ]]; then
    echo "ZipDepth source checkout must be clean" >&2
    exit 65
fi

if ! command -v "$python_bin" >/dev/null 2>&1; then
    echo "Python 3.9 is required; set PYTHON_BIN to its executable" >&2
    exit 69
fi
python_version=$($python_bin -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ "$python_version" != 3.9 ]]; then
    echo "expected Python 3.9, got $python_version" >&2
    exit 65
fi

mkdir -p "$download_dir" "$coreml_dir" "$graph_dir"
if [[ ! -f "$checkpoint_path" ]]; then
    curl -fL \
        "https://raw.githubusercontent.com/fabiotosi92/ZipDepth/$source_revision/checkpoints/zipdepth_base_npu.pth" \
        -o "$checkpoint_path"
fi
actual_checkpoint_sha256=$(shasum -a 256 "$checkpoint_path" | awk '{print $1}')
if [[ "$actual_checkpoint_sha256" != "$checkpoint_sha256" ]]; then
    echo "ZipDepth checkpoint SHA-256 mismatch" >&2
    echo "expected $checkpoint_sha256, got $actual_checkpoint_sha256" >&2
    exit 65
fi
if [[ -e "$model_path" ]]; then
    echo "refusing to replace existing Core ML package: $model_path" >&2
    exit 73
fi

if [[ ! -x "$venv_dir/bin/python" ]]; then
    "$python_bin" -m venv "$venv_dir"
fi
if [[ "${COREML_SKIP_INSTALL:-0}" != 1 ]]; then
    "$venv_dir/bin/python" -m pip install -r "$script_dir/requirements.txt"
fi

"$venv_dir/bin/python" "$script_dir/export_coreml.py" \
    --source-root "$source_root" \
    --checkpoint "$checkpoint_path" \
    --width 384 \
    --height 384 \
    --output "$model_path"

"$repo_root/scripts/common/convert_coreml_to_mpsgraph.sh" \
    "$model_path" "$graph_dir" "$model_name" "${MPSGRAPH_MINIMUM_TARGET:-27.0.0}"
