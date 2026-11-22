# 华心云量表 JSON 导入 chuxin 规划

## 1. 目标

将华心云导出的 66 个量表 JSON 导入 chuxin 的“量表测评”模块，导入后应满足：

- 医生端可查看、编辑、发布、停用导入量表。
- 患者端可完成医生分发或自由测评。
- 计分公式可正确计算题目分、维度原始分、标准分和总分。
- 结果阈值可命中结论、建议和预警等级。
- 报告结构继续复用 chuxin 现有量表报告卡片、医生端结果查询、预警同步逻辑。

导出数据位置：

- `/root/huaxinyun-surveys-export-20260530/all-surveys.json`
- `/root/huaxinyun-surveys-export-20260530/surveys/survey_*.json`

当前数据概况：

- 量表：66
- 题目：4222
- 维度：441
- 结果定义：965
- 题型：全部为 `radio`
- 预警等级：`none`、`low`、`middle`、`high`

## 2. 导入边界

### 本次导入

- 导入量表基础信息、题目、选项、维度、结果定义。
- 导入为 chuxin 原生量表数据，不在运行时依赖华心云接口。
- 支持重复导入、dry-run 校验、按量表失败隔离。
- 优先保证导入后的测评、计分、报告闭环可用。

### 暂不导入

- 华心云历史分发记录。
- 华心云历史答题结果。
- 华心云用户、租户、组织权限。
- 华心云报告 HTML 模板。

## 3. 华心云 JSON 结构

单个量表 JSON 结构基本如下：

```json
{
  "id": 187,
  "title": "90项症状清单(SCL-90)",
  "description": null,
  "type": "basic",
  "questions": [
    {
      "id": 8098,
      "text": "头痛",
      "type": "radio",
      "orderNum": 1,
      "options": [
        { "id": 33389, "text": "没有", "value": "1", "optionNo": "A" }
      ]
    }
  ],
  "dimensions": [
    {
      "id": 1,
      "num": 1,
      "dimensionName": "总分",
      "dimensionCode": "total",
      "evaluateExpression": "hx_t_1 + hx_t_2",
      "standardScoreFormula": "0",
      "results": [
        {
          "evaluateExpression": "hx_wd_y_1 >= 10",
          "conclusionAnalysis": "xxx",
          "suggestion": "xxx",
          "assessmentWarning": "high"
        }
      ]
    }
  ]
}
```

也需要兼容分页接口返回的包装结构：

```json
{
  "id": 187,
  "title": "...",
  "surveyJson": "{\"id\":187,...}"
}
```

## 4. chuxin 目标表映射

| 华心云字段 | chuxin 表字段 | 说明 |
| --- | --- | --- |
| `id` | `scale_surveys.code` | 建议生成 `huaxinyun-{id}`，用于幂等导入 |
| `title` | `scale_surveys.title` | 原样保留 |
| `description` | `scale_surveys.description` | 可追加“来源：华心云”元信息 |
| `type` | `scale_surveys.survey_type` | 原样保留，缺失时用 `basic` |
| `status` | `scale_surveys.status` | 默认导入为 `draft`，校验通过后可发布 |
| `questions[].text` | `scale_questions.stem` | 题干 |
| `questions[].type` | `scale_questions.question_type` | 当前均为 `radio` |
| `questions[].orderNum` | `scale_questions.order_no` | 公式变量 `hx_t_{order_no}` 依赖此字段 |
| `questions[].options[].optionNo` | `scale_options.option_no` | 患者答案值使用此编码 |
| `questions[].options[].text` | `scale_options.label` | 选项文本 |
| `questions[].options[].value` | `scale_options.value` | 选项分值，转 decimal |
| `dimensions[].dimensionName` | `scale_dimensions.name` | 维度名 |
| `dimensions[].dimensionCode` | `scale_dimensions.code` | 维度编码 |
| `dimensions[].num` | `scale_dimensions.num` | 维度序号 |
| `dimensions[].evaluateExpression` | `scale_dimensions.raw_score_formula` | 原始分公式 |
| `dimensions[].standardScoreFormula` | `scale_dimensions.standard_score_formula` | 标准分公式，空或 `0` 需规范化 |
| `results[].evaluateExpression` | `scale_result_definitions.condition_expression` | 阈值命中条件 |
| `results[].conclusionAnalysis` | `scale_result_definitions.conclusion` | 结论 |
| `results[].suggestion` | `scale_result_definitions.suggestion` | 建议 |
| `results[].assessmentWarning` | `scale_result_definitions.warning_level` | 预警等级 |

