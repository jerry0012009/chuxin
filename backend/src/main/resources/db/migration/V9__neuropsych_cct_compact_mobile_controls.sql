UPDATE neuropsych_tests
SET config_json = JSON_SET(
  COALESCE(config_json, CAST('{}' AS JSON)),
  '$.mobileControls',
  CAST('[
    { "id": "continue", "label": "回车/继续", "helper": "说明和过渡页", "icon": "CornerDownLeft", "type": "command", "command": "advance", "key": "Enter", "code": "Enter", "keyCode": 13, "tone": "primary" }
  ]' AS JSON)
)
WHERE code = 'columbia-card-task-hot-demo';
