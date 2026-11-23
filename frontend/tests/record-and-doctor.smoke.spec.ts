import { expect, test } from '@playwright/test'
import { randomUUID } from 'node:crypto'

const baseUrl = 'http://127.0.0.1:5175'
const apiBaseUrl = 'http://127.0.0.1:18080'
const userUsername = 'codex_1779982823'
const doctorUsername = 'codexdoc_1779982823'
const password = 'secret123'

async function expectPath(page: { waitForFunction: Function }, pathWithSearch: string | RegExp) {
  await page.waitForFunction((expected: string | { source: string }) => {
    const actual = `${window.location.pathname}${window.location.search}`
    if (typeof expected === 'string') return actual === expected
    return new RegExp(expected.source).test(actual)
  }, typeof pathWithSearch === 'string' ? pathWithSearch : { source: pathWithSearch.source })
}

async function loginForApi(usernameOrEmail: string) {
  const response = await fetch(`${apiBaseUrl}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({ usernameOrEmail, password }),
  })
  if (!response.ok) {
    throw new Error(`login failed for ${usernameOrEmail}`)
  }
  return response.json() as Promise<{
    accessToken: string
    user: { id: string }
  }>
}

async function seedRiskAlert() {
  const [doctor, user] = await Promise.all([loginForApi(doctorUsername), loginForApi(userUsername)])
  const description = `Playwright 风险预警 ${Date.now()}`

  const response = await fetch(`${apiBaseUrl}/api/data/risk_alerts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      Authorization: `Bearer ${doctor.accessToken}`,
    },
    body: JSON.stringify({
      data: {
        patient_id: user.user.id,
        alert_type: 'playwright-smoke',
        risk_level: 9,
        description,
        data_source: 'playwright',
        source_id: randomUUID(),
        is_handled: false,
      },
      single: true,
    }),
  })

  if (!response.ok) {
    throw new Error('seed risk alert failed')
  }

  return { description }
}

