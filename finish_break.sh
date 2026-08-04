#!/usr/bin/env bash
# Encode the break film, refresh the site, deploy, push.
# Deploys ONLY with the explicit site id (see .netlify-site-id).
set -euo pipefail
cd "$(dirname "$0")"
SID=$(cat .netlify-site-id)

ffmpeg -y -framerate 24 -i frames_break/b_%04d.png -c:v libx264 -pix_fmt yuv420p \
  -crf 18 -movflags +faststart out/pool-break.mp4
ffmpeg -y -i out/pool-break.mp4 -ss 5.5 -frames:v 1 -q:v 3 site/poster.jpg

cp out/pool-break.mp4 site/pool-game.mp4
netlify deploy --prod --dir site --site "$SID" | tee /tmp/pool-deploy.out
grep -q "pool-table-test" /tmp/pool-deploy.out || {
  echo "WRONG SITE — investigate before anything else"; exit 1; }

git add -A && git commit -m "break film: anatomical table, human player, real pocket drops

Built with Claude Code (LiFi NYC)" && git push origin master
echo "FINISH PASS COMPLETE"
