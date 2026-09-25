#!/bin/bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"
source_revision=a561b849ebae10a6f5ef49e26c83cbbcd36c71bf
source_url=https://github.com/DepthAnything/Depth-Anything-V2.git
weight_revision=03876f8651c73a60fe4c2c48294e09fcb6838fcf
weight_sha256=715fade13be8f229f8a70cc02066f656f2423a59effd0579197bbf57860e1378
pristine_dpt_sha256=7cc9a29b41d31e1628e5c8b8705e25ae95bc6490f779dbb695297ce2341566f5
patched_dpt_sha256=e049b2d2455497ad668bb6a960e4c92a4a885bd55c6018d4b0de92cb5aec08ba
build_root="${DA2_BUILD_ROOT:-$repo_root/build/depth-anything-v2}"
source_root="${DA2_SOURCE_ROOT:-$build_root/source}"
python_bin="${PYTHON_BIN:-python3.9}"
venv_dir="${DA2_VENV_DIR:-$build_root/venv}"
coreml_dir="$build_root/coreml"
graph_dir="$build_root/mpsgraph"
download_dir="$build_root/downloads"
model_name=DepthAnythingV2SmallRealtime
model_path="$coreml_dir/$model_name.mlpackage"
checkpoint_path="${DA2_CHECKPOINT:-$download_dir/depth_anything_v2_vits.pth}"
created_source=0

if [[ ! -d "$source_root/.git" ]]; then
    if [[ -e "$source_root" ]]; then
        echo "DA2 source path exists but is not a Git checkout: $source_root" >&2
        exit 66
    fi
    mkdir -p "$(dirname "$source_root")"
    git clone "$source_url" "$source_root"
    git -C "$source_root" checkout --detach "$source_revision"
    created_source=1
fi

actual_revision=$(git -C "$source_root" rev-parse HEAD)
if [[ "$actual_revision" != "$source_revision" ]]; then
    echo "expected DA2 revision $source_revision, got $actual_revision" >&2
    exit 65
fi

dpt_path="$source_root/depth_anything_v2/dpt.py"
dpt_sha256=$(shasum -a 256 "$dpt_path" | awk '{print $1}')
if [[ "$dpt_sha256" == "$pristine_dpt_sha256" && "$created_source" == 1 ]]; then
    git -C "$source_root" apply --unidiff-zero "$script_dir/depth-anything-v2-coreml.patch"
    dpt_sha256=$(shasum -a 256 "$dpt_path" | awk '{print $1}')
fi
if [[ "$dpt_sha256" != "$patched_dpt_sha256" ]]; then
    echo "DA2 dpt.py does not match the validated Core ML source patch" >&2
    echo "expected $patched_dpt_sha256, got $dpt_sha256" >&2
    exit 65
fi
while IFS= read -r changed_path; do
    if [[ -n "$changed_path" && "$changed_path" != "depth_anything_v2/dpt.py" ]]; then
        echo "unexpected tracked DA2 source change: $changed_path" >&2
        exit 65
    fi
done < <(git -C "$source_root" diff --name-only)
if [[ -n $(git -C "$source_root" diff --cached --name-only) ]]; then
    echo "DA2 source checkout has staged changes" >&2
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
        "https://huggingface.co/depth-anything/Depth-Anything-V2-Small/resolve/$weight_revision/depth_anything_v2_vits.pth" \
        -o "$checkpoint_path"
fi
actual_weight_sha256=$(shasum -a 256 "$checkpoint_path" | awk '{print $1}')
if [[ "$actual_weight_sha256" != "$weight_sha256" ]]; then
    echo "DA2 checkpoint SHA-256 mismatch" >&2
    echo "expected $weight_sha256, got $actual_weight_sha256" >&2
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

PYTHONPATH="$source_root" "$venv_dir/bin/python" "$script_dir/export_coreml.py" \
    --encoder vits \
    --checkpoint "$checkpoint_path" \
    --width 448 \
    --height 336 \
    --compute-precision float16 \
    --pos-embed-interpolation bilinear \
    --model-semantics optimized \
    --output "$model_path"

"$repo_root/scripts/common/convert_coreml_to_mpsgraph.sh" \
    "$model_path" "$graph_dir" "$model_name" "${MPSGRAPH_MINIMUM_TARGET:-27.0.0}"