## 5. JSON 解析与规范化

新增后端导入服务：

- `ScaleHuaxinyunImportService`
- `ScaleHuaxinyunImportController`
- API：`POST /api/scale-assessments/import/huaxinyun`

请求能力：

- 支持上传 `all-surveys.json` 数组。
- 支持上传单个 `survey_*.json`。
- 支持上传华心云分页响应，自动解析其中的 `surveyJson`。
- 支持参数：
  - `dry_run=true|false`
  - `publish=true|false`
  - `overwrite=true|false`
  - `skip_invalid=true|false`

解析步骤：

1. 读取 JSON。
2. 判断顶层类型：
   - 数组：按量表数组处理。
   - 对象且有 `questions`：按单量表处理。
   - 对象且有 `data.list[].surveyJson`：解析分页响应。
   - 对象且有 `surveyJson`：解析单条分页记录。
3. 生成内部 DTO：
   - `HuaxinyunSurveyDto`
   - `HuaxinyunQuestionDto`
   - `HuaxinyunOptionDto`
   - `HuaxinyunDimensionDto`
   - `HuaxinyunResultDefinitionDto`
4. 做字段规范化：
   - `id` 转字符串，仅作为来源 ID。
   - 量表 `code = huaxinyun-{sourceId}`。
   - `question.type` 映射到 `radio|checkbox|text`，未知类型阻断发布。
   - `option.value` 转 `BigDecimal`，失败则阻断导入。
   - `assessmentWarning` 统一映射到 `none|low|middle|high`。
   - 空 `standardScoreFormula` 置空；值为 `"0"` 可按业务含义保留或置空，建议 dry-run 标出。

## 6. 导入校验规则

### 阻断级错误

出现以下问题时，单个量表不导入；若 `skip_invalid=false`，整批停止：

- 缺少 `title`。
- 缺少题目。
- 题目 `orderNum` 为空或重复。
- 选择题没有选项。
- 选项 `value` 不能转数字。
- `publish=true` 时没有维度。
- `publish=true` 时维度没有结果定义。
- 公式存在当前计算器不支持的语法且未完成兼容。

### 警告级问题

允许导入草稿，但 dry-run 结果要列出：

- 缺少描述。
- 量表标题重复。
- 维度 `dimensionCode` 为空。
- 结果定义缺少结论或建议。
- 标准分公式为 `"0"`。
- 量表有维度但没有用户报告展示配置。

当前已知异常：

- `survey_167.json`：有 80 道题，但没有维度，建议导入草稿，不自动发布。

## 7. 公式兼容规划

chuxin 当前已支持：

- `+ - * /`
- `> >= < <= == !=`
- `&& || !`
- 括号
- `hx_calc_equal_count`
- `hx_calc_gt_count`
- `hx_calc_ge_count`
- `hx_calc_lt_count`
- `hx_calc_le_count`
- 题目变量：`hx_t_{orderNo}`
- 维度序号变量：`hx_wd_y_{num}`、`hx_wd_b_{num}`

华心云 66 个量表额外需要支持：

### 7.1 `max(...)`

发现 6 处 `max(...)`，涉及霍兰德、危机干预、EPQ 成人/儿童等。

需要在 `ScaleExpressionEvaluator.callFunction` 中新增：

- `max(a,b,c...)`
- 建议同时新增 `min(a,b,c...)`，便于后续兼容。

### 7.2 三元表达式 `condition ? a : b`