test('user login can reach record page, save diary, and open profile subpage', async ({ page }) => {
  const uniqueNote = `playwright smoke ${Date.now()}`
  const recordVoiceText = `记录页语音转写 ${Date.now()}`
  const uniqueName = `Codex用户${Date.now()}`
  const uniquePositiveTag = `好事${Date.now()}`
  const uniqueNegativeTag = `压力${Date.now()}`
  const updatedNote = `${uniqueNote} 覆盖更新`
  const inlineUpdatedNote = `${uniqueNote} 正文编辑`
  let recordSpeechRequestPayload: any = null

  await page.addInitScript(() => {
    Object.defineProperty(window, 'isSecureContext', { value: true, configurable: true })
    class MockMediaRecorder extends EventTarget {
      state = 'inactive'
      ondataavailable: ((event: BlobEvent) => void) | null = null
      onstop: (() => void) | null = null
      constructor(_stream: MediaStream, _options?: MediaRecorderOptions) {
        super()
      }
      start() {
        this.state = 'recording'
        const blob = new Blob(['RIFF....WAVEfmt data'], { type: 'audio/wav' })
        setTimeout(() => this.ondataavailable?.({ data: blob } as BlobEvent), 10)
      }
      stop() {
        this.state = 'inactive'
        this.onstop?.()
      }
    }
    Object.defineProperty(window, 'MediaRecorder', { value: MockMediaRecorder, configurable: true })
    const fakeStream = {
      getTracks: () => [{ stop: () => undefined }],
    } as unknown as MediaStream
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: async () => fakeStream,
      },
      configurable: true,
    })
  })

  await page.route('**/api/functions/speech-recognition', async (route) => {
    recordSpeechRequestPayload = route.request().postDataJSON()
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: { text: recordVoiceText },
        error: null,
      }),
    })
  })

  await page.goto(`${baseUrl}/login`)
  await page.getByTestId('role-user').click()
  await page.getByTestId('mode-login').click()
  await page.getByTestId('username-input').fill(userUsername)
  await page.getByTestId('password-input').fill(password)
  await page.locator('form').getByRole('button', { name: '登录' }).click()

  await expectPath(page, '/')
  await page.goto(`${baseUrl}/record`)
  await expect(page.getByText('继续按 xinyu-care 的记录页收敛')).toHaveCount(0)
  await expect(page.getByText('尽量对齐 xinyu-care 当前记录方式')).toHaveCount(0)
  await expect(page.getByText('对齐 xinyu-care 的周复盘入口')).toHaveCount(0)
  await expect(page.getByText('已接真实后端')).toHaveCount(0)
  await page.getByTestId('record-content-input').fill(uniqueNote)
  await expect(page.getByTestId('record-voice-trigger')).toBeVisible()
  await page.getByTestId('record-voice-trigger').click()
  await expect(page.getByTestId('record-content-input')).toHaveValue(new RegExp(recordVoiceText))
  expect(recordSpeechRequestPayload?.input_audio?.data).toBeTruthy()
  expect(recordSpeechRequestPayload?.input_audio?.format).toBe('wav')
  await page.getByTestId('record-voice-trigger').click()
  await page.getByTestId('record-positive-trigger-input').fill(uniquePositiveTag)
  await page.getByTestId('record-positive-trigger-input').press('Enter')
  await page.getByTestId('record-negative-trigger-input').fill(uniqueNegativeTag)
  await page.getByTestId('record-negative-trigger-input').press('Enter')
  await page.getByTestId('mood-option-good').click()
  await page.getByTestId('save-emotion-record').click()

  await expect(page.getByText('记录已保存').or(page.getByText('记录已更新'))).toBeVisible()
  await expect(page.getByTestId('mood-feedback-close')).toBeVisible({ timeout: 4000 })
  await page.getByTestId('mood-feedback-close').click()
  const todayKey = new Date().toISOString().slice(0, 10)
  await page.getByTestId(`record-calendar-day-${todayKey}`).click()
  await expect(page.getByTestId('record-day-dialog')).toBeVisible()
  await expect(page.getByTestId('record-day-dialog').locator('textarea')).toHaveValue(new RegExp(uniqueNote))
  await expect(page.getByTestId('record-day-dialog')).toContainText(uniquePositiveTag)
  await expect(page.getByTestId('record-day-dialog')).toContainText(uniqueNegativeTag)
  await page.getByTestId('record-day-dialog').getByRole('button', { name: '关闭' }).click()
  await page.getByTestId('record-content-input').fill(updatedNote)
  await page.getByTestId('save-emotion-record').click()
  await expect(page.getByText('记录已更新')).toBeVisible()
  await expect(page.getByTestId('mood-feedback-close')).toBeVisible({ timeout: 4000 })
  await page.getByTestId('mood-feedback-close').click()
  await page.getByTestId(`record-calendar-day-${todayKey}`).click()
  await expect(page.getByTestId('record-day-dialog').locator('textarea')).toHaveValue(new RegExp(updatedNote))
  await page.getByTestId('record-day-dialog').locator('textarea').fill(inlineUpdatedNote)
  await page.getByTestId('record-day-dialog').getByRole('button', { name: '完成' }).click()
  await expect(page.getByText('已更新')).toBeVisible()
  await expect(page.getByTestId('record-day-dialog')).toContainText(inlineUpdatedNote)

  await page.goto(`${baseUrl}/profile`)
  await expect(page.getByRole('heading', { name: '查看健康报告' })).toBeVisible()
  await expect(page.getByTestId('profile-health-report-card')).toContainText('多模态评估结果与康复建议')
  await expect(page.getByRole('button', { name: /^查看报告$/ })).toHaveCount(0)
  await expect(page.getByText('账号信息')).toBeHidden()
  await expect(page.getByText('功能入口')).toBeHidden()
  await expect(page.getByText('真实后端写入统计')).toBeHidden()
  await expect(page.getByText('管理员后台登录')).toBeVisible()
  await page.getByTestId('profile-edit-trigger').click()
  await expect(page.getByTestId('profile-edit-dialog')).toBeVisible()
  await expect(page.getByTestId('profile-edit-dialog')).toContainText('编辑个人资料')
  await page.getByRole('button', { name: '头像设置' }).click()
  await expect(page.getByTestId('profile-edit-dialog')).toContainText('选择预设头像')
  await page.getByRole('button', { name: '背景主题' }).click()
  await expect(page.getByTestId('profile-edit-dialog')).toContainText('选择预设主题')
  await page.getByRole('button', { name: '基本信息' }).click()
  await page.getByTestId('profile-full-name-input').fill(uniqueName)
  await expect(page.getByTestId('profile-save-button')).toContainText('保存更改')
  await page.getByTestId('profile-save-button').click()
  await expect(page.getByText('保存成功')).toBeVisible()
  await expect(page.getByTestId('profile-edit-dialog')).toBeHidden()

  await page.goto(`${baseUrl}/profile/personal`)
  await expect(page.getByRole('heading', { name: '基本信息管理' })).toBeVisible()
  await page.getByTestId('personal-full-name').fill(uniqueName)
  await page.getByLabel('女').check()
  await page.getByTestId('personal-age').selectOption('29')
  await page.getByTestId('personal-height').fill('168')
  await page.getByTestId('personal-weight').fill('56')
  await page.getByTestId('personal-phone').fill(`139${Date.now().toString().slice(-8)}`)
  await page.getByTestId('personal-wechat').fill(`wx_${Date.now()}`)
  await page.getByTestId('personal-email').fill(`codex-${Date.now()}@example.com`)
  await page.getByTestId('personal-save').click()
  await expect(page.getByText('个人资料已自动保存')).toBeVisible()

  await page.goto(`${baseUrl}/profile/privacy`)
  await expect(page.getByRole('heading', { name: '隐私与安全' })).toBeVisible()
  await page.getByTestId('privacy-two-factor').click()
  await expect(page.getByText('设置已更新')).toBeVisible()
  await page.getByTestId('privacy-data-sharing').click()
  await expect(page.getByTestId('privacy-data-sharing')).toHaveAttribute('aria-checked', 'true')
  await page.getByTestId('privacy-locationAccess').click()
  await expect(page.getByTestId('privacy-locationAccess')).toHaveAttribute('aria-checked', 'true')

  await page.goto(`${baseUrl}/profile/healing-plan`)
  await expect(page.getByRole('heading', { name: '干预计划' })).toBeVisible()
  await page.getByTestId('healing-plan-summary').click()
  await expect(page.getByTestId('healing-plan-detail-dialog')).toBeVisible()
  await expect(page.getByTestId('healing-plan-detail-dialog').getByRole('heading', { name: '21天情绪重塑计划' })).toBeVisible()
  await page.getByTestId('healing-plan-detail-close').click()
  await page.getByTestId('healing-plan-complete-3').click()
  await expect(page.getByText('任务已完成！太棒了')).toBeVisible()
  await page.getByTestId('healing-plan-task').filter({ hasText: '睡前助眠引导' }).click()
  await expect(page.getByTestId('healing-plan-task-dialog')).toBeVisible()
  await expect(page.getByText('放松身心，通过阿尔法波引导进入深度睡眠。')).toBeVisible()
  await page.getByText('返回').click()
  await page.getByTestId('healing-plan-tab-roadmap').click()
  await page.getByTestId('healing-plan-milestone').filter({ hasText: '初步评估' }).click()
  await expect(page.getByTestId('healing-plan-milestone-dialog')).toBeVisible()
  await page.getByRole('button', { name: '关闭' }).click()
  await page.getByTestId('healing-plan-milestone').filter({ hasText: '情绪稳定' }).click()
  await expect(page.getByText('该阶段尚未解锁，请继续努力！')).toBeVisible()

  await page.goto(`${baseUrl}/profile/about`)
  await expect(page.getByRole('heading', { name: '关于我们' })).toBeVisible()
  await expect(page.getByTestId('about-hero')).toContainText('初心')
  await expect(page.getByTestId('about-hero')).toContainText('数字化心理健康服务')
  await expect(page.getByTestId('about-feature-card')).toHaveCount(4)
  await expect(page.getByTestId('about-certifications')).toContainText('三甲医院管理员团队支持')

  await page.goto(`${baseUrl}/profile/connect-doctor`)
  await expect(page.getByRole('heading', { name: '对接管理员' })).toBeVisible()
  await page.getByText('在线咨询', { exact: true }).click()
  await expect(page.getByText('已切换至: 在线咨询')).toBeVisible()
  await expect(page.getByTestId('connect-doctor-card')).toHaveCount(3)
  await expect(page.getByText('王管理员')).toBeVisible()
  await page.getByText('隐私严格加密').click()
  await expect(page.getByText(/初心保障：隐私严格加密/)).toBeVisible()
  await page.getByText('查看全部').click()
  await expect(page.getByText('已为您显示全部可用专家列表')).toBeVisible()
  await page.getByTestId('connect-doctor-search').fill('陈管理员')
  await expect(page.getByTestId('connect-doctor-card').first()).toContainText('陈管理员')
  await page.getByTestId('connect-doctor-text').first().click()
  await expect(page.getByText('正在为您连接 陈管理员 的图文咨询窗口...')).toBeVisible()
  await expectPath(page, '/assessment')
  await page.goto(`${baseUrl}/profile/connect-doctor`)
  await page.getByTestId('connect-doctor-search').fill('王管理员')
  await expect(page.getByTestId('connect-doctor-card').first()).toContainText('王管理员')
  await page.getByTestId('connect-doctor-video').first().click()
  await expect(page.getByText('王管理员 目前不在线，请稍后再试或通过预约系统预约。')).toBeVisible()

  await page.goto(`${baseUrl}/profile/subscription`, { waitUntil: 'domcontentloaded' })
  await expect(page.getByRole('heading', { name: '会员中心' })).toBeVisible()
  await expect(page.getByText('普通会员')).toBeVisible()
  await expect(page.getByText('最受欢迎')).toBeVisible()
  await page.getByText('终身会员').click()
  await expect(page.getByText('终身解锁所有功能')).toBeVisible()
  await page.getByTestId('subscription-submit').click()
  await expect(page.getByText('正在调起支付模块...')).toBeVisible()
  await expect(page.getByText('支付环境安全，请在弹出的窗口中完成支付')).toBeVisible()
})

test('user home page matches key entry flows and routes into healing and assessment', async ({ page }) => {
  await page.goto(`${baseUrl}/login`)
  await page.getByTestId('role-user').click()
  await page.getByTestId('mode-login').click()
  await page.getByTestId('username-input').fill(userUsername)
  await page.getByTestId('password-input').fill(password)
  await page.locator('form').getByRole('button', { name: '登录' }).click()

  await expectPath(page, '/')
  await page.goto(`${baseUrl}/`)

  await expect(page.getByRole('heading', { name: '我的工作台' })).toBeVisible()
  await expect(page.getByRole('heading', { name: '当前测评' })).toBeVisible()
  await expect(page.getByRole('heading', { name: '今日干预' })).toBeVisible()
  await expect(page.getByRole('heading', { name: '测评记录' })).toBeVisible()
  await expect(page.getByTestId('home-game-card')).toBeVisible()

  await page.getByTestId('home-feature-assessment').click()
  await expectPath(page, '/assessment')

  await page.goto(`${baseUrl}/`)
  await page.getByTestId('home-feature-record').click()
  await expectPath(page, '/record')
  await expect(page.getByRole('heading', { name: '情绪记录' })).toBeVisible()

  await page.goto(`${baseUrl}/`)
  await page.getByTestId('home-game-card').click()
  await expectPath(page, '/healing')
  await expect(page.getByRole('heading', { name: '神庙逃亡 2' })).toBeVisible()
  await expect(page.getByTestId('healing-start-game')).toContainText('开始游戏')

  await page.goto(`${baseUrl}/`)
  await page.getByTestId('home-feature-healing').click()
  await expectPath(page, '/healing')
  await expect(page.getByRole('heading', { name: '冥想库' })).toBeVisible()
  await expect(page.getByRole('heading', { name: '焦虑缓解呼吸法' })).toBeVisible()

  await page.getByRole('button', { name: '睡眠', exact: true }).click()
  await expect(page.getByRole('button', { name: /睡眠/ })).toHaveClass(/text-white/)
  await expect(page.getByRole('button').filter({ hasText: '睡前放松引导' }).filter({ hasText: 'sleep · 15分钟' })).toBeVisible()
})

