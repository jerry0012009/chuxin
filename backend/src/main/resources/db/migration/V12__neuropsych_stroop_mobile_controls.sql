UPDATE neuropsych_tests
SET config_json = JSON_SET(
  COALESCE(config_json, CAST('{}' AS JSON)),
  '$.mobileControls',
  CAST('[
    { "id": "continue", "label": "开始/继续", "helper": "说明页", "icon": "CornerDownLeft", "type": "command", "command": "advance", "key": "Enter", "code": "Enter", "keyCode": 13, "tone": "secondary" },
    { "id": "red", "label": "红", "helper": "按 R", "icon": "Zap", "type": "keypress", "key": "r", "code": "KeyR", "keyCode": 82, "tone": "danger" },
    { "id": "blue", "label": "蓝", "helper": "按 B", "icon": "Zap", "type": "keypress", "key": "b", "code": "KeyB", "keyCode": 66, "tone": "primary" },
    { "id": "green", "label": "绿", "helper": "按 G", "icon": "Zap", "type": "keypress", "key": "g", "code": "KeyG", "keyCode": 71, "tone": "success" }
  ]' AS JSON)
)
WHERE code IN ('stroop', 'stroop-demo');

UPDATE neuropsych_tests
SET config_json = JSON_SET(
  COALESCE(config_json, CAST('{}' AS JSON)),
  '$.trials',
  12
)
WHERE code = 'stroop-demo';
