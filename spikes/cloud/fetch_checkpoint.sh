#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
read -r warp_release_tag warp_asset_sha < <(python - <<'PY'
import json
m=json.load(open('spikes/cloud/checkpoint.json'))
print(m['release_tag'],m['sha256'])
PY
)
mkdir -p build/cloud_download
# Initial push starts CI before the authorized experimental asset is published.
# Allow a short upload window; fail if the asset never appears.
for warp_attempt in {1..18}; do
    if gh release download "$warp_release_tag" --repo "$GITHUB_REPOSITORY" \
        --pattern compact-checkpoint.tar.gz --dir build/cloud_download; then
        break
    fi
    sleep 10
done
if [ ! -s build/cloud_download/compact-checkpoint.tar.gz ]; then
    mkdir -p build/cloud_setup
    python - <<'PY'
import json
from pathlib import Path
Path('build/cloud_setup/checkpoint_status.json').write_text(json.dumps({
    'status': 'blocked_before_eda',
    'reason': 'Required experimental release asset is not available',
    'design_tested': False,
})+'\n')
PY
    echo '::error::Checkpoint asset unavailable: EDA did not start; this is an input/setup failure, not a routing or functional result.' >&2
    exit 2
fi
python spikes/cloud/checkpoint.py materialize \
    --archive build/cloud_download/compact-checkpoint.tar.gz \
    --sha256 "$warp_asset_sha" --out build/cloud_input
