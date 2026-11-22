# Chuxin 数据恢复指南

本文档记录换服务器、重建数据库或误删数据后的恢复路径。

如果只是从 GitHub 下载后本机试用，请用 [本地快速启动](README.md#本地快速启动)。Compose 会在新数据库自动导入全部量表，无需执行下文的手动恢复命令。手动恢复会覆盖同名量表，请只指向隔离的恢复库。

## 量表库

项目历史里有两类量表来源，需要分开理解。

### 1. 华心云原始导出

2026-07-02 使用华心云演示租户接口重新导出原始量表库：

- 来源站点：`https://psy.rooteam.cn`
- 租户：`演示租户`，`tenant-id=168`
- 列表接口：`/admin-api/pss/surveys/page?pageNo=1&pageSize=100`
- JSON 接口：`/admin-api/pss/surveys/getSurveysJSon?id=<id>`

导出结果已提交到 Git：

- `scale-imports/huaxinyun-original/json/survey_*.json`：66 个原始华心云 JSON。
- `scale-imports/huaxinyun-original/manifest.json`：导出来源、数量和每个量表的题目/维度/结果数量。

这批量表导入 Chuxin 后使用 `huaxinyun-<华心云原始 id>` 作为 code，例如 `huaxinyun-107`。它们会发布到后台量表库，但默认 `self_test_enabled=false`，不进入用户自由测评首页，避免把演示/测试/重复问卷直接展示给用户。

### 2. Git 已跟踪的 Chuxin 量表库

当前可从 Git 完整恢复的是后续维护过的 90 个量表：

- `scale-imports/json/*.json`：72 个最终版 JSON。
- `scale-imports/scripts/p01_*.py` 到 `p90_*.py`：90 个历史量表导入脚本。
- 其中 18 个量表只存在脚本中，没有独立 JSON 文件。

恢复命令：

```bash
# Run from the repository root.
CHUXIN_BASE_URL=http://127.0.0.1:18080 \
CHUXIN_ADMIN_USERNAME=admin \
CHUXIN_ADMIN_PASSWORD=123456 \
python3 scale-imports/scripts/restore_scales.py
```

也可以传入 `CHUXIN_ACCESS_TOKEN`，避免在命令里放管理员密码：

```bash
CHUXIN_BASE_URL=http://127.0.0.1:18080 \
CHUXIN_ACCESS_TOKEN="$TOKEN" \
python3 scale-imports/scripts/restore_scales.py
```

`restore_scales.py` 会执行：

- 导入 72 个 Git 跟踪 JSON，`overwrite=true`；
- 导入 18 个只存在脚本里的量表；
- 发布全部 90 个量表；
- 打开全部 90 个量表的自由测评；
- 按历史导入顺序设置 `sort_order`。
- 导入 66 个华心云原始 JSON，发布到后台量表库但不打开自由测评。

当前生产库在 2026-07-02 的恢复结果：

- `scale_surveys`: 156
- `self_test_enabled`: 90
- `huaxinyun-<数字 id>` 原始华心云量表：66
- `scale_questions`: 6324
- `scale_options`: 26826
- `scale_dimensions`: 746
- `scale_result_definitions`: 2016

核验 SQL：

```sql
SELECT COUNT(*) FROM scale_surveys;
SELECT COUNT(*) FROM scale_surveys WHERE self_test_enabled = TRUE;
SELECT COUNT(*) FROM scale_surveys WHERE code REGEXP '^huaxinyun-[0-9]+$';
SELECT COUNT(*) FROM scale_questions;
SELECT COUNT(*) FROM scale_options;
SELECT COUNT(*) FROM scale_dimensions;
SELECT COUNT(*) FROM scale_result_definitions;
SELECT sort_order, code, title
FROM scale_surveys
WHERE code LIKE 'huaxinyun-%'
ORDER BY sort_order
LIMIT 10;
```

前 10 个量表应为：

1. `huaxinyun-sd3-dark-triad`
2. `huaxinyun-mcsds-social-desirability`
3. `huaxinyun-npi16-narcissism`
4. `huaxinyun-gad7-anxiety`
5. `huaxinyun-pss10-stress`
6. `huaxinyun-bpaq-aggression`
7. `huaxinyun-bis11-impulsiveness`
8. `huaxinyun-tipi-personality`
9. `huaxinyun-lsrp-psychopathy`
10. `huaxinyun-hsns-narcissism`

## 重新导入原始华心云 JSON

仓库已经包含原始华心云 JSON，通常直接执行 `restore_scales.py` 即可。若只想单独导入这 66 个 JSON，先获取管理员 token，再通过接口导入：

```bash
curl -fsS -X POST http://127.0.0.1:18080/api/scale-assessments/import/huaxinyun \
  -H "Authorization: Bearer $CHUXIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d @payload.json
```

`payload.json` 示例：

```json
{
  "content": [],
  "dry_run": false,
  "publish": true,
  "overwrite": true,
  "skip_invalid": false
}
```

不要提交本地 token 文件。恢复脚本支持 `CHUXIN_ACCESS_TOKEN`、`CHUXIN_ADMIN_USERNAME`、`CHUXIN_ADMIN_PASSWORD` 环境变量。

## 神经心理实验范式

实验范式静态资源在 Git 中：

- `frontend/public/neuropsych/expfactory/*`

数据库种子迁移在：

- `backend/src/main/resources/db/migration/V5__neuropsych_and_task_publishing.sql`
- `backend/src/main/resources/db/migration/V6__neuropsych_demo_tests.sql`
- `backend/src/main/resources/db/migration/V11__neuropsych_stroop.sql`
- `backend/src/main/resources/db/migration/V13__neuropsych_more_psytraining_tests.sql`
- `backend/src/main/resources/db/migration/V20__neuropsych_five_new_psytraining_games.sql`
- `backend/src/main/resources/db/migration/V21__neuropsych_five_more_psytraining_games.sql`

当前生产库在 2026-07-02 的核验结果：

- `neuropsych_tests`: 34

核验 SQL：

```sql
SELECT COUNT(*) FROM neuropsych_tests;
SELECT code, title, status, self_test_enabled
FROM neuropsych_tests
ORDER BY code;
```

## 中文疗愈素材

普通话正念疗愈素材在 Git 中：

- `frontend/public/srcs/music/mhcs-mandarin/*.mp3`
- `backend/src/main/resources/db/migration/V23__seed_nsw_mandarin_mindfulness_content.sql`

部署后检查：

- `https://jp.jerrypsy.top/chuxin-vue/healing`
- 音频 URL 应位于 `/chuxin-vue/srcs/music/mhcs-mandarin/`

## 部署路径

标准仓库路径：

- `/root/jry/chuxin`

后端构建：

```bash
cd /root/jry/chuxin/backend
mvn -q -DskipTests package
```

前端构建：

```bash
cd /root/jry/chuxin/frontend
npm run build
```

如果新增或修改 Flyway 迁移，需要在维护窗口重启 `chuxin-backend`，让迁移正式记录到 `flyway_schema_history`。

## API 核验

使用管理员 token 核验管理端和自由测评接口：

```bash
curl -fsS http://127.0.0.1:18080/api/scale-assessments/surveys \
  -H "Authorization: Bearer $CHUXIN_ACCESS_TOKEN"

curl -fsS http://127.0.0.1:18080/api/scale-assessments/free-surveys \
  -H "Authorization: Bearer $CHUXIN_ACCESS_TOKEN"
```

执行 `restore_scales.py` 后，管理端接口应返回 156 个量表，自由测评接口应返回 90 个量表。