test('user can scan and connect smart band with xinyu-care mock-first behavior', async ({ page }) => {
  await page.goto(`${baseUrl}/login`)
  await page.getByTestId('role-user').click()
  await page.getByTestId('mode-login').click()
  await page.getByTestId('username-input').fill(userUsername)
  await page.getByTestId('password-input').fill(password)
  await page.locator('form').getByRole('button', { name: '登录' }).click()

  await expectPath(page, '/')
  await page.goto(`${baseUrl}/profile/smart-band`)
  await expect(page.getByRole('heading', { name: '手环数据' })).toBeVisible()
  await expect(page.getByTestId('smartband-health-score')).toBeVisible()

  await page.getByTestId('smartband-connection-card').click()
  await expect(page.getByTestId('smartband-dialog')).toBeVisible()
  await page.getByTestId('smartband-scan').click()
  await expect(page.getByTestId('smartband-device').filter({ hasText: '华为手环 10' })).toBeVisible()
  await page.getByTestId('smartband-device').filter({ hasText: '华为手环 10' }).click()
  await expect(page.getByTestId('smartband-connected-panel')).toContainText('华为手环 10')
  await expect(page.getByText('设备已连接，正在同步数据')).toBeVisible()
  await page.getByRole('button').filter({ has: page.locator('svg') }).last().click()
  await expect(page.getByTestId('smartband-realtime-preview')).toBeVisible()

  await page.getByTestId('smartband-tab-charts').click()
  await expect(page.getByTestId('smartband-charts')).toContainText('心率趋势')
  await expect(page.getByTestId('smartband-charts')).toContainText('睡眠阶段分布')
  await page.getByTestId('smartband-tab-ai').click()
  await expect(page.getByTestId('smartband-ai')).toContainText('AI 心理健康评估')
  await expect(page.getByTestId('smartband-ai')).toContainText('健康洞察与建议')
})

test('scale dialogue advances one local standard question per user answer', async ({ page }) => {
  let chatCompletionCalls = 0
  await page.route('**/api/functions/chat-completion', async (route) => {
    chatCompletionCalls += 1
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          choices: [{
            message: {
              content: '这是不应出现在中间轮次的额外 AI 问题。第99题：你是否还想回答另一个问题？',
            },
          }],
        },
        error: null,
      }),
    })
  })

  await page.goto(`${baseUrl}/login`)
  await page.getByTestId('role-user').click()
  await page.getByTestId('mode-login').click()
  await page.getByTestId('username-input').fill(userUsername)
  await page.getByTestId('password-input').fill(password)
  await page.locator('form').getByRole('button', { name: '登录' }).click()
  await expectPath(page, '/')

  await page.goto(`${baseUrl}/assessment`)
  await page.getByTestId('start-scale-assessment').click()
  await expect(page.getByTestId('scale-dialogue')).toContainText('第1题')
  await page.getByTestId('scale-dialogue-input').fill('有时候')
  await page.getByTestId('scale-dialogue-send').click()
  await expect(page.getByTestId('scale-dialogue')).toContainText('下面继续第2题')
  await expect(page.getByTestId('scale-dialogue')).not.toContainText('第99题')
  expect(chatCompletionCalls).toBe(0)
})

