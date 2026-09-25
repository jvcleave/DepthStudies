#!/bin/bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DA3_VARIANT=518 exec "$script_dir/build.sh"
