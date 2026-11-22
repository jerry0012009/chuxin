# PsyTraining 神经心理实验接入流程

本次新增 `emotion-regulation`、`digit-span`、`flanker` 三个 PsyTraining 实验，每个实验均提供正式版和体验版。

## 改造步骤

1. 从 `/tmp/PsyTraining/games/{code}` 复制完整实验资源到 `frontend/public/neuropsych/expfactory/{code}`，再复制一份为 `{code}-demo`。
2. 修改每个 `index.html`：
   - 增加 `data-chuxin-test` 与移动端 viewport。
   - 引入 `../../mobile-adapter/base.css`、`presets.js`、`adapter.js`。
   - 设置 `fullscreen: false`，避免 iframe 与移动端全屏权限冲突。
   - 将原 `/save` 提交流程改为 `window.parent.postMessage({ type: 'chuxin-neuropsych-finished', testCode, rawJson, rawCsv })`。
3. 缩短体验版：
   - 情绪调节：1 个训练、1 个练习、4 个正式选择，观看时间缩短。
   - 数字广度：顺背/倒背各 3 轮，数字呈现时间缩短。
   - Flanker：4 个练习、12 个正式试次。
4. 补充移动端适配：
   - 情绪调节：左/右策略选择按钮。
   - 数字广度：保留实验内数字键盘，仅补说明/提交快捷操作，并优化数字键盘移动端布局。
   - Flanker：F/H 响应按钮，仅刺激阶段显示。
5. 后端新增迁移 `V13__neuropsych_more_psytraining_tests.sql`，写入正式版与体验版的 `neuropsych_tests` 配置、自由测评开关、指标 schema 和移动端按钮配置。
6. 后端 `NeuropsychMetricsCalculator` 增加三类计算：
   - 情绪调节：重新评价/分心选择率、高低强度重新评价率、选择反应时。
   - 数字广度：顺背最大广度、倒背最大广度、总广度、正确率。
   - Flanker：一致/不一致反应时、干扰效应、正确率。
7. 增加前后端测试，确保 demo code 复用正式计算模型、移动端配置文件已接入、fallback 操作按钮可用。

## 注意事项

- 已执行过的 Flyway 迁移不能修改；后续实验新增或配置调整应继续新增版本号迁移。
- 若 PsyTraining 原始数据不包含关键解释字段，应在实验脚本内补埋点。本次情绪调节任务已补充 `chosen_strategy`、`choice_side`、`intensity`、`stimulus_file`。
- 移动端浮动响应按钮应只在真正刺激/选择阶段显示，避免遮挡说明页和反馈页。
