#!/bin/bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"

export ZIPDEPTH_VARIANT=1920x1088
export ZIPDEPTH_INPUT_REPRESENTATION=tensor-f16
export ZIPDEPTH_BUILD_ROOT="${ZIPDEPTH_BUILD_ROOT:-$repo_root/build/zipdepth-1920x1088-tensor-f16}"
export ZIPDEPTH_SOURCE_ROOT="${ZIPDEPTH_SOURCE_ROOT:-$repo_root/build/zipdepth/source}"
export ZIPDEPTH_VENV_DIR="${ZIPDEPTH_VENV_DIR:-$repo_root/build/zipdepth/venv}"
export ZIPDEPTH_CHECKPOINT="${ZIPDEPTH_CHECKPOINT:-$repo_root/build/zipdepth/downloads/zipdepth_base_npu.pth}"

exec "$script_dir/build.sh"
