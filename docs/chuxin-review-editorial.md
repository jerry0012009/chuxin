# Chuxin editorial preview handoff

This is the Chuxin review environment only. The target is
`https://chuxin-review.31-220-80-196.sslip.io/chuxin-vue/`, mapped to
`127.0.0.1:28115` and Compose project `chuxin-design-red3`, service `web`.
Do not recreate or migrate `backend`, `db` or `seed`. Do not change Nginx,
public access restrictions, API configuration or other Chuxin environments.

## Candidate and visual acceptance

Run from the candidate repository root on the preview host. The baseline is
`da39acc`; prior desktop and mobile captures are in `/mnt/data/chuxin-plateau/after`.

```bash
cd frontend
VITE_APP_BASE=/chuxin-vue/ npm run build
npm run test:unit -- --run
cd ..

revision=$(git rev-parse --short HEAD)
image="chuxin-design-red3-web:$revision"
docker build -t "$image" -f deploy/local/web.Dockerfile frontend
docker run -d --name chuxin-editorial-stage --network chuxin-design-red3_default \
  -p 127.0.0.1:28116:80 \
  -v /etc/chuxin-preview-round3/upstream.conf:/etc/nginx/conf.d/default.conf:ro "$image"

output=/mnt/data/chuxin-plateau-editorial
node /tmp/chuxin-plateau-check.mjs http://127.0.0.1:28116/chuxin-vue "$output/after"
bash frontend/tests/compare-plateau-screenshots.sh /mnt/data/chuxin-plateau/after "$output/after" "$output/compare"
```

Use only the existing preview test accounts. Confirm the admin data includes
only test accounts before capturing the dashboard. Do not share credentials,
network traces or real camera/audio input. Run the same viewports and inspect the
paired images at 1440×1000 and 390×844. Check the mobile menu and active link,
long task titles, rows and status labels, empty and retry states, focus and
Escape in history, and the short-viewport answer composer (320×568, 844×390,
390×460). The acceptance script additionally covers task detail, module switching,
camera preview with a fake device, scale report, plan, audio playback, publishing
validation, access redirection and logout. `CHECK_CONTINUE=1` also opens the next
task item and may mutate the test account's task state. Capture comparison images
before doing that, and do not submit a real assessment or publish a real task.

## Publish and roll back

After stage passes, check the current image and confirm the rendered Compose
configuration binds `web` only to `127.0.0.1:28115`. Tag the running image by ID
before changing the project image. Keep the rollback tag; do not prune it.

```bash
old=$(docker inspect --format '{{.Image}}' chuxin-design-red3-web-1)
rollback="chuxin-design-red3-web:rollback-${old:7:12}"
docker image tag "$old" "$rollback"
compose=(docker compose -p chuxin-design-red3 \
  -f "$PWD/compose.yaml" -f /etc/chuxin-preview-round3/compose.override.yaml)

docker image tag "$image" chuxin-design-red3-web:latest
CHUXIN_LOCAL_PORT=28115 "${compose[@]}" up -d --no-deps --no-build --force-recreate web
curl -fsS https://chuxin-review.31-220-80-196.sslip.io/chuxin-vue/api/health
node /tmp/chuxin-plateau-check.mjs https://chuxin-review.31-220-80-196.sslip.io/chuxin-vue "$output/public"
```

Confirm the new image ID on `web` and unchanged backend/database container IDs.
On failure, tag `$rollback` back to `chuxin-design-red3-web:latest`, repeat the
same `up` command for `web` only, and recheck the public health endpoint. Remove
the staging container after acceptance or rollback.
