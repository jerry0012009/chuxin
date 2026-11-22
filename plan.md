# chuxin 发布干预任务与疗愈计划开发计划

> 目标：参照现有“发布测评任务”机制，新增独立的“发布干预任务”功能。医生端可以按初筛风险或手工指定，为用户发布跨菜单干预计划；患者端在任务中心和疗愈计划中看到所有待完成子项目，并在冥想、心情、游戏、知识、脑机干预等真实入口完成任务。任务完成后同步进度、生成每日小结日历，并在干预结束时提醒医生查看。

## 1. 当前代码基线

### 1.1 已可复用能力

- 测评任务发布：
  - 后端：`backend/src/main/java/chuxin/assessmenttasks/AssessmentPublishTaskService.java`
  - 前端：`frontend/src/pages/doctor/AssessmentTaskPublishingPage.vue`
  - 患者端任务中心：`frontend/src/pages/user/AssessmentTaskCenterPage.vue`
  - 模式：`batch -> item -> assignee -> item_record`，支持医生发布、用户任务中心、子项目完成回写、报告生成。
- 疗愈内容：
  - 数据表：`healing_contents`、`user_healing_records`、`meditation_sessions`
  - 患者端：`frontend/src/pages/user/HealingPage.vue`
  - 已有模块：冥想、游戏、日记、知识文章/视频。
- 心情日记：
  - 数据表：`emotion_diaries`
  - 患者端：`frontend/src/pages/user/RecordPage.vue` 和 `HealingPage.vue` 的日记 tab。
  - 目前按 `user_id + diary_date` 唯一，每天天然只能保存一条主日记，适合干预任务“一天一次”。
- 医生知识库：
  - 前端：`frontend/src/pages/doctor/KnowledgePage.vue`
  - 表：`knowledge_base`
  - 当前主要是后台知识资料，患者端疗愈页读取的是 `healing_contents` 中的 knowledge 内容；后续应统一干预素材来源。
- 菜单结构：
  - 患者端主菜单已有：任务中心、量表测评、多模态评估、神经心理、疗愈。
  - 医生端主菜单已有：发布测评任务、量表测评、神经心理测评、知识库、用户管理等。

### 1.2 当前缺口

- `AssessmentTaskCenterPage.vue` 下方“干预训练任务”仍是静态数组，未接后端。
- `HealingPlanPage.vue` 是静态 21 天疗愈计划，任务不可由医生发布，进度不会同步。
- 冥想、知识、游戏、心情日记目前只记录自身行为，不知道自己是否属于某个“干预任务”。
- 没有“发布干预任务”的医生端页面，也没有按初筛风险自动匹配干预方案的后端逻辑。
- 没有脑机干预用户端菜单和任务完成记录。
- 没有按天汇总的干预小结日历，也没有医生端干预结束提醒。

### 1.3 代码对照结论

- `frontend/src/pages/user/AssessmentTaskCenterPage.vue`
  - 现有页面已经是“测评与干预任务中心”的壳，但干预部分是本地 `interventionTasks` 静态数组。
  - 后续不需要新建一个并列任务中心，而是在这个页面替换静态干预区，接入 `getMyInterventionTodayTasks()` 和日历接口。
  - 页面顶部当前只统计测评进度，后续应增加“今日干预”摘要，但不要把干预大卡堆在测评卡下面。
- `frontend/src/pages/user/HealingPage.vue`
  - 页面内部已有四个 tab：`meditation | game | diary | knowledge`。
  - 冥想完成当前走 `createMeditationSession()`，知识当前只做浏览、点赞、收藏和播放，游戏当前只是打开外链，日记当前写入 `emotion_diaries`。
  - 因此最合理的落点是给这个页面增加“干预任务模式”，而不是拆散疗愈页。进入任务时通过 query 精确定位 tab、素材和 `interventionRecordId`。
- `frontend/src/pages/user/HealingPlanPage.vue`
  - 当前所有任务、阶段、弹窗和 21 天计划均是本地静态数据。
  - 后续应整体改为真实 `getMyInterventionPlan()` 驱动；不要保留旧静态 `tasks/milestones/explorePlans` 作为业务数据，只可复用局部视觉样式。
- `frontend/src/pages/user/RecordPage.vue`
  - 心情日记保存集中在 `saveCurrentDiary()`，并通过 `createEmotionRecord()` upsert 到 `emotion_diaries`。
  - 任务联动应在保存成功后调用干预完成接口；自由入口保存时也可顺手查询当天是否有未完成心情任务并自动完成。
- `frontend/src/layouts/UserLayout.vue`
  - 患者端主菜单已有“任务中心”和“疗愈”，脑机干预本期不建议直接加入主菜单，避免移动端底栏继续变宽；先通过任务中心/疗愈计划进入。
- `frontend/src/layouts/DoctorLayout.vue`
  - 医生端已有“发布测评任务”，新增“发布干预任务”应紧跟其后，保持同级。
- `frontend/src/pages/doctor/PatientsPage.vue`
  - 患者详情目前 tab 是综合测评报告、量表、语音、表情、对话记录。
  - 后续增加 `intervention` tab 最稳妥，不要混在现有综合测评报告 tab 里。
- `frontend/src/pages/doctor/AlertsPage.vue`
  - 已按 `risk_alerts` 展示 `alert_type/data_source/source_id`，干预结束提醒可先复用该页面。
  - 只需补充显示文案和数据来源筛选，不必新建提醒系统。
