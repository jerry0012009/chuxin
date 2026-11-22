INSERT INTO neuropsych_tests (
  id, code, title, description, dimension, clinical_meaning, estimated_minutes, source_path,
  runner_type, status, self_test_enabled, config_json, metric_schema_json, scoring_version
) VALUES
  (
    '90000000-0000-0000-0000-000000000101',
    'go-nogo-demo',
    'Go-NoGo 反应抑制任务（体验版）',
    '保留 Go 与 NoGo 刺激反应的完整流程，减少练习和正式试次数，适合 1 分钟内联调体验。',
    '反应抑制能力、冲动控制',
    '体验版用于快速熟悉流程，正式评估请使用完整版任务。',
    1,
    'neuropsych/expfactory/go-nogo-demo/index.html',
    'iframe',
    'active',
    TRUE,
    CAST('{"engine":"jspsych","source":"PsyTraining","mode":"demo","outputs":["go_rt_mean","go_accuracy","nogo_false_alarm_rate","d_prime","criterion_c"]}' AS JSON),
    CAST('{"primary":["goRtMean","goAccuracy","nogoFalseAlarmRate","dPrime","criterionC"]}' AS JSON),
    1
  ),
  (
    '90000000-0000-0000-0000-000000000102',
    'columbia-card-task-hot-demo',
    '哥伦比亚卡片任务（热版·体验版）',
    '保留风险决策、翻牌、停止和结算流程，将正式回合降至 5 回合，适合快速联调体验。',
    '风险决策、冲动控制、热认知',
    '体验版用于快速熟悉流程，正式评估请使用完整版任务。',
    1,
    'neuropsych/expfactory/columbia-card-task-hot-demo/index.html',
    'iframe',
    'active',
    TRUE,
    CAST('{"engine":"jspsych","source":"PsyTraining","mode":"demo","rounds":5,"outputs":["avg_cards","loss_rate","total_score","decision_rt_mean"]}' AS JSON),
    CAST('{"primary":["avgCardsPerRound","lossHitRate","totalScore","decisionRtMean","riskAdjustment"]}' AS JSON),
    1
  ),
  (
    '90000000-0000-0000-0000-000000000103',
    'discount-titrate-demo',
    '延迟折扣任务（体验版）',
    '保留即时奖励与延迟奖励选择流程，将正式选择题降至 8 题，适合 1 分钟内联调体验。',
    '延迟折扣率、自我控制、跨期选择',
    '体验版用于快速熟悉流程，正式评估请使用完整版任务。',
    1,
    'neuropsych/expfactory/discount-titrate-demo/index.html',
    'iframe',
    'active',
    TRUE,
    CAST('{"engine":"jspsych","source":"PsyTraining","mode":"demo","trials":8,"outputs":["discount_k","immediate_choice_rate","delayed_choice_rate","consistency"]}' AS JSON),
    CAST('{"primary":["discountK","immediateChoiceRate","delayedChoiceRate","consistency","decisionRtMean"]}' AS JSON),
    1
  )
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  description = VALUES(description),
  dimension = VALUES(dimension),
  clinical_meaning = VALUES(clinical_meaning),
  estimated_minutes = VALUES(estimated_minutes),
  source_path = VALUES(source_path),
  status = VALUES(status),
  self_test_enabled = VALUES(self_test_enabled),
  config_json = VALUES(config_json),
  metric_schema_json = VALUES(metric_schema_json),
  updated_at = CURRENT_TIMESTAMP(3);
