import assert from 'node:assert/strict'
import { randomBytes } from 'node:crypto'
import { chromium, devices } from 'playwright'

const base = (process.env.CHUXIN_TRIAL_URL || '').replace(/\/$/, '')
assert.ok(base, 'Set CHUXIN_TRIAL_URL')
const api = `${base}/api`
const username = `trial_${randomBytes(5).toString('hex')}`
const password = randomBytes(16).toString('hex')
const browser = await chromium.launch({ executablePath: process.env.CHUXIN_CHROMIUM_PATH })

try {
  const desktop = await browser.newPage({ viewport: { width: 1280, height: 900 } })
  const errors = []
  desktop.on('pageerror', (error) => errors.push(error.message))
  await desktop.goto(`${base}/scale-assessment`)
  await desktop.getByTestId('mode-register').click()
  await desktop.getByTestId('username-input').fill(username)
  await desktop.getByTestId('password-input').fill(password)
  await desktop.locator('#department-id option[value]:not([value=""])').first().waitFor({ state: 'attached' })
  await desktop.getByTestId('department-select').selectOption({ index: 1 })
  const signup = desktop.waitForResponse((res) => res.url() === `${api}/auth/signup`)
  await desktop.locator('button[type=submit]').click()
  const signupResponse = await signup
  assert.equal(signupResponse.status(), 200, signupResponse.status() === 200 ? undefined : await signupResponse.text())
  const { accessToken, user } = await signupResponse.json()
  assert.equal(user.user_metadata.role, 'user')
  const headers = { authorization: `Bearer ${accessToken}` }
  const profile = await desktop.request.patch(`${api}/data/profiles`, {
    headers,
    data: { data: { full_name: 'Trial User', role: 'user', email: 'trial@example.invalid' }, single: true },
  })
  assert.equal(profile.status(), 200)
  assert.equal((await profile.json()).data.full_name, 'Trial User')
  const privilegedRoleChange = await desktop.request.patch(`${api}/data/profiles`, {
    headers,
    data: { data: { role: 'admin' }, single: true },
  })
  assert.equal(privilegedRoleChange.status(), 403)
  await desktop.waitForURL((url) => !url.pathname.endsWith('/login'))
  await desktop.goto(`${base}/scale-assessment`)
  await desktop.getByRole('button', { name: '自由测评 90', exact: true }).click()
  const startButtons = desktop.getByRole('button', { name: '开始自由测评', exact: true })
  assert.equal(await startButtons.count(), 90)

  const gad = desktop.getByRole('heading', { name: /GAD-7/ })
  const started = desktop.waitForResponse((res) => res.url().endsWith('/free/huaxinyun-gad7-anxiety/start'))
  await gad.locator('../../..').getByRole('button', { name: '开始自由测评' }).click()
  const record = (await (await started).json()).data
  assert.equal(record.survey.questions.length, 7)
  const submitted = desktop.waitForResponse((res) => res.url() === `${api}/scale-assessments/records/${record.id}/submit`)
  for (let i = 1; i <= 7; i++) {
    await desktop.getByText(`第 ${i} / 7 题`, { exact: true }).waitFor()
    await desktop.getByRole('button', { name: /^A\./ }).click()
  }
  const result = (await (await submitted).json()).data
  assert.equal(result.status, 'completed')
  assert.equal(result.calc_status, 'done')
  assert.equal(result.answers.length, 7)
  assert.ok(result.dimensions.length > 0)
  await desktop.getByText('Scale Report', { exact: true }).waitFor()

  const mobile = await browser.newPage(devices['iPhone 13'])
  mobile.on('pageerror', (error) => errors.push(error.message))
  await mobile.goto(`${base}/scale-assessment`)
  await mobile.getByTestId('username-input').fill(username)
  await mobile.getByTestId('password-input').fill(password)
  await mobile.locator('button[type=submit]').click()
  await mobile.getByRole('button', { name: '已完成 1', exact: true }).click()
  await mobile.getByText(/GAD-7/).first().waitFor()
  assert.deepEqual(errors, [])
  console.log(JSON.stringify({ username, recordId: record.id, answers: result.answers.length, score: result.total_score }))
} finally {
  await browser.close()
}
