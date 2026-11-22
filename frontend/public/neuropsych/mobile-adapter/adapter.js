(function () {
  var presets = window.ChuxinMobilePresets || {}
  var testCode = document.documentElement.getAttribute('data-chuxin-test') || document.body.getAttribute('data-chuxin-test') || ''
  var preset = presets[testCode] || {}
  var isTouchLike = window.matchMedia && window.matchMedia('(max-width: 768px), (pointer: coarse)').matches

  function markDocument() {
    document.documentElement.classList.add('chuxin-neuropsych')
    document.body.classList.add('chuxin-neuropsych-body')
    if (testCode) {
      document.documentElement.setAttribute('data-chuxin-test', testCode)
      document.body.setAttribute('data-chuxin-test', testCode)
    }
    if (preset.layout) {
      document.documentElement.classList.add('chuxin-layout-' + preset.layout)
      document.body.classList.add('chuxin-layout-' + preset.layout)
    }
    if (isTouchLike) {
      document.documentElement.classList.add('chuxin-mobile')
      document.body.classList.add('chuxin-mobile')
    }
  }

  function visibleAndEnabled(el) {
    if (!el || el.hasAttribute('disabled')) return false
    var style = window.getComputedStyle ? window.getComputedStyle(el) : null
    return !style || (style.display !== 'none' && style.visibility !== 'hidden' && style.pointerEvents !== 'none')
  }

  function clickFirst(selectors) {
    for (var i = 0; i < selectors.length; i += 1) {
      var list = document.querySelectorAll(selectors[i])
      for (var j = 0; j < list.length; j += 1) {
        if (visibleAndEnabled(list[j])) {
          list[j].click()
          return true
        }
      }
    }
    return false
  }

  function keySpec(input) {
    if (typeof input === 'string') {
      if (input === 'Space') return { key: ' ', code: 'Space', keyCode: 32 }
      if (input === 'Enter') return { key: 'Enter', code: 'Enter', keyCode: 13 }
      if (input.length === 1) return { key: input, code: 'Key' + input.toUpperCase(), keyCode: input.toUpperCase().charCodeAt(0) }
    }
    return input || { key: 'Enter', code: 'Enter', keyCode: 13 }
  }

  function sendKey(input) {
    var spec = keySpec(input)
    var keyCode = spec.keyCode || 13
    var key = spec.key || (keyCode === 32 ? ' ' : 'Enter')
    var code = spec.code || (keyCode === 32 ? 'Space' : keyCode === 13 ? 'Enter' : '')
    ;['keydown', 'keyup'].forEach(function (type) {
      var event = new KeyboardEvent(type, { key: key, code: code, bubbles: true, cancelable: true })
      Object.defineProperty(event, 'keyCode', { get: function () { return keyCode } })
      Object.defineProperty(event, 'which', { get: function () { return keyCode } })
      Object.defineProperty(event, 'charCode', { get: function () { return keyCode } })
      document.dispatchEvent(event)
      if (document.body) document.body.dispatchEvent(event)
      window.dispatchEvent(event)
    })
    return true
  }

  function advance() {
    var selectors = preset.advanceSelectors || ['#jspsych-instructions-next:not(:disabled)', '.jspsych-btn:not(:disabled)']
    return clickFirst(selectors) || sendKey(preset.advanceKey || 'Enter')
  }

  function respond() {
    return clickFirst(preset.responseClickSelectors || []) || sendKey(preset.responseKey || 'Space')
  }

  function respondWithKey(keySpec) {
    return sendKey(keySpec)
  }

  function chooseLeft() {
    return clickFirst(preset.leftSelectors || []) || sendKey(preset.leftKey || 'q')
  }

  function chooseRight() {
    return clickFirst(preset.rightSelectors || []) || sendKey(preset.rightKey || 'p')
  }

  function clickFirstAvailableCard() {
    return clickFirst(preset.cardSelectors || ['.card_image.select-button:not(:disabled)', 'input.card_image:not(:disabled)'])
  }

  function bindOnce(el, name, handler) {
    var attr = 'data-chuxin-bound-' + name
    if (!el || el.getAttribute(attr) === '1') return
    el.setAttribute(attr, '1')
    el.addEventListener('click', handler)
    el.addEventListener('touchstart', function (event) {
      event.preventDefault()
      handler(event)
    }, { passive: false })
  }

  function syncTwoChoice() {
    var options = document.querySelectorAll('#option')
    for (var i = 0; i < options.length; i += 1) {
      options[i].classList.add('chuxin-choice-card')
      options[i].classList.add(i % 2 === 0 ? 'chuxin-choice-left' : 'chuxin-choice-right')
      bindOnce(options[i], i % 2 === 0 ? 'left' : 'right', i % 2 === 0 ? chooseLeft : chooseRight)
    }
  }

  function syncKeyboardResponse() {
    var selectors = preset.responseSelectors || ['.centerbox']
    selectors.forEach(function (selector) {
      document.querySelectorAll(selector).forEach(function (el) {
        el.classList.add('chuxin-response-target')
        bindOnce(el, 'respond', respond)
      })
    })
  }

  function syncMultiKeyResponse() {
    var responseKeys = preset.responseKeys || []
    if (responseKeys.length === 0) return syncKeyboardResponse()
    if (!isTouchLike) return
    
    var existingButtons = document.querySelector('.chuxin-multi-key-buttons')
    var activeSelectors = preset.activeSelectors || []
    var shouldShow = activeSelectors.length === 0 || activeSelectors.some(function (selector) {
      return Boolean(document.querySelector(selector))
    })
    if (existingButtons) {
      existingButtons.style.display = shouldShow ? 'flex' : 'none'
      return
    }

    var buttonContainer = document.createElement('div')
    buttonContainer.className = 'chuxin-multi-key-buttons'
    buttonContainer.style.cssText = 'position:fixed;bottom:14px;left:50%;transform:translateX(-50%);display:' + (shouldShow ? 'flex' : 'none') + ';gap:12px;z-index:1000;'
    
    responseKeys.forEach(function(keySpec) {
      var btn = document.createElement('button')
      btn.textContent = keySpec.label
      btn.className = 'chuxin-key-btn'
      btn.style.cssText = 'width:68px;height:68px;border-radius:50%;border:3px solid #334155;background:#1e293b;color:white;font-size:22px;font-weight:bold;cursor:pointer;touch-action:manipulation;'
      btn.addEventListener('click', function() {
        respondWithKey(keySpec)
      })
      btn.addEventListener('touchstart', function(event) {
        event.preventDefault()
        respondWithKey(keySpec)
      }, { passive: false })
      buttonContainer.appendChild(btn)
    })
    
    document.body.appendChild(buttonContainer)
  }

  function syncCardGrid() {
    document.querySelectorAll('.card_image').forEach(function (el) {
      el.classList.add('chuxin-card-target')
    })
    document.querySelectorAll('.CCT-btn').forEach(function (el) {
      el.classList.add('chuxin-cct-button')
    })
  }

  function syncInstructionLayoutFixes() {
    if (isTouchLike) return
    document.querySelectorAll('.cct-box2').forEach(function (el) {
      el.classList.toggle('chuxin-cct-instruction-example', Boolean(el.querySelector('.jspsych-instructions-nav')))
    })
  }

  function syncDom() {
    markDocument()
    document.querySelectorAll('.centerbox').forEach(function (el) {
      var isTextScreen = el.querySelector('.block-text, .center-block-text, .block-text2')
      var isStimScreen = el.querySelector('#stim1, #stim2, .fixation')
      if (isTextScreen && !isStimScreen) {
        el.classList.add('chuxin-text-screen')
      }
    })
    if (preset.layout === 'two-choice') syncTwoChoice()
    if (preset.responseKeys && preset.responseKeys.length > 0) {
      syncMultiKeyResponse()
    } else if (preset.layout === 'keyboard-response') {
      syncKeyboardResponse()
    }
    if (preset.layout === 'card-grid') syncCardGrid()
    syncInstructionLayoutFixes()
  }

  markDocument()
  document.addEventListener('DOMContentLoaded', syncDom)
  window.setInterval(syncDom, 350)

  window.ChuxinMobileAdapter = {
    testCode: testCode,
    preset: preset,
    isMobile: isTouchLike,
    advance: advance,
    sendKey: sendKey,
    respond: respond,
    respondWithKey: respondWithKey,
    chooseLeft: chooseLeft,
    chooseRight: chooseRight,
    clickFirst: clickFirst,
    clickFirstAvailableCard: clickFirstAvailableCard,
    noCard: function () { return clickFirst(preset.noCardSelectors || ['#NoCardButton:not(:disabled)']) },
    stopTurn: function () { return clickFirst(preset.stopSelectors || ['#turnButton:not(:disabled)']) },
    nextRound: function () { return clickFirst(preset.nextRoundSelectors || ['#collectButton:not(:disabled)', '#instructButton:not(:disabled)']) },
    sync: syncDom,
  }
})()
