# Chuxin

The canonical checkout on the deployment host is `/root/jerry/chuxin` on
`main`, tracking [GitHub](https://github.com/jerry0012009/chuxin). Use task
branches and temporary worktrees for isolated changes; merge reviewed changes
back into `main` so neither application depends on a task worktree. Gitee is
not a routine sync target.

| Directory | What to maintain there |
| --- | --- |
| [`frontend/`](frontend/) | Vue frontend and browser tests |
| [`backend/`](backend/) | Java 21 Spring Boot API and Flyway migrations |
| [`scale-imports/`](scale-imports/) | Questionnaire definitions and import scripts |
| [`deploy/current-host/`](deploy/current-host/README.md) | Current public trial deployment and operations |

From `frontend/`, run `npm ci`, `npm run test:unit -- --run`, and
`VITE_APP_BASE=/chuxin-vue/ npm run build`. From `backend/`, run `mvn test` or
`mvn package` with Java 21. Follow the [recovery guide](RECOVERY.md) to rebuild
the questionnaire library in an isolated database.

The [public trial](https://eu.jerrypsy.top/chuxin-vue/) serves built artifacts
from `/opt/chuxin/current`, not source files from the checkout. Updating `main`
does not deploy it. Keep runtime credentials, database exports, and user data
out of Git.

The GitHub history starts with the sanitized pre-redesign source snapshot
tagged `baseline/github-pre-redesign-2026-11-22`. It does not include the
legacy database dump, raw sensor recordings, or legacy commit history. Use
`OPENROUTER_API_KEY` to enable OpenRouter outside the public trial. The GitHub
tag is a source reference, not the deployed build.
