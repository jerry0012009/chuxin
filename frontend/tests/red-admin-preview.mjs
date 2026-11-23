import assert from 'node:assert/strict'
import { mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'
import { chromium, devices, request } from 'playwright'

const variant = process.env.PREVIEW_VARIANT
assert.ok(['before', 'after'].includes(variant))
const site = new URL(process.env.PREVIEW_URL)
assert.equal(site.hostname, '127.0.0.1', 'Use an isolated loopback preview')
assert.equal(site.port, variant === 'before' ? '28110' : '28111')
const password = process.env.PREVIEW_PASSWORD
assert.ok(password?.length >= 12)
const username = 'preview_round1'
const base = site.href.replace(/\/$/, '')
const output = resolve(process.env.PREVIEW_OUTPUT || './test-results/round1', variant)
await mkdir(output, { recursive: true })
const client = await request.newContext()

async function api(path, { method = 'GET', token, data } = {}) {
  const response = await client.fetch(`${base}/api${path}`, {
    method, data, headers: token ? { authorization: `Bearer ${token}` } : {},
  })
  assert.ok(response.ok(), `${method} ${path}: ${response.status()} ${response.ok() ? '' : await response.text()}`)
  const body = await response.json()
  return body.data ?? body
}

async function prepare() {
  const staff = await api('/auth/login', { method: 'POST', data: { usernameOrEmail: 'admin', password: '123456' } })
  const token = staff.accessToken
  if (process.env.PREVIEW_REUSE_FIXTURE === '1') {
    const user = await api('/auth/login', { method: 'POST', data: { usernameOrEmail: username, password } })
    await prepareSharedIntervention(token, user.user.id)
    return loadFixture(user.accessToken)
  }
  const browserAccount = { username, password, role: 'user' }
  const departments = await api('/departments')
  const user = await api('/auth/signup', { method: 'POST', data: { ...browserAccount, departmentId: departments[0].id } })
  const userToken = user.accessToken
  const userId = user.user.id
  await api('/data/profiles', { method: 'PATCH', token: userToken, data: { data: { full_name: '预览测试员' }, single: true } })

  const materials = await api('/assessment-publish-tasks/materials', { token })
  const scale = materials.scale.find((item) => item.code === 'huaxinyun-gad7-anxiety')
  const neuropsych = materials.neuropsych.find((item) => item.code === 'columbia-card-task-hot-demo')
  assert.ok(scale && neuropsych)
  const items = [
    ['scale', '广泛性焦虑量表（GAD-7）', scale.id],
    ['neuropsych', '神经心理测验', neuropsych.id],
    ['dialogue_scale', '对话式心理健康评估', null],
    ['voice', '语音识别', null],
    ['expression', '表情评估', null],
  ].map(([item_type, title, target_id], index) => ({ item_type, title, target_id, order_no: index + 1, required: true }))
  const task = await api('/assessment-publish-tasks', { method: 'POST', token, data: { title: '身心状态初筛测评', user_ids: [userId], items } })
  await api(`/assessment-publish-tasks/${task.id}/publish`, { method: 'POST', token })

  await prepareSharedIntervention(token, userId)

  const report = await api('/scale-assessments/free/huaxinyun-gad7-anxiety/start', { method: 'POST', token: userToken })
  const answers = report.survey.questions.map((question) => ({
    questionId: question.id, questionType: question.question_type, myAnswer: question.options[0].id,
  }))
  const result = await api(`/scale-assessments/records/${report.id}/submit`, { method: 'POST', token: userToken, data: { answers } })
  assert.equal(result.calc_status, 'done')
  assert.equal(result.answers.length, 7)

  return loadFixture(userToken)
}

async function prepareSharedIntervention(token, userId) {
  const available = await api('/intervention-tasks/materials', { token })
  const plans = await api('/intervention-tasks', { token })
  for (const [title, materials] of [
    ['身心调节练习', [available.mood[0], available.meditation[0]]],
    ['身心调节练习（重复素材核验）', [available.mood[0]]],
  ]) {
    if (plans.some((plan) => plan.title === title)) continue
    const items = materials.map((item, index) => ({
      material_id: item.id, title: item.title, frequency_type: 'daily', required_count: 1, required: true,
      duration_sec: item.duration_sec || 10, order_no: index + 1,
    }))
    const plan = await api('/intervention-tasks', { method: 'POST', token, data: {
      title, user_ids: [userId], duration_days: 30, daily_required_count: items.length, items,
    } })
    await api(`/intervention-tasks/${plan.id}/publish`, { method: 'POST', token })
  }
}

async function loadFixture(userToken) {
  const assignee = (await api('/assessment-publish-tasks/my', { token: userToken })).find((item) => item.batch_title === '身心状态初筛测评')
  assert.ok(assignee)
  const detail = await api(`/assessment-publish-tasks/my/${assignee.id}`, { token: userToken })
  assert.deepEqual(detail.items.map((item) => item.item_type), ['scale', 'neuropsych', 'dialogue_scale', 'voice', 'expression'])
  await api(`/scale-assessments/records/${detail.items[0].result_ref_id}/start`, { method: 'POST', token: userToken })
  if (variant === 'after') {
    const today = await api('/intervention-tasks/my/today', { token: userToken })
    assert.ok(today.tasks.length >= 2)
    assert.ok(today.tasks.some((item) => item.record_ids?.length > 1), 'Expected shared intervention material to be merged')
  }
  return { assigneeId: assignee.id, activeRecord: detail.items[0].result_ref_id }
}

const fixture = await prepare()
const browser = await chromium.launch({ executablePath: process.env.CHUXIN_CHROMIUM_PATH })
try {
  for (const [device, options] of [
    ['desktop', { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 }],
    ['mobile', { ...devices['iPhone 13'], viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 }],
    ...(variant === 'after' ? [['narrow', { viewport: { width: 320, height: 720 }, isMobile: true, hasTouch: true }]] : []),
  ]) {
    const page = await browser.newPage({ ...options, locale: 'zh-CN', timezoneId: 'Asia/Shanghai', colorScheme: 'light' })
    const exceptions = []
    page.on('pageerror', (error) => exceptions.push(error.message))
    async function capture(name) {
      await page.evaluate(() => document.fonts.ready)
      if (variant === 'after') {
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), `${device} ${name}: horizontal document overflow`)
      }
      if (device !== 'narrow') await page.screenshot({ path: resolve(output, `${name}-${device}.png`), fullPage: true, animations: 'disabled' })
    }

    await page.goto(`${base}/login`)
    await page.getByTestId('username-input').waitFor()
    await capture('login')
    if (variant === 'after') {
      await page.getByTestId('role-doctor').click()
      await page.getByTestId('mode-register').click()
      await page.getByTestId('verification-code-input').waitFor()
      await page.getByTestId('role-user').click()
      await page.getByTestId('department-select').waitFor()
      await page.getByTestId('mode-login').click()
    }
    await page.getByTestId('username-input').fill(username)
    await page.getByTestId('password-input').fill(password)
    await page.locator('form button[type="submit"]').click()
    await page.waitForURL(`${base}/`)
    await page.getByText('身心状态初筛测评', { exact: true }).waitFor()
    if (variant === 'after') {
      await page.getByRole('heading', { name: '我的工作台' }).waitFor()
      await page.getByTestId('work-intervention').getByText('待完成').first().waitFor()
      await page.getByTestId('work-records').getByRole('link', { name: /GAD-7/ }).waitFor()
    }
    await capture('workbench')

    if (variant === 'after') await page.getByTestId('work-current-link').click()
    else await page.getByRole('button', { name: /身心状态初筛测评/ }).click()
    await page.waitForURL(`${base}/assessment-tasks/${fixture.assigneeId}`)
    await page.getByRole('heading', { name: '表情评估' }).waitFor()
    if (variant === 'after') {
      assert.equal(await page.getByTestId('task-step').count(), 5)
      assert.ok(await page.getByTestId('task-step-title').evaluateAll((titles) =>
        titles.every((title) => title.getBoundingClientRect().width >= 160 && title.getBoundingClientRect().height <= 60),
      ), `${device}: task titles must have room for readable wrapping`)
      await page.getByTestId('task-continue').filter({ hasText: '继续测评' }).waitFor()
    }
    await capture('task')

    if (variant === 'after') {
      await page.getByTestId('task-continue').click()
      await page.waitForURL((url) => url.pathname.endsWith('/scale-assessment') && url.searchParams.get('recordId') === fixture.activeRecord)
      await page.getByText('第 1 / 7 题', { exact: true }).waitFor()
      await page.goto(`${base}/`)
      await page.getByTestId('work-records').getByRole('link', { name: /GAD-7/ }).click()
      await page.getByText('量表测评报告', { exact: true }).waitFor()
      await page.goto(`${base}/`)
      await page.getByTestId('work-records').getByRole('link', { name: '查看量表记录' }).click()
      assert.equal(new URL(page.url()).searchParams.get('tab'), 'completed')
      await page.getByRole('button', { name: /查看报告/ }).first().waitFor()
      await page.goto(`${base}/`)
      await page.getByTestId('work-intervention').getByRole('link', { name: '查看干预计划' }).click()
      await page.waitForURL(`${base}/profile/healing-plan`)
    }
    assert.deepEqual(exceptions, [])
    console.log(`${variant} ${device}: passed`)
    await page.close()
  }
} finally {
  await browser.close()
  await client.dispose()
}
