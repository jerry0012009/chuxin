UPDATE neuropsych_tests
SET config_json = CAST('{
  "engine": "jspsych",
  "source": "PsyTraining",
  "mode": "demo",
  "outputs": ["go_rt_mean", "go_accuracy", "nogo_false_alarm_rate", "d_prime", "criterion_c"],
  "mobileControls": [
    { "id": "continue", "label": "继续", "helper": "说明页", "icon": "CornerDownLeft", "type": "keypress", "key": "Enter", "code": "Enter", "keyCode": 13, "tone": "secondary" },
    { "id": "respond", "label": "反应", "helper": "Go 刺激时点击", "icon": "Zap", "type": "keypress", "key": " ", "code": "Space", "keyCode": 32, "tone": "primary" }
  ]
}' AS JSON)
WHERE code = 'go-nogo-demo';

UPDATE neuropsych_tests
SET config_json = CAST('{
  "engine": "jspsych",
  "source": "PsyTraining",
  "mode": "demo",
  "rounds": 5,
  "outputs": ["avg_cards", "loss_rate", "total_score", "decision_rt_mean"],
  "mobileControls": [
    { "id": "continue", "label": "继续", "helper": "说明页", "icon": "CornerDownLeft", "type": "keypress", "key": "Enter", "code": "Enter", "keyCode": 13, "tone": "secondary" },
    { "id": "flip-card", "label": "翻一张", "helper": "选择牌片", "icon": "Layers", "type": "command", "command": "clickFirstAvailableCard", "tone": "primary" },
    { "id": "stop-turn", "label": "停止/翻牌", "helper": "结算本轮", "icon": "TimerReset", "type": "click", "selectors": ["#turnButton:not(:disabled)"], "tone": "warning" },
    { "id": "next-round", "label": "下一步", "helper": "继续回合", "icon": "Check", "type": "click", "selectors": ["#collectButton:not(:disabled)", "#instructButton:not(:disabled)"], "tone": "success" },
    { "id": "no-card", "label": "不取牌", "helper": "跳过本轮", "icon": "Hand", "type": "click", "selectors": ["#NoCardButton:not(:disabled)"], "tone": "secondary" }
  ]
}' AS JSON)
WHERE code = 'columbia-card-task-hot-demo';

UPDATE neuropsych_tests
SET config_json = CAST('{
  "engine": "jspsych",
  "source": "PsyTraining",
  "mode": "demo",
  "trials": 8,
  "outputs": ["discount_k", "immediate_choice_rate", "delayed_choice_rate", "consistency"],
  "mobileControls": [
    { "id": "continue", "label": "继续", "helper": "进入下一步", "icon": "CornerDownLeft", "type": "keypress", "key": "Enter", "code": "Enter", "keyCode": 13, "tone": "secondary" },
    { "id": "choose-left", "label": "选左侧", "helper": "按 Q", "icon": "ArrowLeftRight", "type": "keypress", "key": "q", "code": "KeyQ", "keyCode": 81, "tone": "primary" },
    { "id": "choose-right", "label": "选右侧", "helper": "按 P", "icon": "ArrowLeftRight", "type": "keypress", "key": "p", "code": "KeyP", "keyCode": 80, "tone": "success" }
  ]
}' AS JSON)
WHERE code = 'discount-titrate-demo';