- `backend/src/main/java/chuxin/db/TableRegistry.java`
  - 通用 `/api/data/{table}` 必须在 `TableRegistry` 中登记表和 JSON 字段，否则前端直接访问新表会报“不支持的数据表”。
  - 本功能建议主要走专用 `/api/intervention-tasks` 接口；如果医生端或统计页需要通用查询，也要同步白名单。
- `backend/src/main/java/chuxin/db/GenericDataService.java`
  - 读写作用域已经对测评任务做了专用接口保护。新增干预表后也要在 `applyReadScope/applyWriteScope/prepareWritablePayload/enrichRows` 中补权限规则。
  - 患者只能读写自己的干预记录；医生/admin 才能管理发布任务和模板。
- `backend/src/main/java/chuxin/config/SecurityConfig.java`
  - `/api/**` 网络层是 `permitAll`，真正鉴权靠 JWT filter 后的 service 层 `requireUser/requireStaff`。
  - 新增接口必须在 service 层显式校验身份，不能依赖 Spring Security 路径拦截。

## 2. 产品范围

### 2.1 本期要做

- 新增医生端“发布干预任务”，与“发布测评任务”同级。
- 新增后端干预任务编排系统，独立于测评任务，但结构尽量同构。
- 默认干预方案按职务犯罪初筛报告风险分层自动匹配：
  - 低风险
  - 中风险
  - 高风险
- 支持医生编辑默认干预方案。
- 支持医生手工指定干预任务，可以从已有小项目中选择。
- 患者端任务中心合并展示所有干预子项目，不展示多张干预任务大卡。
- 患者端“疗愈计划”改为真实干预计划页，展示当前计划、每日子项目和完成进度。
- 在实际功能入口增加任务完成按钮：
  - 冥想：指定音频，可多选。
  - 心情：每天最多完成 1 次，不需要倒计时。
  - 游戏：作为大类选择，前期可用现有 Temple Run 外链入口。
  - 知识：文章和视频均可作为任务项。
  - 脑机干预：先做用户端菜单和模拟完成，包含光调控、磁调控、脑机接口调控。
- 需要倒计时的任务，前期统一 10 秒倒计时后才能点“完成”；心情日记不倒计时。
- 干预任务带持续时间和完成规则，达到固定次数/天后结束。
- 任务中心底部展示干预日历，点击日期查看当日完成任务和小结。
- 医生端看到干预任务进度、用户完成明细和干预结束提醒。

### 2.2 本期不做

- 不做真实脑机设备接入。
- 不做复杂 21 天多阶段自动解锁逻辑。
- 不做干预效果的临床诊断结论，只做完成追踪、风险分层建议和随访提醒。
- 不强制改造现有 AI 多模态报告；只读取已生成的职务犯罪初筛任务报告来匹配默认干预方案。

## 3. 设计规格

DESIGN SPECIFICATION
====================
1. Purpose Statement：干预任务面向已经完成或正在随访的用户，核心是让用户每天清楚知道“今天要做什么”，并在真实功能页完成。医生端核心是快速给一组用户安排可执行、可追踪、可调整的疗愈计划。
2. Aesthetic Direction：临床秩序感 + 温和陪伴。延续 chuxin 当前浅色、圆角、lucide 图标和柔和渐变体系，但任务列表要更克制，避免把干预做成营销页。
3. Color Palette：沿用项目现有 Tailwind token；干预主色建议使用 `emerald/cyan`，待完成用 `slate`，完成用 `emerald`，到期/提醒用 `amber`，高风险干预提示用 `rose`。
4. Typography：沿用现有项目字体栈，不引入新字体，避免和已上线页面割裂。
5. Layout Strategy：患者端采用“今日待办列表 + 当前计划摘要 + 日历小结”的垂直结构；医生端采用“默认方案配置 + 手动发布 + 进度追踪”的管理台结构。

## 4. 核心业务规则

### 4.1 干预任务与测评任务的关系

- 干预任务与测评任务平级，不复用 `assessment_publish_*` 表。
- 任务中心统一展示两类任务：
  - 测评任务：职务犯罪初筛、手工发布测评任务。
  - 干预任务：默认风险分层干预、手工发布干预任务。
- 任务中心不展示多张“干预任务卡片”，只展示合并后的“今日干预子项目”。
- 如果用户同时存在多个干预任务，按子项目去重和排序展示：
  - 同一音频同一天只展示一次。
  - 心情日记同一天只展示一次。
  - 脑机干预不同类型分别展示。
  - 知识/视频可按具体内容展示，也可按“知识卡片任选 1 个”展示。

### 4.2 完成规则

- `completion_mode = diary_once`：心情日记，保存当天日记后自动完成，不需要倒计时。
- 心情日记任务入口统一进入患者端“疗愈-日记”，不另起一套日记流程；独立心情记录页仍可作为自由记录入口存在。
- `completion_mode = countdown`：冥想、知识、游戏、脑机干预，进入对应页面后前端倒计时，倒计时结束后按钮从灰色变为可点击。
- `completion_mode = media_end`：后续可用于音频/视频真实播放到一定比例；本期先不强依赖，统一 10 秒。
- 任务完成后写入干预任务记录，并同步：
  - 子项目状态。
  - 当日完成数。
  - 当前计划进度。
  - 任务中心展示状态。
- 已完成子项目当天可重新进入内容，但不重复计数；页面显示“今日已完成，可再次练习”。

### 4.2.1 任务池、每日发布数量与多计划并集