多个复杂量表使用三元表达式，例如：

```text
hx_wd_y_a > 0 ? 1 : 0
hx_gender == 1 ? formulaA : formulaB
```

需要在公式解析器中加入三元层级：

```text
parseTernary -> parseOr -> parseAnd -> parseComparison -> ...
```

规则：

- 条件 truthy 时返回 `then` 表达式。
- 条件 falsy 时返回 `else` 表达式。
- 三元表达式需支持嵌套和括号。

### 7.3 维度编码变量

部分公式引用：

```text
hx_wd_y_s
hx_wd_y_k
hx_wd_y_d
hx_wd_y_ei
hx_wd_y_sn
```

chuxin 当前计算维度后应同时写入：

```java
variables.put("hx_wd_y_" + num, raw);
variables.put("hx_wd_b_" + num, standard);

if (code 不为空) {
  variables.put("hx_wd_y_" + code, raw);
  variables.put("hx_wd_b_" + code, standard);
}
```

### 7.4 维度计算顺序

导入后按 `dimensions[].num` 升序计算。  
如果某个维度公式引用后续维度变量，应在 dry-run 中识别为依赖顺序风险。

建议实现公式变量扫描：

- 提取 `hx_wd_y_xxx`、`hx_wd_b_xxx`。
- 判断引用的维度是否已在当前维度前计算。
- 如果不是，提示“维度依赖顺序风险”。

## 8. 计分适配

患者提交答案后，继续复用 chuxin 现有逻辑：

1. 根据题目 `id` 匹配答案。
2. 根据答案 `option_no` 找选项。
3. 读取选项 `value` 作为题目得分。
4. 写入变量：

```text
hx_t_1
hx_t_2
...
```

需要确认导入器生成的题目 ID：

- 不保留华心云旧 ID 作为主键，使用 chuxin UUID。
- 公式不依赖题目 ID，只依赖 `order_no`，所以不影响计分。
- 患者端答题使用 chuxin UUID，提交后仍可正常匹配。

## 9. 预警适配

华心云结果定义中的 `assessmentWarning` 映射到 chuxin：

| 华心云 | chuxin |
| --- | --- |
| `none` | `none` |
| `low` | `low` |
| `middle` | `middle` |
| `high` | `high` |
| 空值 | `none` |

计算时：

- 每个维度匹配所有命中的结果定义。
- 维度预警取命中结果中的最高等级。
- 量表总预警取全部维度最高等级。
- 保持现有风险预警同步逻辑，`middle/high` 继续进入预警视图。

## 10. 报告适配

继续使用 chuxin 当前 `report` JSON 结构：

```json
{
  "surveyId": "...",
  "surveyTitle": "...",
  "recordId": "...",
  "patientId": "...",
  "totalScore": 10,
  "warningLevel": "high",
  "completedAt": "...",
  "dimensions": [
    {
      "dimensionId": "...",
      "name": "总分",
      "code": "total",
      "rawScore": 10,
      "standardScore": 10,
      "warningLevel": "high",
      "conclusion": "...",
      "suggestion": "..."
    }
  ],
  "answers": []
}
```

需要注意：

- 华心云一个维度可能命中多个结果定义，chuxin 当前会用换行拼接多个结论/建议，可以继续保留。
- 对“人格类型/职业倾向”这类用数值编码表达类别的量表，报告展示应重点显示结果定义结论，而不是只显示分数。
- 医生端完整报告保留所有维度。
- 患者端结果卡片默认展示 `show_in_user_report=true` 的维度；导入数据没有该字段时默认展示。

## 11. 导入接口返回设计

dry-run 返回：

```json
{
  "total": 66,
  "valid": 65,
  "invalid": 1,
  "willCreate": 66,
  "willUpdate": 0,
  "blockingIssues": [
    {
      "sourceId": 167,
      "title": "校园生活调查表",
      "message": "publish=true 时量表缺少维度"
    }
  ],
  "warnings": [],
  "formulaFeatures": {
    "max": 6,
    "ternary": 20,
    "dimensionCodeVariables": 10
  }
}
```

