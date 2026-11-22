# 神经心理实验移动端适配套件

## 目标

移动端适配不重写实验核心逻辑，保留 jsPsych / ExpFactory 原始 trial、计时、按键、结果导出字段，只在实验页面外层增加通用适配能力。

## 文件结构

```text
frontend/public/neuropsych/mobile-adapter/
  base.css      # 通用移动端布局、按钮、说明页、选择项、卡片网格样式
  presets.js   # 按实验 code 注册移动端行为 preset
  adapter.js   # 统一桥接方法，供实验本体和 Vue iframe runner 调用
```

## 接入方式

实验 `index.html` 需要：

```html
<html data-chuxin-test="your-test-code">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="stylesheet" href="../../mobile-adapter/base.css">
<script src="../../mobile-adapter/presets.js"></script>
<script src="../../mobile-adapter/adapter.js"></script>
```

`presets.js` 中为新实验补充配置：

```js
window.ChuxinMobilePresets['your-test-code'] = {
  layout: 'two-choice',
  leftKey: { key: 'q', code: 'KeyQ', keyCode: 81 },
  rightKey: { key: 'p', code: 'KeyP', keyCode: 80 },
  advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
  advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)'],
}
```

## 当前 preset 类型

- `keyboard-response`：适合 Go-NoGo、Stroop 等单键反应任务。
- `two-choice`：适合左右选择任务，例如延迟折扣。
- `card-grid`：适合 CCT 这类卡片网格任务。

## Vue 外层调用

`NeuropsychRunner.vue` 会优先调用 iframe 内的 `window.ChuxinMobileAdapter`：

- `advance()`
- `sendKey()`
- `respond()`
- `chooseLeft()`
- `chooseRight()`
- `clickFirstAvailableCard()`

如果新实验还没有接入 adapter，外层会 fallback 到原来的 keypress / selector 点击逻辑。

## 新增实验原则

1. 常规键盘反应或二选一任务：优先只加 preset。
2. DOM 结构复杂的实验：加 preset，并在 `base.css` 中补一个新的 layout 分支。
3. 不改 trial 数组、计时、结果导出字段，避免影响指标可信度。
4. 体验版实验建议关闭 jsPsych 原生 fullscreen，避免 iframe 全屏遮挡 chuxin 外层控制台。

## 旧 jsPsych 预加载注意事项

ExpFactory 的旧 jsPsych 插件经常把 `stimulus` 注册为 `image` 预加载字段，但很多实验的 `stimulus` 实际是函数或 HTML 片段，不是图片 URL。浏览器原生 `Image.src` 通常会容忍这种输入，但某些调试脚本或浏览器插件会拦截 `Image.src` 并假设传入值是字符串，从而触发 `url.startsWith is not a function`。

新增实验时要检查对应 `js/jspsych/jspsych.js` 的 `preloadImages`：

- 只把字符串 URL 传给 `Image.src`。
- 如果 `stimulus` 是 HTML 字符串，只提取其中的 `src="..."`。
- 如果 `stimulus` 是函数、对象、空值，直接跳过。
- 不要为了预加载修改 trial、计时或结果字段。

当前三个体验版已经在各自的旧 jsPsych 副本中加入 `normalizeImagePreloadList` 防御逻辑。