- 医生发布干预任务时，勾选的是该计划的“任务池”，记为 `N` 个项目。
- `daily_required_count` 在页面上命名为“每日发布数量”，记为 `M`。
- 每天为每个计划从任务池中稳定随机抽取项目：
  - 如果 `N > M`，当天抽取 `M` 个项目。
  - 如果 `N <= M`，当天发布全部 `N` 个项目。
- 不再在干预计划里区分“必做/选做”。任务中心只展示当天被发布的干预任务；其他疗愈内容用户可以自由练习，但不在任务中心展示。
- 用户同时参与多个干预计划时，任务中心展示当天项目的并集；同一个项目只展示一次。
- 同一个项目如果同时属于多个计划，用户完成一次会同步回写所有相关计划。
- 每个计划的完成天数仍按该计划当天抽取出的项目是否完成计算；任务中心的今日进度按并集项目显示，避免多计划共享项目时数字大于卡片数量。

### 4.3 持续时间与结束

- 每个干预任务有：
  - `duration_days`
  - `daily_required_count`
  - `start_date`
  - `end_date`
  - `completion_target_days`，默认等于 `duration_days`
- 达到以下任一条件后，任务进入结束状态：
  - 当前日期超过 `end_date`。
  - 已完成天数达到 `completion_target_days`。
- 结束后医生端出现提醒：
  - `干预已结束`
  - `完成率`
  - `建议复查/重新发布/结束随访`

### 4.4 与初筛结果联动

- 触发时机：
  - 第一触发点：用户完成“职务犯罪风险与心理状态初筛”并生成总报告后，后端立即按报告风险分层自动发布干预任务。
  - 第二触发点：存量用户或历史报告用户打开患者端任务中心、疗愈计划、干预日历时，后端会执行一次默认干预确保逻辑；如果发现已有初筛总报告但尚未发放干预任务，会自动补发对应风险方案。
  - 第三触发点：医生端可通过干预任务专用接口执行全量存量补发，用于上线后一次性补齐历史用户。
- 风险来源：
  - 优先读取 `assessment_type = 'assessment_package_report'` 且 `report.packageData.taskType = 'initial_screening'` 的最新报告。
  - 使用 `report.overall.riskLevel` 和 `score`。
- 映射：
  - `none/no/normal` 或没有完成初筛 -> 基础稳定关怀计划。
  - `low` -> 低风险干预方案。
  - `middle/medium` -> 中风险干预方案。
  - `high` -> 高风险干预方案。
- 自动分配需要防重：
  - 同一用户同一份初筛报告只自动生成一次默认干预任务。
  - 未完成初筛用户的基础稳定关怀计划只自动生成一次。
  - 如果医生后续手工发布，可以并存。

### 4.5 基础稳定关怀计划

- 适用对象：
  - 未完成职务犯罪初筛的用户。
  - 初筛总报告明确为无风险/正常的用户。
  - 存量用户上线时没有可用初筛总报告的用户。
- 默认内容：
  - 心情日记：每日 1 次。
  - 焦虑缓解呼吸法：每日 1 次，10 秒后可完成。
- 默认周期：3 天。
- 展示方式：和其他干预任务一样进入任务中心/疗愈计划，但不展示成多张任务大卡，只合并展示今日子项目。

## 5. 默认干预方案建议

### 5.1 低风险方案，建议 7 天

目标：维持稳定状态，建立日常情绪记录习惯。

- 心情日记：每日 1 次。
- 焦虑缓解呼吸法：每日 1 次，10 秒体验完成。
- 知识文章：如何应对焦虑情绪，任选 1 次。
- 视频：运动与心理健康，任选 1 次。

总项目：4 个，不超过用户负担。

### 5.2 中风险方案，建议 14 天

目标：加强情绪识别、冲动控制和压力调节。

- 心情日记：每日 1 次。
- 身体扫描冥想：每日 1 次。
- 专注力训练：每周 3 次。
- 知识文章：认知行为疗法(CBT)介绍。
- 视频：睡眠与心理健康。
- 游戏：Temple Run 2 跑酷，作为轻量行为激活任务。

总项目：6 个。

### 5.3 高风险方案，建议 14 天或 21 天

目标：提高随访频率，强化稳定化任务，避免单纯自助。

- 心情日记：每日 1 次。
- 焦虑缓解呼吸法：每日 1 次。
- 睡前放松引导：每日 1 次或睡前推荐。
- 身体扫描冥想：每周 3 次。
- 知识文章：家人如何支持抑郁症患者，或医生可替换。
- 视频：睡眠与心理健康。
- 脑机干预：光调控，模拟任务，10 秒后可完成。
- 脑机干预：脑机接口调控，模拟任务，10 秒后可完成。

总项目：8 个。高风险方案页面必须提示“该计划不能替代专业诊疗，请按医生建议随访”。

## 6. 数据库设计

新增迁移建议：`backend/src/main/resources/db/migration/V15__intervention_tasks.sql`

### 6.1 干预素材表

```sql
CREATE TABLE intervention_materials (
  id CHAR(36) PRIMARY KEY,
  code VARCHAR(96) NOT NULL UNIQUE,
  title VARCHAR(255) NOT NULL,
  description TEXT NULL,
  category ENUM('meditation','mood','game','knowledge','brain_intervention') NOT NULL,
  subtype VARCHAR(64) NULL,
  target_ref_table VARCHAR(64) NULL,
  target_ref_id CHAR(36) NULL,
  route_path VARCHAR(255) NOT NULL,
  duration_sec INT NOT NULL DEFAULT 10,
  completion_mode ENUM('countdown','diary_once','media_end') NOT NULL DEFAULT 'countdown',
  tags JSON NULL,
  config_json JSON NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)
);
```

