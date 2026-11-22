# Chuxin

## 本地快速启动

安装并启动 Docker（需包含 Compose v2）。在 GitHub 克隆或解压下载的源码后，在项目根目录运行：

```sh
docker compose up --build -d
```

首次启动需要联网下载基础镜像和构建依赖，并会自动创建 MySQL 数据库、执行 Flyway 迁移、导入仓库自带的量表。命令成功后打开 `http://127.0.0.1:18090/chuxin-vue/`，注册普通用户，进入「量表测评 → 自由测评」即可作答。初始化共发布 **156 套量表**：90 套普通用户可自测，另外 66 套华心云原始量表仅在后台量表库提供。注册、答题、评分和查看报告不需要 API 密钥、旧站账号或数据库备份。

`docker compose stop` 停止本地服务，数据库保留在 Docker 卷中。已初始化的量表不会在启动时重新导入。排查启动问题可运行 `docker compose logs db backend seed web`；如果本机端口冲突，设置 `CHUXIN_LOCAL_PORT` 后再启动。

这套配置仅供本机试用，网页只监听回环地址，不对外暴露 API 容器或 MySQL。AI、文件上传和传感器流不在默认启动范围内。高级恢复流程见 [数据恢复指南](RECOVERY.md)。

## Repository layout

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
| [`sql/`](sql/) | Legacy database schema and synthetic import fixture |
| [`hardware/`](hardware/) | Sensor protocols, MATLAB references and recorded test fixtures |
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
tagged `baseline/github-pre-redesign-2026-11-22`. Current `main` also includes
the recorded hardware test fixtures and an importable legacy database fixture
with synthetic accounts. The original database dump and legacy commit history
are not published. Set `OPENROUTER_API_KEY` in the environment to enable
OpenRouter outside the public trial. The GitHub tag is a source reference, not
the deployed build.
