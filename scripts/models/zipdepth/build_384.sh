#!/bin/bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZIPDEPTH_VARIANT=384 exec "$script_dir/build.sh"