说明：
- 冥想素材引用 `healing_contents.id`。
- 知识文章/视频优先引用 `healing_contents.id`，医生知识库可后续同步到 `healing_contents`。
- 心情日记不需要 `target_ref_id`，使用 `route_path = '/record'` 或 `'/healing?tab=diary'`。
- 游戏本期可使用 `config_json.externalUrl`。
- 脑机干预先使用虚拟素材，不依赖设备表。

### 6.2 默认方案模板

```sql
CREATE TABLE intervention_plan_templates (
  id CHAR(36) PRIMARY KEY,
  code VARCHAR(96) NOT NULL UNIQUE,
  title VARCHAR(255) NOT NULL,
  risk_level ENUM('low','middle','high') NOT NULL,
  description TEXT NULL,
  duration_days INT NOT NULL DEFAULT 7,
  daily_required_count INT NOT NULL DEFAULT 1,
  auto_assign_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  status ENUM('draft','active','stopped') NOT NULL DEFAULT 'active',
  created_by CHAR(36) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  CONSTRAINT fk_intervention_templates_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE intervention_plan_template_items (
  id CHAR(36) PRIMARY KEY,
  template_id CHAR(36) NOT NULL,
  material_id CHAR(36) NOT NULL,
  title VARCHAR(255) NOT NULL,
  frequency_type ENUM('daily','weekly','once','plan_total') NOT NULL DEFAULT 'daily',
  required_count INT NOT NULL DEFAULT 1,
  duration_sec INT NOT NULL DEFAULT 10,
  order_no INT NOT NULL DEFAULT 1,
  required BOOLEAN NOT NULL DEFAULT TRUE,
  config_json JSON NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT fk_intervention_template_items_template FOREIGN KEY (template_id) REFERENCES intervention_plan_templates(id) ON DELETE CASCADE,
  CONSTRAINT fk_intervention_template_items_material FOREIGN KEY (material_id) REFERENCES intervention_materials(id) ON DELETE RESTRICT
);
```

### 6.3 发布任务主表

```sql
CREATE TABLE intervention_publish_batches (
  id CHAR(36) PRIMARY KEY,
  batch_type ENUM('manual','auto_after_screening') NOT NULL DEFAULT 'manual',
  template_id CHAR(36) NULL,
  source_assessment_id CHAR(36) NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT NULL,
  risk_level ENUM('low','middle','high') NULL,
  duration_days INT NOT NULL DEFAULT 7,
  daily_required_count INT NOT NULL DEFAULT 1,
  status ENUM('draft','active','stopped','completed') NOT NULL DEFAULT 'draft',
  start_date DATE NULL,
  end_date DATE NULL,
  recipient_type ENUM('users','groups') NOT NULL DEFAULT 'users',
  recipient_scope JSON NULL,
  created_by CHAR(36) NULL,
  published_at DATETIME(3) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  CONSTRAINT fk_intervention_batches_template FOREIGN KEY (template_id) REFERENCES intervention_plan_templates(id) ON DELETE SET NULL,
  CONSTRAINT fk_intervention_batches_source_assessment FOREIGN KEY (source_assessment_id) REFERENCES assessments(id) ON DELETE SET NULL,
  CONSTRAINT fk_intervention_batches_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE intervention_publish_items (
  id CHAR(36) PRIMARY KEY,
  batch_id CHAR(36) NOT NULL,
  material_id CHAR(36) NOT NULL,
  item_type ENUM('meditation','mood','game','knowledge','brain_intervention') NOT NULL,
  subtype VARCHAR(64) NULL,
  title VARCHAR(255) NOT NULL,
  route_path VARCHAR(255) NOT NULL,
  required BOOLEAN NOT NULL DEFAULT TRUE,
  frequency_type ENUM('daily','weekly','once','plan_total') NOT NULL DEFAULT 'daily',
  required_count INT NOT NULL DEFAULT 1,
  duration_sec INT NOT NULL DEFAULT 10,
  order_no INT NOT NULL DEFAULT 1,
  config_json JSON NULL,
  status ENUM('enabled','disabled') NOT NULL DEFAULT 'enabled',
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  CONSTRAINT fk_intervention_items_batch FOREIGN KEY (batch_id) REFERENCES intervention_publish_batches(id) ON DELETE CASCADE,
  CONSTRAINT fk_intervention_items_material FOREIGN KEY (material_id) REFERENCES intervention_materials(id) ON DELETE RESTRICT
);
```

### 6.4 用户任务与每日记录