test('user login can complete assessment flow and generate fusion report', async ({ page }) => {
  test.setTimeout(60_000)

  let fusionAlertDescription = ''
  let speechRequestPayload: any = null
  let scaleSpeechRequestPayload: any = null
  let visionRequestPayload: any = null

  await page.addInitScript(() => {
    Object.defineProperty(window, 'isSecureContext', { value: true, configurable: true })
    HTMLMediaElement.prototype.play = async function play() {
      return Promise.resolve()
    }
    Object.defineProperty(HTMLVideoElement.prototype, 'videoWidth', { get: () => 640 })
    Object.defineProperty(HTMLVideoElement.prototype, 'videoHeight', { get: () => 480 })
    HTMLCanvasElement.prototype.toDataURL = function toDataURL() {
      return `data:image/jpeg;base64,${'A'.repeat(1600)}`
    }
    class MockMediaRecorder extends EventTarget {
      state = 'inactive'
      ondataavailable: ((event: BlobEvent) => void) | null = null
      onstop: (() => void) | null = null
      constructor(_stream: MediaStream, _options?: MediaRecorderOptions) {
        super()
      }
      start() {
        this.state = 'recording'
        const blob = new Blob(['RIFF....WAVEfmt data'], { type: 'audio/wav' })
        setTimeout(() => this.ondataavailable?.({ data: blob } as BlobEvent), 10)
      }
      stop() {
        this.state = 'inactive'
        this.onstop?.()
      }
    }
    Object.defineProperty(window, 'MediaRecorder', { value: MockMediaRecorder, configurable: true })
    const fakeStream = {
      getTracks: () => [{ stop: () => undefined }],
    } as unknown as MediaStream
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: async () => fakeStream,
      },
      configurable: true,
    })
  })

  await page.goto(`${baseUrl}/login`)
  await page.getByTestId('role-user').click()
  await page.getByTestId('mode-login').click()
  await page.getByTestId('username-input').fill(userUsername)
  await page.getByTestId('password-input').fill(password)
  await page.locator('form').getByRole('button', { name: '登录' }).click()

  await expectPath(page, /^\/(?:profile)?$/)
  await page.goto(`${baseUrl}/assessment`)
  await expect(page.getByText('当前列表来自真实后端')).toHaveCount(0)
  await expect(page.getByText('assessment 写入结果')).toHaveCount(0)

  let speechRequestCount = 0
  await page.route('**/api/functions/speech-recognition', async (route) => {
    speechRequestCount += 1
    speechRequestPayload = route.request().postDataJSON()
    if (speechRequestCount === 1) {
      scaleSpeechRequestPayload = speechRequestPayload
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          text: speechRequestCount === 1
            ? '量表语音输入转写：最近两周睡眠很浅，经常觉得疲惫。'
            : '最近持续疲惫、睡眠很浅，压力和焦虑反复出现，也常常感到低落，需要尽快得到支持。',
        },
        error: null,
      }),
    })
  })
  let scaleReplyIndex = 1
  await page.route('**/api/functions/chat-completion', async (route) => {
    const payload = route.request().postDataJSON()
    const systemPrompt = String(payload?.messages?.[0]?.content || '')
    let content = '我理解你的感受。第2题：最近两周，你是否感到情绪低落、沮丧或绝望？'
    if (systemPrompt.includes('语音情绪评估助手')) {
      content = JSON.stringify({
        emotion_vector: { calm: 0.08, happy: 0.03, sad: 0.5, angry: 0.04, surprised: 0.02, fearful: 0.18, disgusted: 0.03, neutral: 0.12 },
        confidence: 0.88,
        indicators: { isLowSpeed: true, isHighPitchDrop: true, isLongPause: true },
        depression_analysis: '语音表现出持续疲惫、语速偏低和停顿增加，建议继续完成表情识别并关注近期压力来源。',
      })
    } else if (systemPrompt.includes('刚完成一轮主动式量表对话')) {
      content = '评估已完成，分数为 24 分，风险等级为高风险。建议继续完成语音情绪识别和表情识别，以形成完整多模态报告。'
    } else {
      scaleReplyIndex += 1
      content = `我理解你的回答。第${scaleReplyIndex}题：最近两周，你是否经常觉得疲惫或没有精力？`
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          choices: [{ message: { content } }],
        },
        error: null,
      }),
    })
  })
  await page.route('**/api/functions/multimodal-fusion', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          choices: [{
            message: {
              content: JSON.stringify({
                fused_score: 78,
                risk_level: 7,
                detailed_report: '多模态融合显示量表、语音和表情均提示近期情绪压力较高，需要持续关注。',
                recommendations: ['保持规律睡眠', '联系专业人员进一步评估'],
              }),
            },
          }],
        },
        error: null,
      }),
    })
  })
  await page.route('**/api/functions/multimodal-analysis', async (route) => {
    visionRequestPayload = route.request().postDataJSON()
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          choices: [{
            message: {
              content: JSON.stringify({
                emotion_radar: { neutral: 0.25, happy: 0.04, sad: 0.42, angry: 0.04, surprised: 0.03, fearful: 0.12, disgusted: 0.03, contempt: 0.02, pain: 0.05 },
                depression_risk_score: 76,
                analysis_report: 'Qwen3.5-397B-A17B视觉理解模型分析：面部微表情检测到悲伤情绪主导，建议关注情绪状态并适当调节。',
                micro_features: {
                  brow_furrow: '眉心频繁皱缩，显示持续的心理压力',
                  mouth_droop: '嘴角自然状态下垂，缺乏愉悦微表情',
                  eye_contact: '眼神游离，眨眼频率迟滞',
                },
              }),
            },
          }],
        },
        error: null,
      }),
    })
  })

  await page.getByTestId('scale-history-trigger').click()
  await expect(page.getByTestId('scale-history-dialog')).toContainText('历史评估记录')
  await expect(page.getByTestId('scale-history-item')).toHaveCount(5)
  await expect(page.getByTestId('scale-history-dialog')).toContainText('SDS-20')
  await expect(page.getByTestId('scale-history-dialog')).toContainText('HAMD-17 + SDS-20')
  await page.getByTestId('scale-history-item').filter({ hasText: 'PHQ-9 + HAMD-17' }).click()
  await expect(page.getByTestId('scale-history-detail-dialog')).toContainText('评估记录')
  await expect(page.getByTestId('scale-history-detail-dialog')).toContainText('睡眠确实不太好')
  await page.getByTestId('scale-history-view-report').click()
  await expect(page.getByTestId('scale-history-report-dialog')).toContainText('量表评估报告')
  await expect(page.getByTestId('scale-history-report-dialog')).toContainText('各维度得分详情')
  await expect(page.getByTestId('scale-history-report-dialog')).toContainText('AI 专业建议')
  await page.getByTestId('scale-history-report-close').click()
  await expect(page.getByTestId('scale-history-report-dialog')).toBeHidden()
  await page.getByTestId('scale-history-detail-dialog').getByRole('button').last().click()
  await page.getByTestId('scale-history-close').click()
  await expect(page.getByTestId('scale-history-dialog')).toBeHidden()

  await page.getByTestId('start-scale-assessment').click()
  await expect(page.getByTestId('scale-dialogue')).toContainText('你好，我是初心心理助手')
  await expect(page.getByTestId('scale-dialogue')).toContainText('第1题')
  await page.getByTestId('scale-voice-input').click()
  await page.getByTestId('scale-voice-input').click()
  await expect(page.getByTestId('scale-dialogue-input')).toHaveValue(/量表语音输入转写/)
  expect(scaleSpeechRequestPayload?.input_audio?.data).toBeTruthy()
  expect(scaleSpeechRequestPayload?.input_audio?.format).toBe('wav')
  await page.getByTestId('scale-dialogue-send').click()
  for (let index = 0; index < 8; index += 1) {
    await expect(page.getByTestId('assessment-answer-strong')).toBeEnabled()
    await page.getByTestId('assessment-answer-strong').click()
  }
  await expect(page.getByTestId('scale-report')).toContainText('量表评估报告')
  await page.getByTestId('scale-report-next').click()
  await expect(page.getByTestId('voice-status-panel')).toContainText('正在录音')
  await expect(page.getByTestId('voice-recording-progress')).toContainText('录音进度')
  await expect(page.getByTestId('complete-voice')).toHaveCount(0)
  await page.getByTestId('assessment-voice-record').click()
  await expect(page.getByTestId('voice-status-panel')).toContainText('准备就绪')
  await page.getByTestId('assessment-voice-upload').setInputFiles('/root/jry/chuxin/frontend/tests/fixtures/silence.wav')
  expect(speechRequestPayload?.input_audio?.data).toBeTruthy()
  expect(speechRequestPayload?.input_audio?.format).toBe('wav')
  await expect(page.getByTestId('voice-report-dialog')).toBeVisible()
  await expect(page.getByTestId('voice-report-dialog').getByText('语音识别完成')).toBeVisible()
  await expect(page.getByTestId('voice-report-dialog')).toContainText('最近持续疲惫')
  await expect(page.getByTestId('voice-report-export-pdf')).toBeVisible()
  await expect(page.getByTestId('voice-report-export-png')).toBeVisible()
  await expect(page.getByTestId('voice-radar-chart').locator('svg[aria-label="8维情绪雷达图"]')).toBeVisible()
  await expect(page.getByTestId('voice-radar-chart').locator('polygon')).toHaveCount(4)
  await page.getByTestId('voice-report-next').click()
  await page.getByTestId('complete-expression').click()
  await expect(page.getByTestId('expression-live-panel')).toContainText('LIVE FEED')
  await expect(page.getByTestId('expression-live-panel')).toContainText('MODEL: Qwen3.5-397B-A17B')
  await expect(page.getByTestId('expression-live-panel')).toContainText('FACE:')
  await expect(page.getByTestId('expression-live-panel')).toContainText('MICRO')
  await expect(page.getByTestId('expression-live-panel')).toBeVisible()
  await page.getByTestId('complete-expression').click()
  await expect(page.getByTestId('expression-report-dialog')).toBeVisible()
  expect(JSON.stringify(visionRequestPayload)).toContain('image_url')
  expect(JSON.stringify(visionRequestPayload)).toContain('emotion_radar')
  await expect(page.getByTestId('expression-report-dialog').getByRole('heading', { name: '表情识别完成' })).toBeVisible()
  await expect(page.getByTestId('expression-report-card')).toContainText('微表情表征图')
  await expect(page.getByTestId('expression-report-card')).toContainText('9维情绪雷达')
  await expect(page.getByTestId('expression-report-card')).toContainText('AI 综合分析')
  await expect(page.getByTestId('expression-radar-chart').locator('svg[aria-label="9维情绪雷达图"]')).toBeVisible()
  await expect(page.getByTestId('expression-radar-chart').locator('polygon')).toHaveCount(4)
  await page.getByTestId('expression-report-complete').click()

  await expect(page.getByRole('heading', { name: '多模态报告', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '关闭报告' })).toBeVisible()
  await expect(page.getByText('返回评估')).toHaveCount(0)
  await expect(page.getByTestId('fusion-score')).toBeVisible()
  await expect(page.getByTestId('fusion-professional-advice')).toContainText('智能诊断结论')
  await expect(page.getByText('量表评估 (50%)')).toBeVisible()
  await expect(page.getByText('语音情绪 (20%)')).toBeVisible()
  await expect(page.getByText('表情识别 (30%)')).toBeVisible()
  const assessmentHistoryResponse = page.waitForResponse((response) =>
    response.url().includes('/api/data/assessments') && response.request().method() === 'GET' && response.status() === 200,
  )
  await page.getByTestId('fusion-history-trigger').click()
  await assessmentHistoryResponse
  await expect(page.getByTestId('fusion-history-dialog')).toBeVisible()
  await expect(page.getByTestId('fusion-history-dialog')).toContainText('历史记录')
  const historyScoreText = await page.getByTestId('fusion-history-item').first().locator('span').last().textContent()
  await page.getByTestId('fusion-history-item').first().click()
  await expect(page.getByTestId('fusion-history-dialog')).toBeHidden()
  await expect(page.getByTestId('fusion-score')).toContainText((historyScoreText || '').trim())
  await page.getByTestId('fusion-history-trigger').click()
  await expect(page.getByTestId('fusion-history-dialog')).toBeVisible()
  await page.getByTestId('fusion-history-close').click()
  await page.getByTestId('fusion-open-scale').click()
  await expect(page.getByTestId('fusion-scale-report-detail')).toContainText('各维度得分详情')
  await page.getByTestId('fusion-subreport-dialog').getByRole('button').first().click()
  await page.getByTestId('fusion-open-voice').click()
  await expect(page.getByTestId('fusion-voice-report-detail')).toContainText('声学特征指标')
  await page.getByTestId('fusion-subreport-dialog').getByRole('button').first().click()
  await page.getByTestId('fusion-open-expression').click()
  await expect(page.getByTestId('fusion-expression-report-detail')).toContainText('面部表情分布')
  await page.getByTestId('fusion-subreport-dialog').getByRole('button').first().click()
  const fusionScore = Number(await page.getByTestId('fusion-score').textContent())
  if (!Number.isFinite(fusionScore)) throw new Error('fusion score not found')
  const expectedRiskLevel = Math.min(10, Math.max(1, Math.ceil(fusionScore / 10)))
  fusionAlertDescription = `融合风险分值 ${fusionScore}/100`
  await page.getByTestId('fusion-close').click()
  await expectPath(page, '/profile')
  const profileAssessmentsResponse = page.waitForResponse((response) =>
    response.url().includes('/api/data/assessments') && response.request().method() === 'GET' && response.status() === 200,
  )
  await page.goto(`${baseUrl}/profile?openReport=1`)
  await profileAssessmentsResponse
  await expect(page.getByTestId('profile-fusion-report')).toBeVisible()
  await expect(page.getByRole('heading', { name: '多模态报告', exact: true })).toBeVisible()
  await expect(page.getByTestId('profile-fusion-score')).toContainText(String(fusionScore))
  await expect(page.getByText('xinyu-care 默认示例')).toBeHidden()
  await expect(page.getByText('暂无后端历史报告')).toBeHidden()
  await expect(page.getByTestId('profile-fusion-professional-advice')).toContainText('智能诊断结论')
  await expect(page.getByText('量表评估 (50%)')).toBeVisible()
  await expect(page.getByText('语音情绪 (20%)')).toBeVisible()
  await expect(page.getByText('表情识别 (30%)')).toBeVisible()
  await expect(page.getByTestId('profile-fusion-close')).toBeVisible()
  await expect(page.getByTestId('profile-fusion-export-pdf')).toBeVisible()
  await expect(page.getByTestId('profile-fusion-export-png')).toHaveCount(0)
  const profileHistoryResponse = page.waitForResponse((response) =>
    response.url().includes('/api/data/assessments') && response.request().method() === 'GET' && response.status() === 200,
  )
  await page.getByTestId('profile-fusion-history').click()
  await profileHistoryResponse
  await expect(page.getByTestId('profile-fusion-history-dialog')).toBeVisible()
  await expect(page.getByTestId('profile-fusion-history-dialog')).toContainText('历史记录')
  await page.getByTestId('profile-fusion-history-item').first().click()
  await expect(page.getByTestId('profile-fusion-history-dialog')).toBeHidden()
  await expect(page.getByTestId('profile-fusion-report')).toBeVisible()
  await page.getByTestId('profile-fusion-open-scale').click()
  await expect(page.getByTestId('profile-fusion-scale-detail')).toContainText('PHQ-9 总分')
  await page.getByTestId('profile-fusion-subreport-dialog').getByRole('button').first().click()
  await page.getByTestId('profile-fusion-open-voice').click()
  await expect(page.getByTestId('profile-fusion-voice-detail')).toContainText('/ 100')
  await page.getByTestId('profile-fusion-subreport-dialog').getByRole('button').first().click()
  await page.getByTestId('profile-fusion-open-expression').click()
  await expect(page.getByTestId('profile-fusion-expression-detail')).toContainText('Qwen3.5-397B-A17B')
  await page.getByTestId('profile-fusion-subreport-dialog').getByRole('button').first().click()
  await page.getByTestId('profile-fusion-close').click()
  await expectPath(page, '/profile')

  await page.evaluate(() => window.localStorage.removeItem('chuxin.access-token'))
  await page.goto(`${baseUrl}/login`)
  await page.getByTestId('role-doctor').click()
  await page.getByTestId('username-input').fill(doctorUsername)
  await page.getByTestId('password-input').fill(password)
  await page.locator('form').getByRole('button', { name: '登录' }).click()
  await expectPath(page, '/admin/dashboard')
  await page.goto(`${baseUrl}/admin/alerts`)
  await expect(page.getByText('多模态融合评估').first()).toBeVisible()
  await expect(page.getByText(`风险等级 ${expectedRiskLevel}/10`).first()).toBeVisible()
  await expect(page.getByText(fusionAlertDescription).first()).toBeVisible()
})

