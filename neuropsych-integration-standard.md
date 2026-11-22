# PsyTraining 游戏统一接入标准 v2.0

基于现有7个游戏（stroop/flanker/go-nogo/columbia-card-task-hot/discount-titrate/emotion-regulation/digit-span）的集成经验，提炼出的标准化接入流程。

## 一、命名规范

| 项目 | 格式 | 示例 |
|------|------|------|
| 正式版目录 | `{game-code}` | `n-back` |
| 体验版目录 | `{game-code}-demo` | `n-back-demo` |
| testCode | 与目录名一致 | `n-back` / `n-back-demo` |
| SQL 迁移文件 | `V{N}__neuropsych_{game_code}.sql` | `V15__neuropsych_n_back.sql` |

## 二、前端接入步骤

### Step 1: 复制文件
```
从 /tmp/PsyTraining/games/{source-dir}/ 复制到
frontend/public/neuropsych/expfactory/{game-code}/
```

### Step 2: 修改 index.html（6处改动）

```html
<!-- ① html标签加 data-chuxin-test -->
<!DOCTYPE html><html class='' data-chuxin-test='{game-code}'>

<!-- ② 加 viewport meta -->
<meta name='viewport' content='width=device-width, initial-scale=1, viewport-fit=cover'>

<!-- ③ 改标题为中文 -->
<title>中文任务名称</title>

<!-- ④ 引入移动端适配CSS -->
<link rel='stylesheet' type='text/css' href='../../mobile-adapter/base.css'>

<!-- ⑤ 引入移动端适配JS（在experiment.js之后） -->
<script src='../../mobile-adapter/presets.js'></script>
<script src='../../mobile-adapter/adapter.js'></script>

<!-- ⑥ jsPsych.init 配置修改 -->
jsPsych.init({
    timeline: {timeline_var_name},
    display_element: "getDisplayElement",
    fullscreen: false,                    // 必须false，iframe冲突
    on_trial_finish: function(data){
      addID('{game-code}')               // 与testCode一致
    },
    on_finish: function(){
        var rawJson = jsPsych.data.dataAsJSON();
        var rawCsv = jsPsych.data.dataAsCSV ? jsPsych.data.dataAsCSV() : '';
        window.parent.postMessage({
            type: 'chuxin-neuropsych-finished',
            testCode: '{game-code}',
            rawJson: rawJson,
            rawCsv: rawCsv
        }, window.location.origin);
    }
});
```

### Step 3: 创建体验版
- 复制正式版目录为 `{game-code}-demo`
- 修改 `data-chuxin-test='{game-code}-demo'`
- 修改 `addID('{game-code}-demo')`
- 修改 `testCode: '{game-code}-demo'`
- 修改 title 加"（体验版）"
- **缩短试次**：减少 practice/test 试次数量，缩短计时参数

### Step 4: 移动端预设（presets.js）

在 `window.ChuxinMobilePresets` 中添加：
```javascript
'{game-code}': { /* 正式版和体验版共用 */ },
'{game-code}-demo': { /* 同正式版 */ },
```

预设字段说明：
- `layout`: 布局类型（'keyboard-response' / 'two-choice' / 'digit-grid' / 'card-grid'）
- `advanceKey`: 说明页翻页键
- `advanceSelectors`: 说明页"下一步"按钮选择器
- `responseKeys`: 响应按钮数组 `[{key, code, keyCode, label}]`
- `activeSelectors`: 刺激阶段的选择器（控制按钮显示时机）

## 三、后端接入步骤

### Step 1: SQL 迁移
新增 `V{N}__neuropsych_{game_code}.sql`，插入 `neuropsych_tests` 记录：

```sql
INSERT INTO neuropsych_tests (id, code, title, description, dimension, clinical_meaning,
  estimated_minutes, source_path, runner_type, status, self_test_enabled,
  config_json, metric_schema_json, scoring_version)
VALUES (
  '{uuid}', '{game-code}', '任务标题', '任务描述', '维度1、维度2', '临床意义',
  N, 'neuropsych/expfactory/{game-code}/index.html', 'iframe', 'active', TRUE,
  CAST('{...}' AS JSON),   -- config_json: engine, source, outputs, mobileControls
  CAST('{...}' AS JSON),   -- metric_schema_json: primary metrics
  1
);
```

config_json 格式：
```json
{
  "engine": "jspsych",
  "source": "PsyTraining",
  "outputs": ["metric1", "metric2"],
  "mobileControls": [
    {"id":"continue","label":"开始/继续","helper":"说明页","icon":"CornerDownLeft","type":"command","command":"advance","key":"Enter","code":"Enter","keyCode":13,"tone":"secondary"},
    {"id":"left","label":"F","helper":"左侧","icon":"Zap","type":"keypress","key":"f","code":"KeyF","keyCode":70,"tone":"primary"}
  ]
}
```

### Step 2: 指标计算
在 `NeuropsychMetricsCalculator.java` 的 `calculate()` switch 中新增：
```java
case "{game-code}" -> calculate{GameName}(trials);
```

计算方法规范：
- 筛选有效试次：`trial_id` + `exp_stage` + `condition`
- 提取反应时：`rt > 0` 的有效值
- 计算正确率：`correct` 字段或 `key_press == correct_response`
- 分条件对比：congruent/incongruent、go/nogo 等
- 输出格式：`LinkedHashMap` 保证顺序
- 风险等级：`warning` 字段（high/middle/low/none）
- 反馈卡片：`buildResult()` 统一格式

### Step 3: 单元测试
在 `NeuropsychMetricsCalculatorTest.java` 新增测试方法：
- 构造模拟试次数据
- 调用 `calculator.calculate()`
- 断言关键指标值
- 验证 feedbackCards 格式

## 四、关键注意事项

1. **Flyway 迁移不可变** — 已执行的 SQL 不能修改，只能新增版本号
2. **fullscreen 必须 false** — iframe 内全屏会冲突
3. **demo 自动复用计算** — `testCode.endsWith("-demo")` 自动 strip，demo 不需单独写计算
4. **移动端按钮只在刺激阶段显示** — 用 `activeSelectors` 控制
5. **原始数据可能缺字段** — 如需补充埋点，修改 experiment.js
6. **timeline 变量名不统一** — 每个游戏的 timeline 变量名不同，需从 experiment.js 中提取
7. **jsPsych 插件依赖不同** — 每个游戏引用的 jsPsych 插件不同，需保留原始引用

## 五、验证清单

- [ ] 正式版页面可加载，无控制台错误
- [ ] 体验版页面可加载，试次数量正确缩短
- [ ] 完成后 postMessage 正确发送
- [ ] 后端 metrics 计算返回正确指标
- [ ] 移动端按钮在刺激阶段显示，说明页隐藏
- [ ] demo code 自动复用正式版计算逻辑
- [ ] 单元测试全部通过
