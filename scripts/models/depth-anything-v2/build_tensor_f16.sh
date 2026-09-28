#!/bin/bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"

export DA2_ATTENTION_IMPLEMENTATION=decomposed
export DA2_INPUT_REPRESENTATION=tensor-f16
export DA2_BUILD_ROOT="${DA2_BUILD_ROOT:-$repo_root/build/depth-anything-v2-tensor-f16}"
export DA2_SOURCE_ROOT="${DA2_SOURCE_ROOT:-$repo_root/build/depth-anything-v2/source}"
export DA2_VENV_DIR="${DA2_VENV_DIR:-$repo_root/build/depth-anything-v2/venv}"
export DA2_CHECKPOINT="${DA2_CHECKPOINT:-$repo_root/build/depth-anything-v2/downloads/depth_anything_v2_vits.pth}"

exec "$script_dir/build.sh"
