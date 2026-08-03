#!/usr/bin/env bash
# Finish pass after the full render: encode, poster, site, push.
# Deploys ONLY with the explicit site id (see .netlify-site-id).
set -euo pipefail
cd "$(dirname "$0")"
SID=$(cat .netlify-site-id)

ffmpeg -y -framerate 30 -i frames/f_%04d.png -c:v libx264 -pix_fmt yuv420p \
  -crf 18 -movflags +faststart out/pool-game.mp4
ffmpeg -y -i out/pool-game.mp4 -ss 6.0 -frames:v 1 -q:v 3 site/poster.jpg

cp out/pool-game.mp4 site/pool-game.mp4
netlify deploy --prod --dir site --site "$SID" | tee /tmp/pool-deploy.out
grep -q "pool-table-test" /tmp/pool-deploy.out || {
  echo "WRONG SITE — investigate before anything else"; exit 1; }

git add -A && git commit -m "film: final render + site deploy

Built with Claude Code (LiFi NYC)" && git push origin master
echo "FINISH PASS COMPLETE"