test('assessment scale step can resume unfinished local session', async ({ page }) => {
  await page.goto(`${baseUrl}/login`)
  await page.getByTestId('role-user').click()
  await page.getByTestId('mode-login').click()
  await page.getByTestId('username-input').fill(userUsername)
  await page.getByTestId('password-input').fill(password)
  await page.locator('form').getByRole('button', { name: '登录' }).click()

  await expectPath(page, '/')
  await page.goto(`${baseUrl}/assessment`)
  await page.evaluate((username) => {
    window.localStorage.removeItem('chuxin.scale-assessment.session')
    for (let index = window.localStorage.length - 1; index >= 0; index -= 1) {
      const key = window.localStorage.key(index)
      if (key?.startsWith('mindcare_assessment_session_')) {
        window.localStorage.removeItem(key)
      }
    }
    window.localStorage.setItem('mindcare_assessment_session_v1_other-user', JSON.stringify({
      version: 'v1',
      userId: 'other-user',
      selectedScales: ['PHQ-9'],
      questionIndex: 1,
      totalQuestions: 9,
      questionBank: [],
      updatedAt: new Date().toISOString(),
      completed: false,
      messages: [{ role: 'assistant', content: `其他用户会话 ${username}`, timestamp: new Date().toISOString() }],
    }))
  }, userUsername)
  await page.reload()
  await expect(page.getByTestId('scale-resume-banner')).toBeHidden()
  await page.getByTestId('start-scale-assessment').click()
  await expect(page.getByTestId('scale-dialogue')).toContainText('第1题')
  await page.getByTestId('scale-emoji-trigger').click()
  await expect(page.getByTestId('scale-emoji-panel')).toBeVisible()
  await page.getByTestId('scale-emoji-panel').getByRole('button', { name: '😊' }).click()
  await expect(page.getByTestId('scale-dialogue-input')).toHaveValue('😊')
  await page.getByTestId('scale-dialogue-input').fill('最近几天睡眠很浅，白天很疲惫')
  await page.getByTestId('scale-dialogue-send').click()
  await expect(page.getByTestId('scale-dialogue')).toContainText('最近几天睡眠很浅')
  await expect(page.getByTestId('scale-dialogue')).toContainText('第2题')
  const sessionKeys = await page.evaluate(() =>
    Object.keys(window.localStorage).filter((key) => key.startsWith('mindcare_assessment_session_v1_')),
  )
  expect(sessionKeys.length).toBeGreaterThan(0)
  expect(sessionKeys.some((key) => !key.endsWith('_other-user'))).toBe(true)

  await page.reload()
  await expect(page.getByTestId('scale-resume-banner')).toContainText('发现未完成的评估')
  await page.getByTestId('scale-resume-continue').click()
  await expect(page.getByTestId('scale-dialogue')).toContainText('最近几天睡眠很浅')
  await expect(page.getByTestId('scale-dialogue')).toContainText('第2题')
  await page.reload()
  await expect(page.getByTestId('scale-resume-banner')).toBeVisible()
  await page.getByTestId('scale-resume-dismiss').click()
  await expect(page.getByTestId('scale-resume-banner')).toBeHidden()
})

