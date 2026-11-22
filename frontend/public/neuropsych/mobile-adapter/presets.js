(function () {
  var stroopPreset = {
    layout: 'keyboard-response',
    responseKey: { key: 'r', code: 'KeyR', keyCode: 82 },
    advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
    advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)'],
    activeSelectors: ['.stroop-stim'],
    responseKeys: [
      { key: 'r', code: 'KeyR', keyCode: 82, label: '红' },
      { key: 'b', code: 'KeyB', keyCode: 66, label: '蓝' },
      { key: 'g', code: 'KeyG', keyCode: 71, label: '绿' },
    ],
  }

  var flankerPreset = {
    layout: 'keyboard-response',
    advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
    advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)'],
    activeSelectors: ['.flanker-text'],
    responseKeys: [
      { key: 'f', code: 'KeyF', keyCode: 70, label: 'F' },
      { key: 'h', code: 'KeyH', keyCode: 72, label: 'H' },
    ],
  }

  var emotionRegulationPreset = {
    layout: 'emotion-choice',
    advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
    advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)'],
    activeSelectors: ['.leftBox', '.rightBox'],
    responseKeys: [
      { key: 'ArrowLeft', code: 'ArrowLeft', keyCode: 37, label: '左' },
      { key: 'ArrowRight', code: 'ArrowRight', keyCode: 39, label: '右' },
    ],
  }

  var digitSpanPreset = {
    layout: 'digit-grid',
    advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
    advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)', '#SubmitButton:not(:disabled)'],
  }

  var nBackPreset = {
    layout: 'keyboard-response',
    advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
    advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)'],
    activeSelectors: ['.centerbox'],
    responseKeys: [
      { key: 'ArrowDown', code: 'ArrowDown', keyCode: 40, label: '非目标' },
      { key: 'ArrowLeft', code: 'ArrowLeft', keyCode: 37, label: '目标' },
    ],
  }

  var stopSignalPreset = {
    layout: 'keyboard-response',
    advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
    advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)'],
    activeSelectors: ['#stim1', '#stim2', '.centerbox'],
    responseKeys: [
      { key: 'ArrowLeft', code: 'ArrowLeft', keyCode: 37, label: '← 左' },
      { key: 'ArrowRight', code: 'ArrowRight', keyCode: 39, label: '右 →' },
    ],
  }

  var simonPreset = {
    layout: 'keyboard-response',
    advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
    advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)'],
    activeSelectors: ['.centerbox'],
    responseKeys: [
      { key: 'ArrowLeft', code: 'ArrowLeft', keyCode: 37, label: '← 左' },
      { key: 'ArrowRight', code: 'ArrowRight', keyCode: 39, label: '右 →' },
    ],
  }

  var antPreset = {
    layout: 'keyboard-response',
    advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
    advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)'],
    activeSelectors: ['.centerbox'],
    responseKeys: [
      { key: 'ArrowLeft', code: 'ArrowLeft', keyCode: 37, label: '← 左' },
      { key: 'ArrowRight', code: 'ArrowRight', keyCode: 39, label: '右 →' },
    ],
  }

  var axCptPreset = {
    layout: 'keyboard-response',
    advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
    advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)'],
    activeSelectors: ['.centerbox'],
    responseKeys: [
      { key: 'm', code: 'KeyM', keyCode: 77, label: 'M' },
      { key: 'z', code: 'KeyZ', keyCode: 90, label: 'Z' },
    ],
  }

  var spatialSpanPreset = {
    layout: 'digit-grid',
    advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
    advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)'],
  }

  var towerOfLondonPreset = {
    layout: 'keyboard-response',
    advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
    advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)'],
    activeSelectors: ['.tol_canvas'],
  }

  var ravensPreset = {
    layout: 'keyboard-response',
    advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
    advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)'],
  }

  var simpleReactionTimePreset = {
    layout: 'keyboard-response',
    advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
    advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)'],
    activeSelectors: ['.centerbox'],
    responseKeys: [
      { key: ' ', code: 'Space', keyCode: 32, label: '空格' },
    ],
  }

  var numberLetterPreset = {
    layout: 'keyboard-response',
    advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
    advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)'],
    activeSelectors: ['.centerbox'],
    responseKeys: [
      { key: 'q', code: 'KeyQ', keyCode: 81, label: 'Q' },
      { key: 'p', code: 'KeyP', keyCode: 80, label: 'P' },
    ],
  }

  window.ChuxinMobilePresets = {
    'go-nogo-demo': {
      layout: 'keyboard-response',
      responseKey: { key: ' ', code: 'Space', keyCode: 32 },
      advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
      advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)'],
      responseSelectors: ['#stim1', '#stim2', '.centerbox'],
    },
    'discount-titrate-demo': {
      layout: 'two-choice',
      leftKey: { key: 'q', code: 'KeyQ', keyCode: 81 },
      rightKey: { key: 'p', code: 'KeyP', keyCode: 80 },
      advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
      advanceSelectors: ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)'],
    },
    'columbia-card-task-hot-demo': {
      layout: 'card-grid',
      advanceKey: { key: 'Enter', code: 'Enter', keyCode: 13 },
      advanceSelectors: [
        '#jspsych-instructions-next:not(:disabled)',
        '#instructButton:not(:disabled)',
        '.jspsych-btn:not(:disabled)',
      ],
      cardSelectors: ['.card_image.select-button:not(:disabled)', 'input.card_image:not(:disabled)'],
      noCardSelectors: ['#NoCardButton:not(:disabled)'],
      stopSelectors: ['#turnButton:not(:disabled)'],
      nextRoundSelectors: ['#collectButton:not(:disabled)', '#instructButton:not(:disabled)'],
    },
    'stroop': stroopPreset,
    'stroop-demo': stroopPreset,
    'flanker': flankerPreset,
    'flanker-demo': flankerPreset,
    'emotion-regulation': emotionRegulationPreset,
    'emotion-regulation-demo': emotionRegulationPreset,
    'digit-span': digitSpanPreset,
    'digit-span-demo': digitSpanPreset,
    'n-back': nBackPreset,
    'n-back-demo': nBackPreset,
    'stop-signal': stopSignalPreset,
    'stop-signal-demo': stopSignalPreset,
    'simon': simonPreset,
    'simon-demo': simonPreset,
    'ant': antPreset,
    'ant-demo': antPreset,
    'ax-cpt': axCptPreset,
    'ax-cpt-demo': axCptPreset,
    'spatial-span': spatialSpanPreset,
    'spatial-span-demo': spatialSpanPreset,
    'tower-of-london': towerOfLondonPreset,
    'tower-of-london-demo': towerOfLondonPreset,
    'ravens': ravensPreset,
    'ravens-demo': ravensPreset,
    'simple-reaction-time': simpleReactionTimePreset,
    'simple-reaction-time-demo': simpleReactionTimePreset,
    'number-letter': numberLetterPreset,
    'number-letter-demo': numberLetterPreset,
  }
})()
