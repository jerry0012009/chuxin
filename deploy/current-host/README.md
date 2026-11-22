# Chuxin public trial

Primary URL: `https://eu.jerrypsy.top/chuxin-vue/`. The original sslip.io URL
also serves the same database.
The app serves questionnaires on the public host; AI, file uploads and sensor
streaming are outside this trial. Regular users can self-register. Administrator
credentials are stored in `/etc/chuxin/admin-password` (root only).

- Frontend: `VITE_APP_BASE=/chuxin-vue/ npm run build` from `frontend/`.
- Backend: Java 21 and Maven, `mvn package` from `backend/`.
- Artifacts: `/opt/chuxin/releases/<release>/backend.jar` and
  `/opt/chuxin/releases/<release>/web/chuxin-vue/`. `/opt/chuxin/current`
  points at the deployed release. Restart `chuxin-public.service` after switching.
- MySQL: `docker compose -f /etc/chuxin/compose.yaml ps`. The persistent
  `chuxin_mysql-data` volume is independent of the application release. MySQL
  and the backend only listen on loopback. Do not run Compose down with `-v`.
- HTTPS: Include `/etc/nginx/snippets/chuxin-eu-locations.conf` inside the
  `eu.jerrypsy.top` HTTPS server. Nginx serves the frontend and proxies
  `/chuxin-vue/api/`. For the original hostname, Certbot
  uses `/var/www/chuxin-acme` for webroot verification. The renewal deploy hook
  validates the Nginx configuration and reloads it for this certificate only.
- Backups: `chuxin-backup.timer` keeps local compressed MySQL dumps for at
  least 14 days in `/var/backups/chuxin/`. Run `systemctl start chuxin-backup.service`
  for an on-demand backup. Local backups do not protect against loss of the host.
- Smoke test: from `frontend/`, set `CHUXIN_TRIAL_URL` to the trial URL and run
  `node tests/public-trial.smoke.mjs` after installing Playwright Chromium. It
  registers a temporary synthetic user and completes GAD-7 on the live site.

The initial database was created by Flyway and populated from the tracked
scale library, not from a historical user-data dump. Expected baseline: 156
published surveys (90 curated self-tests and 66 original library-only items),
6,324 questions, 26,826 options, 746 dimensions, and 2,016 result definitions.
Run the restore script only against an empty recovery database; it overwrites
survey definitions.

The EU deployment imported three active ordinary accounts and their profiles
from the legacy database, preserving password hashes. The legacy administrator
and pending task records were not imported; there were no legacy questionnaire
submissions. The export/import helpers are insert-only and are not intended to
be rerun against the same accounts. Keep export and SQL streams private.

To take the trial offline, remove the Chuxin include from the EU vhost, unlink
`/etc/nginx/sites-enabled/chuxin-https.conf` and
`/etc/nginx/sites-enabled/chuxin-http.conf`, run `nginx -t`, and reload
Nginx. This does not delete data or stop other services. Do not roll back to
an unpatched application build while the public vhost is enabled.