test('mobile assessment uses xinyu-care step-by-step layout', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto(`${baseUrl}/login`)
  await page.getByTestId('role-user').click()
  await page.getByTestId('mode-login').click()
  await page.getByTestId('username-input').fill(userUsername)
  await page.getByTestId('password-input').fill(password)
  await page.locator('form').getByRole('button', { name: '登录' }).click()

  await expectPath(page, '/')
  await page.goto(`${baseUrl}/assessment`)
  await expect(page.getByTestId('assessment-step-navigation')).toBeVisible()
  await expect(page.getByRole('button', { name: '开始实时录音' })).toBeHidden()
  await expect(page.getByTestId('expression-start-panel')).toBeHidden()
  await page.getByTestId('assessment-step-voice').click()
  await expect(page.getByRole('button', { name: '开始实时录音' })).toBeVisible()
  await expect(page.getByTestId('start-scale-assessment')).toBeHidden()
  await page.getByTestId('assessment-step-expression').click()
  await expect(page.getByTestId('expression-start-panel')).toBeVisible()
  await expect(page.getByRole('button', { name: '开始实时录音' })).toBeHidden()
})

test('assessment expression analysis does not fake completion when AI service fails', async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, 'isSecureContext', { value: true, configurable: true })
    HTMLMediaElement.prototype.play = async function play() {
      return Promise.resolve()
    }
    Object.defineProperty(HTMLVideoElement.prototype, 'videoWidth', { get: () => 640 })
    Object.defineProperty(HTMLVideoElement.prototype, 'videoHeight', { get: () => 480 })
    HTMLCanvasElement.prototype.toDataURL = function toDataURL() {
      return `data:image/jpeg;base64,${'A'.repeat(1600)}`
    }
    const fakeStream = {
      getTracks: () => [{ stop: () => undefined }],
    } as unknown as MediaStream
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: async () => fakeStream,
      },
      configurable: true,
    })
  })

  await page.route('**/api/functions/multimodal-analysis', async (route) => {
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ data: null, error: 'OPENROUTER_API_KEY 未配置' }),
    })
  })

  await page.goto(`${baseUrl}/login`)
  await page.getByTestId('role-user').click()
  await page.getByTestId('mode-login').click()
  await page.getByTestId('username-input').fill(userUsername)
  await page.getByTestId('password-input').fill(password)
  await page.locator('form').getByRole('button', { name: '登录' }).click()

  await expectPath(page, '/')
  await page.goto(`${baseUrl}/assessment`)
  await page.getByText('表情识别', { exact: true }).click()
  await page.getByTestId('complete-expression').click()
  await expect(page.getByTestId('expression-live-panel')).toContainText('LIVE FEED')
  await page.getByTestId('complete-expression').click()
  await expect(page.getByText(/面部识别失败/)).toBeVisible()
  await expect(page.getByTestId('expression-report-dialog')).toHaveCount(0)
  await expect(page.getByTestId('generate-fusion-report')).toBeDisabled()
})

test('assessment expression analysis rejects incomplete AI report JSON', async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, 'isSecureContext', { value: true, configurable: true })
    HTMLMediaElement.prototype.play = async function play() {
      return Promise.resolve()
    }
    Object.defineProperty(HTMLVideoElement.prototype, 'videoWidth', { get: () => 640 })
    Object.defineProperty(HTMLVideoElement.prototype, 'videoHeight', { get: () => 480 })
    HTMLCanvasElement.prototype.toDataURL = function toDataURL() {
      return `data:image/jpeg;base64,${'A'.repeat(1600)}`
    }
    const fakeStream = {
      getTracks: () => [{ stop: () => undefined }],
    } as unknown as MediaStream
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: async () => fakeStream,
      },
      configurable: true,
    })
  })

  await page.route('**/api/functions/multimodal-analysis', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          choices: [{
            message: {
              content: JSON.stringify({
                emotion_radar: { neutral: 0.5, sad: 0.3 },
                depression_risk_score: 70,
              }),
            },
          }],
        },
        error: null,
      }),
    })
  })

  await page.goto(`${baseUrl}/login`)
  await page.getByTestId('role-user').click()
  await page.getByTestId('mode-login').click()
  await page.getByTestId('username-input').fill(userUsername)
  await page.getByTestId('password-input').fill(password)
  await page.locator('form').getByRole('button', { name: '登录' }).click()

  await expectPath(page, '/')
  await page.goto(`${baseUrl}/assessment`)
  await page.getByText('表情识别', { exact: true }).click()
  await page.getByTestId('complete-expression').click()
  await expect(page.getByTestId('expression-live-panel')).toContainText('LIVE FEED')
  await page.getByTestId('complete-expression').click()
  await expect(page.getByText(/面部识别失败/)).toBeVisible()
  await expect(page.getByTestId('expression-report-dialog')).toHaveCount(0)
  await expect(page.getByTestId('generate-fusion-report')).toBeDisabled()
})

test('assessment voice analysis does not fake completion when speech recognition fails', async ({ page }) => {
  await page.route('**/api/functions/speech-recognition', async (route) => {
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ data: null, error: '语音识别服务暂时不可用，请稍后重试。' }),
    })
  })

  await page.goto(`${baseUrl}/login`)
  await page.getByTestId('role-user').click()
  await page.getByTestId('mode-login').click()
  await page.getByTestId('username-input').fill(userUsername)
  await page.getByTestId('password-input').fill(password)
  await page.locator('form').getByRole('button', { name: '登录' }).click()

  await expectPath(page, '/')
  await page.goto(`${baseUrl}/assessment`)
  await page.getByTestId('assessment-voice-upload').setInputFiles('/root/jry/chuxin/frontend/tests/fixtures/silence.wav')
  await expect(page.getByText(/语音识别失败/)).toBeVisible()
  await expect(page.getByTestId('voice-report-dialog')).toHaveCount(0)
  await expect(page.getByTestId('complete-voice')).toHaveCount(0)
  await expect(page.getByTestId('generate-fusion-report')).toBeDisabled()
})

