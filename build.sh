#!/bin/bash
set -e

cd "$(dirname "$0")"

rm -rf build dist launcher.spec launcher

# --distpath . : hasil build ditaruh langsung di root project (sejajar
# tmu-v2-standard/ dan tmu-v2-smart/), bukan di dist/ - karena launcher
# mencari kedua folder itu relatif ke lokasi exe-nya sendiri saat runtime
python3 -m PyInstaller --onefile --name launcher --distpath . launcher.py

rm -rf build launcher.spec

echo "Build selesai: ./launcher (sejajar tmu-v2-standard/ dan tmu-v2-smart/)"