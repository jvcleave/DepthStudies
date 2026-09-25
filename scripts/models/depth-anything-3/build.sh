#!/bin/bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"
source_revision=b4571a4856af0d3e2075e129edf4ef5bab93b30f
source_tag=da3-small-coreml-v0.2.0
source_url=https://github.com/jvcleave/Depth-Anything-3.git
weight_revision=e08cab65ca0ec38e7826075418411ab90cab4da3
weight_sha256=364492e38a3a06d221ac75da7f6621ada3f2361cd24fde11ba79091e9f40efcf
reference_image_sha256=ea78c3b872b1e8b27de48cadf1d4a692cd42ddf5f72fcab78e2be2937935fb79
build_root="${DA3_BUILD_ROOT:-$repo_root/build/depth-anything-3}"
source_root="${DA3_SOURCE_ROOT:-$build_root/source}"
python_bin="${PYTHON_BIN:-python3.11}"
venv_dir="${DA3_VENV_DIR:-$build_root/venv}"
coreml_dir="$build_root/coreml"
graph_dir="$build_root/mpsgraph"
trace_dir="$build_root/traces"
download_dir="$build_root/downloads"
weights_path="${DA3_WEIGHTS:-$download_dir/model.safetensors}"

if [[ ! -d "$source_root/.git" ]]; then
    if [[ -e "$source_root" ]]; then
        echo "DA3 source path exists but is not a Git checkout: $source_root" >&2
        exit 66
    fi
    mkdir -p "$(dirname "$source_root")"
    git clone --branch "$source_tag" --depth 1 "$source_url" "$source_root"
fi
actual_revision=$(git -C "$source_root" rev-parse HEAD)
if [[ "$actual_revision" != "$source_revision" ]]; then
    echo "expected DA3 revision $source_revision, got $actual_revision" >&2
    exit 65
fi
if [[ -n $(git -C "$source_root" status --porcelain) ]]; then
    echo "DA3 source checkout must be clean" >&2
    exit 65
fi

if ! command -v "$python_bin" >/dev/null 2>&1; then
    echo "Python 3.11 is required; set PYTHON_BIN to its executable" >&2
    exit 69
fi
python_version=$($python_bin -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [[ "$python_version" != 3.11 ]]; then
    echo "expected Python 3.11, got $python_version" >&2
    exit 65
fi

mkdir -p "$download_dir" "$coreml_dir" "$graph_dir" "$trace_dir"
if [[ ! -f "$weights_path" ]]; then
    curl -fL \
        "https://huggingface.co/depth-anything/DA3-SMALL/resolve/$weight_revision/model.safetensors" \
        -o "$weights_path"
fi
actual_weight_sha256=$(shasum -a 256 "$weights_path" | awk '{print $1}')
if [[ "$actual_weight_sha256" != "$weight_sha256" ]]; then
    echo "DA3 weights SHA-256 mismatch" >&2
    echo "expected $weight_sha256, got $actual_weight_sha256" >&2
    exit 65
fi
reference_image="$source_root/assets/examples/SOH/000.png"
actual_reference_sha256=$(shasum -a 256 "$reference_image" | awk '{print $1}')
if [[ "$actual_reference_sha256" != "$reference_image_sha256" ]]; then
    echo "DA3 reference image SHA-256 mismatch" >&2
    exit 65
fi

if [[ ! -x "$venv_dir/bin/python" ]]; then
    "$python_bin" -m venv "$venv_dir"
fi
if [[ "${COREML_SKIP_INSTALL:-0}" != 1 ]]; then
    "$venv_dir/bin/python" -m pip install "pip==26.2.1"
    "$venv_dir/bin/python" -m pip install \
        -r "$source_root/tools/coreml/requirements-coreml.txt"
fi

build_variant() {
    local input_size=$1
    local model_name=$2
    local model_path="$coreml_dir/$model_name.mlpackage"
    local trace_path="$trace_dir/${model_name}_traced.pt"
    if [[ -e "$model_path" || -e "$trace_path" ]]; then
        echo "refusing to replace existing DA3 output for $model_name" >&2
        exit 73
    fi

    KMP_DUPLICATE_LIB_OK=TRUE "$venv_dir/bin/python" \
        "$source_root/tools/coreml/export_camera_token.py" \
        --model-name da3-small \
        --model-source "$weights_path" \
        --input-size "$input_size" \
        --use-image-input \
        --grayscale-output \
        --compute-precision float16 \
        --trace-output "$trace_path" \
        --output "$model_path"

    KMP_DUPLICATE_LIB_OK=TRUE "$venv_dir/bin/python" \
        "$source_root/tools/coreml/validate_export.py" \
        --model "$model_path" \
        --model-source "$weights_path" \
        --image "$reference_image" \
        --input-size "$input_size"

    "$repo_root/scripts/common/convert_coreml_to_mpsgraph.sh" \
        "$model_path" "$graph_dir" "$model_name" "${MPSGRAPH_MINIMUM_TARGET:-27.0.0}"
}

case "${DA3_VARIANT:-all}" in
    518)
        build_variant 518 DepthAnything3SmallCameraTokenImageF16
        ;;
    392)
        build_variant 392 DepthAnything3SmallCameraToken392x392ImageF16
        ;;
    all)
        build_variant 518 DepthAnything3SmallCameraTokenImageF16
        build_variant 392 DepthAnything3SmallCameraToken392x392ImageF16
        ;;
    *)
        echo "DA3_VARIANT must be 518, 392, or all" >&2
        exit 64
        ;;
esac