test('user login can open healing tabs and save one meditation session record', async ({ page }) => {
  const healingDiaryVoiceText = `疗愈日记语音转写 ${Date.now()}`
  const healingDiaryManualText = `疗愈日记正文 ${Date.now()}`
  let healingDiarySpeechRequestPayload: any = null
  let htpMultimodalRequestPayload: any = null

  await page.addInitScript(() => {
    Object.defineProperty(window, 'isSecureContext', { value: true, configurable: true })
    class MockMediaRecorder extends EventTarget {
      state = 'inactive'
      ondataavailable: ((event: BlobEvent) => void) | null = null
      onstop: (() => void) | null = null
      constructor(_stream: MediaStream, _options?: MediaRecorderOptions) {
        super()
      }
      start() {
        this.state = 'recording'
        const blob = new Blob(['RIFF....WAVEfmt data'], { type: 'audio/wav' })
        setTimeout(() => this.ondataavailable?.({ data: blob } as BlobEvent), 10)
      }
      stop() {
        this.state = 'inactive'
        this.onstop?.()
      }
    }
    Object.defineProperty(window, 'MediaRecorder', { value: MockMediaRecorder, configurable: true })
    const fakeStream = {
      getTracks: () => [{ stop: () => undefined }],
    } as unknown as MediaStream
    Object.defineProperty(navigator, 'mediaDevices', {
      value: {
        getUserMedia: async () => fakeStream,
      },
      configurable: true,
    })
  })

  await page.route('**/api/functions/speech-recognition', async (route) => {
    healingDiarySpeechRequestPayload = route.request().postDataJSON()
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: { text: healingDiaryVoiceText },
        error: null,
      }),
    })
  })

  await page.route('**/api/functions/multimodal-analysis', async (route) => {
    htpMultimodalRequestPayload = route.request().postDataJSON()
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          choices: [{
            message: {
              content: JSON.stringify({
                summary: '画面包含房屋、树木与人物结构，整体线条稳定，空间布局清晰。结果仅供自我探索参考，不作为医疗诊断依据。',
                dimensions: [
                  { name: '内在动力', score: 82, label: '稳定', description: '线条连续，行动能量较稳定。' },
                  { name: '自我防御', score: 78, label: '稳固', description: '结构边界清晰，有自我保护感。' },
                  { name: '生长潜能', score: 85, label: '活跃', description: '画面延展性较好，成长意愿明显。' },
                  { name: '思维秩序', score: 80, label: '严谨', description: '空间布局清楚，表达有条理。' },
                ],
              }),
            },
          }],
        },
        error: null,
      }),
    })
  })

  await page.goto(`${baseUrl}/login`)
  await page.getByTestId('role-user').click()
  await page.getByTestId('mode-login').click()
  await page.getByTestId('username-input').fill(userUsername)
  await page.getByTestId('password-input').fill(password)
  await page.locator('form').getByRole('button', { name: '登录' }).click()

  await expectPath(page, '/')
  await page.goto(`${baseUrl}/healing`)

  await expect(page.getByRole('heading', { name: '冥想库' })).toBeVisible()
  await expect(page.getByText('探索内心的宁静')).toBeVisible()
  await expect(page.getByText('按 xinyu-care 当前生效结构收口')).toHaveCount(0)
  await expect(page.getByText('保留分类切换')).toHaveCount(0)
  await page.waitForFunction(() => {
    const audio = document.querySelector('audio') as HTMLAudioElement | null
    return Boolean(audio?.src && audio.src.includes('/srcs/music/'))
  })
  await page.evaluate(() => {
    const audio = document.querySelector('audio') as HTMLAudioElement | null
    if (!audio) throw new Error('healing audio element missing')
    Object.defineProperty(audio, 'duration', { configurable: true, get: () => 180 })
    audio.currentTime = 42
    audio.dispatchEvent(new Event('loadedmetadata'))
    audio.dispatchEvent(new Event('timeupdate'))
  })
  await expect(page.getByTestId('healing-progress-slider')).toHaveValue('23')
  await page.getByTestId('healing-loop-mode').click()
  await page.getByTestId('healing-volume-slider').fill('0.5')
  await expect(page.getByTestId('healing-progress-slider')).toHaveValue('23')
  await page.getByTestId('healing-save-session').click()
  await expect(page.getByTestId('healing-mood-dialog')).toBeVisible()
  await page.getByTestId('healing-mood-focused').click()
  await page.getByTestId('healing-session-notes').fill(`冥想回归 ${Date.now()}`)
  await page.getByTestId('healing-confirm-session').click()
  await expect(page.getByText('冥想记录已保存')).toBeVisible()
  await page.getByTestId('healing-tab-diary').click()
  await expect(page.getByTestId('healing-diary-panel')).toBeVisible()
  await expect(page.getByRole('heading', { name: '情绪日历' })).toBeVisible()
  await expect(page.getByTestId('healing-diary-calendar')).toBeVisible()
  await page.getByTestId('healing-diary-content').fill(healingDiaryManualText)
  await page.getByTestId('healing-diary-voice-trigger').click()
  await page.getByTestId('healing-diary-voice-trigger').click()
  await expect(page.getByTestId('healing-diary-content')).toHaveValue(new RegExp(healingDiaryVoiceText))
  expect(healingDiarySpeechRequestPayload?.input_audio?.data).toBeTruthy()
  expect(healingDiarySpeechRequestPayload?.input_audio?.format).toBe('wav')
  await page.getByTestId('healing-diary-positive-input').fill(`疗愈好事${Date.now()}`)
  await page.getByTestId('healing-diary-positive-add').click()
  await page.getByTestId('healing-diary-mood-good').click()
  await page.getByTestId('healing-diary-save').click()
  await expect(page.getByText('日记已保存').or(page.getByText('日记已更新'))).toBeVisible()
  await page.getByTestId('healing-tab-game').click()
  await expect(page.getByRole('heading', { name: '神庙逃亡 2' })).toBeVisible()
  await expect(page.getByTestId('healing-start-game')).toContainText('开始游戏')
  await expect(page.getByText('手势或方向键控制')).toBeVisible()
  await page.goto(`${baseUrl}/assessment/htp`)
  await expect(page.getByRole('heading', { name: '房树人心理测评' })).toBeVisible()
  await page.getByTestId('htp-palette-trigger').click()
  await expect(page.getByTestId('htp-palette-modal')).toBeVisible()
  await expect(page.getByTestId('htp-palette-modal')).toContainText('Brush & Palette')
  await page.getByTestId('htp-palette-modal').getByRole('button', { name: '关闭调色板' }).click()
  await expect(page.getByTestId('htp-palette-modal')).toHaveCount(0)
  const canvas = page.getByTestId('htp-canvas')
  const box = await canvas.boundingBox()
  if (!box) throw new Error('HTP canvas not visible')
  const drawStroke = async (fromX: number, fromY: number, toX: number, toY: number) => {
    await page.mouse.move(box.x + fromX, box.y + fromY)
    await page.mouse.down()
    await page.mouse.move(box.x + toX, box.y + toY, { steps: 6 })
    await page.mouse.up()
  }
  await drawStroke(80, 80, 180, 170)
  await drawStroke(240, 90, 320, 190)
  await drawStroke(120, 240, 360, 260)
  await page.getByTestId('htp-analyze').click()
  await expect(page.getByTestId('htp-report')).toBeVisible()
  expect(htpMultimodalRequestPayload?.messages?.[0]?.content?.[1]?.image_url?.url).toMatch(/^data:image\/png;base64,/)
  const assessmentCountBeforeHtpSave = await page.evaluate(async ({ apiBaseUrl, userUsername, password }) => {
    const login = await fetch(`${apiBaseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ usernameOrEmail: userUsername, password }),
    }).then((response) => response.json())
    const filters = encodeURIComponent(JSON.stringify([{ op: 'eq', field: 'user_id', value: login.user.id }]))
    const rows = await fetch(`${apiBaseUrl}/api/data/assessments?select=*&filters=${filters}`, {
      headers: { Accept: 'application/json', Authorization: `Bearer ${login.accessToken}` },
    }).then((response) => response.json())
    return Array.isArray(rows.data) ? rows.data.length : 0
  }, { apiBaseUrl, userUsername, password })
  await page.getByTestId('htp-save').click()
  await expect(page.getByText('测评结果已保存至历史记录')).toBeVisible()
  await expect(page.getByTestId('htp-history-list')).toBeVisible()
  await expect(page.getByTestId('htp-history-list')).toContainText('内在动力')
  await expect(page.getByTestId('htp-history-list')).toContainText('自我防御')
  await expect(page.getByTestId('htp-history-list')).toContainText('生长潜能')
  await expect(page.getByTestId('htp-history-list')).toContainText('思维秩序')
  const assessmentCountAfterHtpSave = await page.evaluate(async ({ apiBaseUrl, userUsername, password }) => {
    const login = await fetch(`${apiBaseUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ usernameOrEmail: userUsername, password }),
    }).then((response) => response.json())
    const filters = encodeURIComponent(JSON.stringify([{ op: 'eq', field: 'user_id', value: login.user.id }]))
    const rows = await fetch(`${apiBaseUrl}/api/data/assessments?select=*&filters=${filters}`, {
      headers: { Accept: 'application/json', Authorization: `Bearer ${login.accessToken}` },
    }).then((response) => response.json())
    return Array.isArray(rows.data) ? rows.data.length : 0
  }, { apiBaseUrl, userUsername, password })
  expect(assessmentCountAfterHtpSave).toBe(assessmentCountBeforeHtpSave)
  await page.goto(`${baseUrl}/healing`)
  await page.getByTestId('healing-tab-knowledge').click()
  await expect(page.getByTestId('healing-knowledge-search')).toBeVisible()
  await expect(page.getByTestId('healing-knowledge-type-article')).toBeVisible()
  await expect(page.getByTestId('healing-knowledge-sort-trending')).toBeVisible()
  await expect(page.getByRole('heading', { name: '疗愈树洞' })).toHaveCount(0)
  await page.getByTestId('healing-knowledge-type-video').click()
  await expect(page.getByTestId('healing-knowledge-item').first()).toContainText('视频')
  await page.waitForFunction(() => {
    const cover = document.querySelector('[data-testid="healing-knowledge-video-cover"]') as HTMLImageElement | null
    return Boolean(cover?.src && (cover.src.startsWith('data:image/') || cover.src.includes('/srcs/')))
  })
  await page.getByTestId('healing-knowledge-item').first().click()
  await expect(page.getByTestId('healing-knowledge-detail')).toBeVisible()
  await page.waitForFunction(() => {
    const video = document.querySelector('video') as HTMLVideoElement | null
    return Boolean(video?.src && video.src.includes('/srcs/video/'))
  })
  await page.waitForFunction(() => {
    const video = document.querySelector('video') as HTMLVideoElement | null
    return Boolean(video?.poster && (video.poster.startsWith('data:image/') || video.poster.includes('/srcs/')))
  })
  await page.getByTestId('healing-knowledge-detail').getByRole('button').first().click()
  await expect(page.getByTestId('healing-knowledge-detail')).toHaveCount(0)
  await page.getByTestId('healing-knowledge-type-all').click()
  await page.getByTestId('healing-knowledge-sort-trending').click()
  await expect(page.getByTestId('healing-knowledge-item').first()).toBeVisible()
  const firstKnowledgeTitle = (await page.getByTestId('healing-knowledge-item').first().locator('h3').textContent()) || ''
  await page.getByTestId('healing-knowledge-search').fill(firstKnowledgeTitle.slice(0, 4))
  await expect(page.getByTestId('healing-knowledge-item').first()).toContainText(firstKnowledgeTitle)
  await page.getByTestId('healing-knowledge-item').first().click()
  await expect(page.getByTestId('healing-knowledge-detail')).toBeVisible()
  await expect(page.getByTestId('healing-knowledge-detail')).toContainText(firstKnowledgeTitle)
  await page.getByTestId('healing-knowledge-detail').getByRole('button').filter({ hasText: /收藏/ }).click()
  await expect(page.getByText('已添加到收藏').or(page.getByText('已取消收藏'))).toBeVisible()
  await page.keyboard.press('Escape').catch(() => undefined)
  await page.getByTestId('healing-knowledge-detail').getByRole('button').first().click()
  await expect(page.getByTestId('healing-knowledge-detail')).toHaveCount(0)
  await page.getByTestId('healing-knowledge-favorite').first().click()
  await expect(page.getByText('已添加到收藏').or(page.getByText('已取消收藏'))).toBeVisible()
})

