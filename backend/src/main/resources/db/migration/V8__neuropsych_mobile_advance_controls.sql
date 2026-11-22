UPDATE neuropsych_tests
SET config_json = JSON_SET(
  COALESCE(config_json, CAST('{}' AS JSON)),
  '$.mobileControls[0]',
  CAST('{ "id": "continue", "label": "开始/继续", "helper": "说明页", "icon": "CornerDownLeft", "type": "command", "command": "advance", "key": "Enter", "code": "Enter", "keyCode": 13, "tone": "secondary" }' AS JSON)
)
WHERE code IN ('go-nogo-demo', 'columbia-card-task-hot-demo');

UPDATE neuropsych_tests
SET config_json = JSON_SET(
  COALESCE(config_json, CAST('{}' AS JSON)),
  '$.mobileControls[0]',
  CAST('{ "id": "continue", "label": "开始/继续", "helper": "进入下一步", "icon": "CornerDownLeft", "type": "command", "command": "advance", "key": "Enter", "code": "Enter", "keyCode": 13, "tone": "secondary" }' AS JSON)
)
WHERE code = 'discount-titrate-demo';