```sql
CREATE TABLE intervention_publish_assignees (
  id CHAR(36) PRIMARY KEY,
  batch_id CHAR(36) NOT NULL,
  user_id CHAR(36) NOT NULL,
  source_assessment_id CHAR(36) NULL,
  status ENUM('pending','in_progress','completed','expired','cancelled') NOT NULL DEFAULT 'pending',
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  completed_days INT NOT NULL DEFAULT 0,
  total_completed_count INT NOT NULL DEFAULT 0,
  last_completed_at DATETIME(3) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  UNIQUE KEY uk_intervention_assignees_batch_user (batch_id, user_id),
  UNIQUE KEY uk_intervention_assignees_source_report (user_id, source_assessment_id),
  KEY idx_intervention_assignees_user_status (user_id, status, start_date),
  CONSTRAINT fk_intervention_assignees_batch FOREIGN KEY (batch_id) REFERENCES intervention_publish_batches(id) ON DELETE CASCADE,
  CONSTRAINT fk_intervention_assignees_source_assessment FOREIGN KEY (source_assessment_id) REFERENCES assessments(id) ON DELETE SET NULL,
  CONSTRAINT fk_intervention_assignees_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE intervention_item_records (
  id CHAR(36) PRIMARY KEY,
  assignee_id CHAR(36) NOT NULL,
  batch_id CHAR(36) NOT NULL,
  item_id CHAR(36) NOT NULL,
  material_id CHAR(36) NOT NULL,
  user_id CHAR(36) NOT NULL,
  plan_date DATE NOT NULL,
  status ENUM('pending','in_progress','completed','expired','cancelled') NOT NULL DEFAULT 'pending',
  source_ref_table VARCHAR(64) NULL,
  source_ref_id CHAR(36) NULL,
  duration_seconds INT NULL,
  completion_note TEXT NULL,
  summary_json JSON NULL,
  started_at DATETIME(3) NULL,
  completed_at DATETIME(3) NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  KEY idx_intervention_item_records_user_date (user_id, plan_date, status),
  KEY idx_intervention_item_records_assignee_date (assignee_id, plan_date),
  CONSTRAINT fk_intervention_records_assignee FOREIGN KEY (assignee_id) REFERENCES intervention_publish_assignees(id) ON DELETE CASCADE,
  CONSTRAINT fk_intervention_records_item FOREIGN KEY (item_id) REFERENCES intervention_publish_items(id) ON DELETE CASCADE,
  CONSTRAINT fk_intervention_records_material FOREIGN KEY (material_id) REFERENCES intervention_materials(id) ON DELETE RESTRICT,
  CONSTRAINT fk_intervention_records_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE intervention_daily_summaries (
  id CHAR(36) PRIMARY KEY,
  assignee_id CHAR(36) NOT NULL,
  user_id CHAR(36) NOT NULL,
  summary_date DATE NOT NULL,
  completed_count INT NOT NULL DEFAULT 0,
  required_count INT NOT NULL DEFAULT 0,
  mood_level VARCHAR(32) NULL,
  summary_text TEXT NULL,
  details_json JSON NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  UNIQUE KEY uk_intervention_daily_summary (assignee_id, summary_date),
  CONSTRAINT fk_intervention_daily_assignee FOREIGN KEY (assignee_id) REFERENCES intervention_publish_assignees(id) ON DELETE CASCADE,
  CONSTRAINT fk_intervention_daily_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

说明：
- `intervention_item_records` 建议采用“按天懒生成”：用户打开任务中心/疗愈计划时，后端为当天生成待办记录；避免一次性生成 21 天 * 多任务的大量记录。
- 对于 `once/plan_total` 项目，后端只在尚未完成时展示；完成后不再每日重复出现。
- 同一用户同一天可能因多个干预任务出现同一素材，数据库可以保留多条记录，接口层负责合并展示；完成某个素材时，后端应 fan-out 同步同日同素材的所有待完成记录，避免用户重复打卡同一个项目。

### 6.5 医生提醒

可复用 `risk_alerts`，新增 `data_source = 'intervention_task'`：
- 干预结束提醒：`alert_type = '干预任务结束提醒'`
- 高风险未完成提醒：`alert_type = '高风险干预未完成提醒'`

如后续需要更完整的消息中心，再新增 `doctor_notifications`。

## 7. 后端接口规划

新增包建议：`backend/src/main/java/chuxin/interventiontasks/`

### 7.1 医生端接口

- `GET /api/intervention-tasks/materials`
  - 返回可选素材：冥想、心情、游戏、知识、脑机干预。
- `GET /api/intervention-tasks/templates`
  - 返回低/中/高风险默认方案。
- `PUT /api/intervention-tasks/templates/{templateId}`
  - 医生修改默认方案标题、周期、项目列表、启停状态。
- `GET /api/intervention-tasks`
  - 返回发布干预任务列表，包含对象数、完成数、结束数。
- `POST /api/intervention-tasks`
  - 创建草稿。
- `PUT /api/intervention-tasks/{batchId}`
  - 编辑草稿。
- `POST /api/intervention-tasks/{batchId}/publish`
  - 发布给用户。
- `POST /api/intervention-tasks/{batchId}/stop`
  - 停止任务。
- `GET /api/intervention-tasks/{batchId}`
  - 查看任务详情、项目、用户完成进度。
- `POST /api/intervention-tasks/auto-assign/{assessmentId}`
  - 根据某份初筛报告为用户生成默认干预任务。

### 7.2 患者端接口

- `GET /api/intervention-tasks/my`
  - 返回当前用户所有有效干预任务摘要。
- `GET /api/intervention-tasks/my/today`
  - 返回合并后的今日干预子项目，已去重、已排序、带跳转信息。
- `GET /api/intervention-tasks/my/plan`
  - 返回疗愈计划页所需：当前计划、周期、完成率、今日任务、日历摘要。
- `POST /api/intervention-tasks/items/{recordId}/start`
  - 标记子项目开始。
- `POST /api/intervention-tasks/items/{recordId}/complete`
  - 完成子项目，写入 `source_ref_table/source_ref_id/duration_seconds/summary_json`。
- `GET /api/intervention-tasks/my/calendar?start=YYYY-MM-DD&end=YYYY-MM-DD`
  - 返回日历小结。
- `GET /api/intervention-tasks/my/calendar/{date}`
  - 返回某日完成明细和小结。

### 7.3 自动同步接口

后端服务需要提供内部方法：
- `assignDefaultInterventionByAssessment(assessmentId, userId)`
- `completeBySource(userId, sourceTable, sourceId, options)`

用于以下场景：
- 初筛报告生成后自动创建默认干预任务。
- 心情日记保存后自动完成当天心情任务。
- 冥想保存 session 后自动完成对应音频任务。

## 8. 前端患者端规划

### 8.1 任务中心改造

文件：`frontend/src/pages/user/AssessmentTaskCenterPage.vue`

改造目标：
- 页面名仍可为“任务中心”，但内部明确分区：
  - 测评任务
  - 今日干预
  - 干预日历小结
- 删除当前静态 `interventionTasks`。
- 加载：
  - `getMyAssessmentPublishTasks()`
  - `getMyInterventionTodayTasks()`
  - `getMyInterventionCalendar()`
- 干预子项目卡片字段：
  - 类型图标。
  - 项目标题。
  - 来源计划。
  - 今日状态：待完成 / 进行中 / 已完成。
  - 完成规则：倒计时 / 保存日记后自动完成。
  - 主按钮：去完成 / 今日已完成。
- 如果多个干预任务同时存在，只展示合并后的子项目，不展示多张计划卡。
- 底部新增日历小结：
  - 月视图点状标记。
  - 点击日期打开抽屉或弹窗。
  - 展示当天完成项目、未完成项目、心情摘要、小结文案。

### 8.2 疗愈计划页改造

文件：`frontend/src/pages/user/HealingPlanPage.vue`

改造目标：
- 放弃静态 21 天阶段逻辑。
- 作为真实干预计划总览页：
  - 顶部：当前干预计划摘要，展示风险分层、剩余天数、完成率。
  - 中部：今日任务列表，和任务中心同源。
  - 下方：计划内容清单，展示本计划包含哪些小项目和频率。
  - 底部：日历小结。
- 如果没有干预任务：
  - 展示“暂无医生发布的疗愈计划”，引导去疗愈自由练习。

### 8.3 疗愈页跨菜单完成按钮

文件：`frontend/src/pages/user/HealingPage.vue`

#### 冥想 tab
- 读取 query：
  - `interventionRecordId`
  - `materialId`
  - `tab=meditation`
  - `track=...`
- 如果是干预任务进入：
  - 顶部显示小型任务条：“当前干预任务中”。
  - 播放器下方显示倒计时完成按钮。
  - 10 秒倒计时结束后可点击“完成本次干预”。
  - 点击后先保存 `meditation_sessions`，再调用 `completeInterventionTaskItem(recordId, source_ref_id)`。
- 自由练习不显示任务条，只保留原“记录本次冥想完成”。

#### 知识 tab
- 从任务进入具体文章/视频时自动打开详情。
- 详情底部显示任务完成条：
  - 文章：10 秒后可点击完成。
  - 视频：本期仍使用 10 秒，后续可按播放进度。
- 完成后回写任务。

#### 游戏 tab
- 如果是任务进入，游戏卡片下方显示 10 秒倒计时完成按钮。
- 外链打开后不可靠，前期以“已进入游戏页面并完成 10 秒体验”作为记录。

### 8.4 心情日记完成联动

文件：
- `frontend/src/pages/user/RecordPage.vue`
- `frontend/src/pages/user/HealingPage.vue`

逻辑：
- 从任务进入：
  - query 带 `interventionRecordId`。
  - 保存当天日记成功后调用完成接口。
- 从自由入口进入：
  - 保存日记后，前端可调用 `completeTodayMoodInterventionIfAny()` 查询并自动完成当天心情任务。
  - 防止用户不知道“写完日记已完成任务”。
- 心情任务不显示倒计时。

### 8.5 脑机干预用户端

新增页面建议：
- `frontend/src/pages/user/BrainInterventionPage.vue`
- 路由：
  - `/brain-intervention`
  - `/brain-intervention/:mode`

菜单：
- 光调控
- 磁调控
- 脑机接口调控

页面逻辑：
- 卡片式选择三类调控。
- 从任务进入时进入指定 mode。
- 显示说明、注意事项、模拟干预计时器。
- 10 秒后“记录完成”按钮可用。
- 明确标注“当前为模拟记录，真实设备接入未上线”。

### 8.6 导航调整

- 患者端主菜单保持“疗愈”，但“我的-疗愈计划”要接真实干预计划。
- 可考虑在疗愈页顶部增加“我的疗愈计划”入口。
- 任务中心继续作为主菜单，与疗愈同级。
- 脑机干预暂不放主菜单，先从任务中心/疗愈计划跳转；后续上线设备后再考虑主菜单入口。

## 9. 前端医生端规划

### 9.1 新增发布干预任务页面

新增文件：`frontend/src/pages/doctor/InterventionTaskPublishingPage.vue`

新增路由：`/doctor/intervention-task-publishing`

新增医生菜单项：
- 标签：发布干预任务
- 图标：`HeartPulse` 或 `Send`
- 位置：紧跟“发布测评任务”之后。

页面结构：
- Tab 1：手动发布
- Tab 2：默认方案
- Tab 3：进度追踪

#### 手动发布

字段：
- 任务标题。
- 任务说明。
- 开始日期。
- 持续天数。
- 每日需完成次数。
- 选择患者。
- 选择小项目。

选择小项目规则：
- 冥想：必须指定具体音频，可多选。
- 心情：只能选择一次，系统提示“每天最多完成 1 次”。
- 游戏：作为大类选择。
- 知识：可选具体文章/视频，也可选择大类“知识卡片任选 1 个”。
- 脑机干预：可选光调控、磁调控、脑机接口调控。

#### 默认方案

- 展示低/中/高风险三套方案。
- 每套方案可编辑：
  - 标题
  - 周期
  - 每日目标
  - 项目列表
  - 启用/停用
- 保存后更新模板表，不影响已发布任务。

#### 进度追踪

- 列表展示：
  - 任务名称
  - 风险分层
  - 对象数
  - 进行中人数
  - 已结束人数
  - 平均完成率
- 详情展示：
  - 患者列表
  - 今日完成情况
  - 日历明细
  - 结束提醒状态

### 9.2 用户管理联动

文件：`frontend/src/pages/doctor/PatientsPage.vue`

新增：
- 患者详情增加 tab：`干预计划`。
- 展示该患者当前/历史干预任务：
  - 当前状态
  - 完成率
  - 最近 7 天日历
  - 每日小结
- 如果有最新初筛报告但没有对应默认干预任务，显示按钮：
  - “按初筛结果生成干预计划”
- 如果干预已结束，显示医生提醒：
  - “干预已结束，建议复查或重新发布计划”。

### 9.3 预警消息联动

文件：`frontend/src/pages/doctor/AlertsPage.vue`

新增过滤或兼容：
- `data_source = intervention_task`
- 展示类型：
  - 干预任务结束提醒
  - 高风险干预未完成提醒

## 10. 后端服务设计细节

### 10.1 `InterventionTaskService`

核心方法：
- `materials(authUser)`
- `listTemplates(authUser)`
- `updateTemplate(templateId, payload, authUser)`
- `listTasks(authUser)`
- `createTask(payload, authUser)`
- `updateTask(batchId, payload, authUser)`
- `publishTask(batchId, authUser)`
- `stopTask(batchId, authUser)`
- `myTasks(authUser)`
- `myToday(authUser)`
- `myPlan(authUser)`
- `startItem(recordId, authUser)`
- `completeItem(recordId, payload, authUser)`
- `calendar(authUser, start, end)`
- `calendarDate(authUser, date)`
- `assignDefaultByAssessment(assessmentId, authUser)`

### 10.2 今日待办生成

`myToday()` 执行时：
1. 查询当前用户所有 `active/in_progress` 干预 assignee。
2. 对每个 assignee 判断 `today` 是否在 `start_date/end_date` 内。
3. 根据 item 的 `frequency_type` 判断今天是否应该出现。
4. 如果不存在当天 `intervention_item_records`，则创建。
5. 合并去重并返回。

### 10.3 完成后刷新计划状态

`completeItem()` 后：
1. 更新 item_record。
2. 生成或更新当天 `intervention_daily_summaries`。
3. 统计 assignee 完成天数和完成次数。
4. 如果达到结束条件，更新 assignee 为 `completed`。
5. 如果所有 assignee 结束，更新 batch 为 `completed`。
6. 如果任务结束，创建医生提醒。

### 10.4 与初筛报告自动联动

在 `AssessmentPublishTaskService.buildAndSyncPackageReport()` 成功生成 `assessment_package_report` 后：
- 注入或调用 `InterventionTaskService.assignDefaultByAssessment(assessmentId, userId)`。
- 必须捕获异常，不能因为干预任务生成失败导致测评报告失败。
- 生成逻辑要防重：
  - `source_assessment_id` 唯一约束可选：同一报告同一用户只生成一次。

### 10.5 通用数据 API 与权限补丁

虽然干预任务建议走专用接口，但当前项目很多页面仍通过 `frontend/src/db/api.ts` 的通用 `selectRows/insertRow/updateRow` 访问基础表。落地时需要同步：

- `TableRegistry.java`
  - 注册 `intervention_materials`、`intervention_plan_templates`、`intervention_plan_template_items`、`intervention_publish_batches`、`intervention_publish_items`、`intervention_publish_assignees`、`intervention_item_records`、`intervention_daily_summaries`。
  - JSON 字段包含 `tags`、`config_json`、`recipient_scope`、`summary_json`、`details_json`。
- `GenericDataService.applyReadScope`
  - `intervention_materials`：患者只能读 active 素材，医生可读全部。
  - `intervention_publish_assignees`、`intervention_item_records`、`intervention_daily_summaries`：患者只能读自己的 `user_id`。
  - `intervention_plan_templates`、`intervention_plan_template_items`、`intervention_publish_batches`、`intervention_publish_items`：患者不直接读，必须走专用接口。
- `GenericDataService.applyWriteScope`
  - 患者不能直接写发布表、模板表和素材表。
  - 患者完成任务只允许走 `/api/intervention-tasks/items/{recordId}/complete`，由 service 校验并写记录。
- `GenericDataService.prepareWritablePayload`
  - 医生创建模板/任务时补 `created_by`。
  - 患者相关记录由专用 service 写入，不从通用 API 暴露写入口。

## 11. 前端 API 与类型

### 11.1 `frontend/src/types/index.ts`

新增类型：
- `InterventionMaterial`
- `InterventionPlanTemplate`
- `InterventionPlanTemplateItem`
- `InterventionPublishBatch`
- `InterventionPublishItem`
- `InterventionPublishAssignee`
- `InterventionItemRecord`
- `InterventionDailySummary`
- `InterventionTodayTask`

### 11.2 `frontend/src/db/api.ts`

新增方法：
- `getInterventionMaterials`
- `getInterventionTemplates`
- `updateInterventionTemplate`
- `getInterventionTasks`
- `createInterventionTask`
- `updateInterventionTask`
- `publishInterventionTask`
- `stopInterventionTask`
- `getMyInterventionTasks`
- `getMyInterventionTodayTasks`
- `getMyInterventionPlan`
- `startInterventionItem`
- `completeInterventionItem`
- `getMyInterventionCalendar`
- `getMyInterventionCalendarDate`
- `assignDefaultInterventionByAssessment`

## 12. 页面跳转协议

所有干预任务入口统一携带：

```text
interventionRecordId=<intervention_item_records.id>
interventionAssigneeId=<intervention_publish_assignees.id>
returnTo=/assessment-tasks
```

不同模块附加参数：

```text
冥想：/healing?tab=meditation&materialId=xxx&track=xxx
知识：/healing?tab=knowledge&materialId=xxx
游戏：/healing?tab=game&interventionRecordId=xxx
心情：/record?interventionRecordId=xxx
脑机：/brain-intervention/light?interventionRecordId=xxx
```

完成后默认返回：
- 若有 `returnTo`，回到 `returnTo`。
- 否则留在当前功能页，并展示“今日已完成”。

## 13. 测试计划

### 13.1 后端单元/集成测试

- 创建干预任务草稿。
- 发布给单个用户。
- 查询今日待办并懒生成记录。
- 完成倒计时任务。
- 完成心情日记任务。
- 多任务并存时子项目去重。
- 达到持续天数后任务结束。
- 初筛报告自动生成低/中/高风险默认干预任务。
- 医生端只允许医生/admin 管理，患者只能访问自己的任务。

### 13.2 前端测试

- 任务中心能展示测评任务 + 今日干预。
- 今日干预子项目能正确跳转。
- 冥想任务倒计时结束前按钮禁用，结束后可完成。
- 心情日记保存后自动完成任务。
- 知识文章/视频任务能完成并回写。
- 脑机模拟页能完成并回写。
- 疗愈计划页无任务、进行中、已完成三种状态显示正常。
- 医生端发布干预任务能完成完整流程。
- 医生端默认方案能编辑保存。

### 13.3 浏览器烟测

- PC：
  - `/doctor/intervention-task-publishing`
  - `/assessment-tasks`
  - `/profile/healing-plan`
  - `/healing?tab=meditation`
  - `/record`
  - `/brain-intervention/light`
- 移动端：
  - 任务中心子项目列表不能拥挤。
  - 倒计时完成条不遮挡内容。
  - 日历弹窗可滚动且按钮可点击。

## 14. 实施步骤

### 阶段 1：后端基础闭环

- [ ] 新增 `V15__intervention_tasks.sql`，创建干预素材、模板、发布、记录、日历小结表。
- [ ] 预置低/中/高风险默认方案和素材。
- [ ] 新增 `InterventionTaskController` 与 `InterventionTaskService`。
- [ ] 实现医生端材料、模板、发布、停止、详情接口。
- [ ] 实现患者端我的任务、今日任务、计划、日历、开始、完成接口。
- [ ] 接入初筛报告自动生成默认干预任务。
- [ ] 增加后端测试。

### 阶段 2：医生端发布干预任务

- [ ] 新增 `InterventionTaskPublishingPage.vue`。
- [ ] 医生端菜单加入“发布干预任务”。
- [ ] 实现手动发布表单。
- [ ] 实现默认方案配置。
- [ ] 实现进度追踪和结束提醒展示。
- [ ] 用户详情增加“干预计划”tab。

### 阶段 3：患者端任务中心与疗愈计划

- [ ] `AssessmentTaskCenterPage.vue` 删除静态干预任务数组，接后端今日干预。
- [ ] 任务中心合并展示多个干预任务的子项目。
- [ ] 新增干预日历小结区域。
- [ ] 重构 `HealingPlanPage.vue` 为真实疗愈计划页。
- [ ] 首页如有待完成干预，可在任务卡下方显示轻量提醒。

### 阶段 4：跨菜单完成联动

- [ ] `HealingPage.vue` 冥想任务模式：倒计时完成、保存 session、回写任务。
- [ ] `HealingPage.vue` 知识任务模式：自动打开内容、倒计时完成、回写任务。
- [ ] `HealingPage.vue` 游戏任务模式：倒计时完成、回写任务。
- [ ] `RecordPage.vue` 心情任务模式：保存日记后回写任务。
- [ ] 新增 `BrainInterventionPage.vue`，支持光调控、磁调控、脑机接口调控模拟完成。

### 阶段 5：验收与部署

- [ ] 运行后端测试。
- [ ] 运行前端单元测试。
- [ ] 本地浏览器检查医生端发布、患者端完成、任务中心同步。
- [ ] 构建前端：`VITE_APP_BASE=/chuxin-vue/ npm run build`
- [ ] 部署到 `/var/www/html/chuxin-vue/`
- [ ] 确认线上 `https://jp.jerrypsy.top/chuxin-vue/` 登录、任务中心、疗愈计划、完成回写正常。

## 15. 验收标准

- 医生可以发布一套包含冥想、心情、游戏、知识、脑机干预的干预任务。
- 医生可以编辑低/中/高风险默认方案。
- 用户完成职务犯罪初筛后，可以自动获得对应风险分层的干预任务。
- 任务中心只展示所有待完成干预子项目，不展示多张干预任务卡。
- 子项目能跳转到正确功能位置，并在真实位置完成。
- 倒计时任务 10 秒后才能完成；心情日记保存后自动完成。
- 多个干预任务并存时，今日子项目合并展示且状态同步。
- 疗愈计划页展示当前计划、完成进度、计划内容和日历小结。
- 医生端能看到干预进度和干预结束提醒。
- 所有新增页面在 PC 与移动端均不遮挡、不溢出、交互清晰。