test('doctor login can reach dashboard and alerts page', async ({ page }) => {
  const uniqueTitle = `知识上传 ${Date.now()}`
  const uniqueHandleNote = `已处理 ${Date.now()}`
  const uniqueVerificationCode = `PX${Date.now()}`
  const seededAlert = await seedRiskAlert()

  await page.goto(`${baseUrl}/login`)
  await page.getByTestId('role-doctor').click()
  await page.getByTestId('username-input').fill(doctorUsername)
  await page.getByTestId('password-input').fill(password)
  await page.locator('form').getByRole('button', { name: '登录' }).click()

  await expectPath(page, '/admin/dashboard')
  await expect(page.getByRole('heading', { name: '管理员数据看板' })).toBeVisible()
  await expect(page.getByText('对齐 xinyu-care')).toHaveCount(0)
  await expect(page.getByText('真实后端数据')).toHaveCount(0)

  await page.goto(`${baseUrl}/admin/alerts`)
  await expect(page.getByRole('heading', { name: '风险预警' })).toBeVisible()
  await expect(page.getByText('对齐 xinyu-care')).toHaveCount(0)
  await expect(page.getByText(seededAlert.description)).toBeVisible()
  await page.getByTestId('alert-handle-trigger').first().click()
  await page.getByTestId('alert-notes-input').fill(uniqueHandleNote)
  await page.getByTestId('alert-confirm-handle').click()
  await expect(page.getByTestId('doctor-alerts-toast')).toContainText('预警已处理')
  await expect(page.locator('.rounded-\\[8px\\].border-emerald-200', { hasText: '预警已处理' })).toHaveCount(0)
  await page.getByTestId('alerts-tab-handled').click()
  await expect(page.getByText(uniqueHandleNote)).toBeVisible()

  await page.goto(`${baseUrl}/admin/patients`)
  await expect(page.getByRole('heading', { name: '参与者管理' })).toBeVisible()
  await expect(page.getByText('对齐 xinyu-care')).toHaveCount(0)
  await page.getByTestId('patient-search-input').fill(userUsername)
  await page.getByTestId('patient-view-detail').first().click()
  await expect(page.getByTestId('patient-detail-dialog')).toBeVisible()
  await page.getByTestId('patient-scale-report-toggle').first().click()
  await expect(page.getByTestId('patient-scale-report-detail').first()).toContainText('风险等级分布')
  await page.getByTestId('patient-tab-voice').click()
  await expect(page.getByText('语音情绪').first()).toBeVisible()
  await page.getByTestId('patient-voice-report-toggle').first().click()
  await expect(page.getByTestId('patient-voice-report-detail').first()).toContainText('声学特征指标')
  await page.getByTestId('patient-tab-conversation').click()
  await expect(page.getByText('对话记录').first()).toBeVisible()
  await page.getByTestId('patient-tab-expression').click()
  await expect(page.getByText('表情识别').first()).toBeVisible()
  await page.getByTestId('patient-expression-report-toggle').first().click()
  await expect(page.getByTestId('patient-expression-report-detail').first()).toContainText('面部表情分布')
  await expect(page.getByTestId('patient-expression-report-detail').first()).toContainText('厌恶')
  await expect(page.getByTestId('patient-expression-report-detail').first()).toContainText('轻蔑')
  await expect(page.getByTestId('patient-expression-report-detail').first()).toContainText('痛苦')
  await page.getByRole('button', { name: '关闭' }).click()

  await page.getByTestId('open-code-manager').click()
  await page.getByTestId('verification-code-input').fill(uniqueVerificationCode)
  await page.getByTestId('create-verification-code').click()
  await expect(page.getByTestId('doctor-patients-toast')).toContainText('验证码创建成功')
  await expect(page.getByText(uniqueVerificationCode)).toBeVisible()
  await expect(page.locator('.rounded-\\[8px\\].border-emerald-200', { hasText: '验证码创建成功' })).toHaveCount(0)
  await page.getByRole('button', { name: '关闭' }).click()

  await page.goto(`${baseUrl}/admin/knowledge`)
  await expect(page.getByRole('heading', { name: '知识库管理' })).toBeVisible()
  await expect(page.getByText('对齐 xinyu-care')).toHaveCount(0)
  await page.getByTestId('knowledge-title-input').fill(uniqueTitle)
  await page.getByTestId('knowledge-category-select').selectOption('research')
  await page.getByPlaceholder('请输入内容摘要、适用场景或说明').fill('管理员端文档上传回归测试')
  await page.getByTestId('knowledge-file-input').setInputFiles('/root/jry/chuxin/frontend/tests/fixtures/knowledge-doc.txt')
  await page.getByTestId('knowledge-save').click()
  await expect(page.getByTestId('doctor-knowledge-toast')).toContainText('知识内容已创建')
  await expect(page.locator('.rounded-\\[8px\\].border-emerald-200', { hasText: '知识内容已创建' })).toHaveCount(0)
  await expect(page.getByText(uniqueTitle)).toBeVisible()
  await expect(page.getByText('knowledge-doc.txt').first()).toBeVisible()
})
