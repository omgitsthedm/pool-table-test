#!/usr/bin/env bash
# Encode the break, deploy the bare video page.
set -euo pipefail
cd "$(dirname "$0")"
SID=$(cat .netlify-site-id)
ffmpeg -y -framerate 24 -i frames_break/f_%04d.png -c:v libx264 -pix_fmt yuv420p \
  -crf 18 -movflags +faststart out/break.mp4
ffmpeg -y -i out/break.mp4 -ss 11.0 -frames:v 1 -q:v 3 site/poster.jpg
cp out/break.mp4 site/break.mp4
netlify deploy --prod --dir site --site "$SID" | tee /tmp/brk-deploy.out
grep -q "pool-table-test" /tmp/brk-deploy.out || { echo "WRONG SITE"; exit 1; }
git add -A && git commit -m "the break film: no figure, table and physics only

Built with Claude Code (LiFi NYC)" && git push origin master
echo "FINISH COMPLETE"
