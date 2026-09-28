#!/bin/bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZIPDEPTH_VARIANT=1536x864 exec "$script_dir/build.sh"