实际导入返回：

```json
{
  "created": 65,
  "updated": 0,
  "skipped": 1,
  "published": 64,
  "draft": 1,
  "items": [
    {
      "sourceId": 187,
      "surveyId": "...",
      "code": "huaxinyun-187",
      "title": "90项症状清单(SCL-90)",
      "status": "published"
    }
  ]
}
```

## 12. 医生端 UI 规划

在医生端“量表测评”管理页新增“导入华心云量表”按钮：

1. 上传 JSON 文件。
2. 选择导入模式：
   - 仅校验 dry-run
   - 导入为草稿
   - 导入并发布
   - 覆盖同 code 量表
3. 显示导入预览：
   - 量表数、题目数、维度数、结果定义数。
   - 错误列表。
   - 警告列表。
   - 公式兼容检查。
4. 用户确认后正式导入。
5. 导入完成后跳转/刷新量表列表。

样式应复用现有医生端卡片、按钮、弹窗、表格风格，不单独做新视觉体系。

## 13. 实施步骤

### 第一步：公式兼容

- 扩展 `ScaleExpressionEvaluator` 支持 `max`。
- 扩展三元表达式。
- 支持维度 code 变量。
- 增加单元测试：
  - `max(1,2,3) == 3`
  - `1 > 0 ? 5 : 2 == 5`
  - 嵌套三元。
  - `hx_wd_y_s` 可参与计算。

### 第二步：导入 DTO 与解析器

- 新增 Huaxinyun DTO。
- 新增 JSON 顶层识别。
- 新增字段规范化。
- 新增 dry-run 校验。

### 第三步：导入服务

- 按量表事务导入，避免一个坏量表回滚全部。
- `code = huaxinyun-{sourceId}`。
- `overwrite=false` 时同 code 跳过。
- `overwrite=true` 时：
  - 无答题记录：替换量表子表。
  - 已有答题记录：创建新版本 code，例如 `huaxinyun-187-v2`，避免破坏历史报告。

### 第四步：发布与快照

- 导入为草稿后可手动发布。
- `publish=true` 时自动调用发布校验和生成 `survey_json` 快照。
- 无维度或公式不兼容的量表保持草稿。

### 第五步：医生端导入弹窗

- 文件上传。
- dry-run 预览。
- 正式导入。
- 结果摘要展示。

### 第六步：端到端验证

至少选择以下量表验证：

- PHQ-9：简单量表，验证基础计分和预警。
- SCL-90：多题多维，验证大体量报告。
- 霍兰德职业倾向：验证 `max`。
- MBTI 或 UPI：验证三元表达式。
- 危机干预量表：验证维度 code 变量、三元、max、预警。

每个量表验证：

- 医生端可见。
- 可发布。
- 可开启自由测评。
- 患者端可答题提交。
- 结果总分、维度分、结论建议、预警等级正常。
- 医生端结果查询能查看报告。

## 14. 验收标准

- dry-run 能识别 66 个量表并输出完整校验报告。
- 除结构缺失量表外，其余量表均可导入。
- 公式解析器支持导出数据中出现的全部公式语法。
- 至少 5 个代表性量表完成真实答题闭环。
- 患者端报告卡片能展示结论、建议和预警。
- 医生端结果查询能查看导入量表的报告。
- 导入不会影响现有 AI 评估、神经心理测评、发布测评任务逻辑。

## 15. 风险与处理

- **版权/授权风险**：导入前确认这些量表内容可在 chuxin 项目中使用。
- **公式语义风险**：复杂公式需用华心云原系统结果做抽样对照。
- **重复量表风险**：当前数据中存在同名量表，必须用来源 ID 生成唯一 code。
- **历史结果风险**：覆盖已有量表定义可能影响历史报告，已有记录时必须新建版本。
- **报告可读性风险**：职业倾向、人格类型类量表不能只显示数字，需要依赖结果定义结论展示。
