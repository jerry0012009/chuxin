INSERT INTO neuropsych_tests (
  id, code, title, description, dimension, clinical_meaning, estimated_minutes, source_path,
  runner_type, status, self_test_enabled, config_json, metric_schema_json, scoring_version
) VALUES
  (
    '90000000-0000-0000-0000-000000000004',
    'stroop',
    'Stroop 色词干扰任务',
    '通过颜色词汇的语义-颜色冲突评估注意控制、执行功能和认知灵活性。',
    '注意控制、执行功能、认知灵活性',
    '可辅助 ADHD、执行功能障碍、认知灵活性缺陷和冲动控制问题的评估。',
    8,
    'neuropsych/expfactory/stroop/index.html',
    'iframe',
    'active',
    TRUE,
    CAST('{"engine":"jspsych","source":"PsyTraining","outputs":["congruent_rt_mean","incongruent_rt_mean","stroop_effect","stroop_effect_ratio","congruent_accuracy","incongruent_accuracy","overall_accuracy"]}' AS JSON),
    CAST('{"primary":["congruentRtMean","incongruentRtMean","stroopEffect","stroopEffectRatio","congruentAccuracy","incongruentAccuracy","overallAccuracy"]}' AS JSON),
    1
  ),
  (
    '90000000-0000-0000-0000-000000000104',
    'stroop-demo',
    'Stroop 色词干扰任务（体验版）',
    '保留色词干扰的核心流程，减少练习和正式试次数，适合 1 分钟内联调体验。',
    '注意控制、执行功能、认知灵活性',
    '体验版用于快速熟悉流程，正式评估请使用完整版任务。',
    1,
    'neuropsych/expfactory/stroop-demo/index.html',
    'iframe',
    'active',
    TRUE,
    CAST('{"engine":"jspsych","source":"PsyTraining","mode":"demo","trials":16,"outputs":["congruent_rt_mean","incongruent_rt_mean","stroop_effect","stroop_effect_ratio","congruent_accuracy","incongruent_accuracy","overall_accuracy"]}' AS JSON),
    CAST('{"primary":["congruentRtMean","incongruentRtMean","stroopEffect","stroopEffectRatio","congruentAccuracy","incongruentAccuracy","overallAccuracy"]}' AS JSON),
    1
  )
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  description = VALUES(description),
  dimension = VALUES(dimension),
  clinical_meaning = VALUES(clinical_meaning),
  estimated_minutes = VALUES(estimated_minutes),
  source_path = VALUES(source_path),
  config_json = VALUES(config_json),
  metric_schema_json = VALUES(metric_schema_json),
  updated_at = CURRENT_TIMESTAMP(3);
