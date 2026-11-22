import { expect, type Page, test } from '@playwright/test'

const baseUrl = 'http://127.0.0.1:5175'
const userUsername = 'codex_1779982823'
const doctorUsername = 'codexdoc_1779982823'
const password = 'secret123'

async function login(page: Page, role: 'user' | 'doctor') {
  await page.goto(`${baseUrl}/login`)
  await page.getByTestId(role === 'doctor' ? 'role-doctor' : 'role-user').click()
  await page.getByTestId('mode-login').click()
  await page.getByTestId('username-input').fill(role === 'doctor' ? doctorUsername : userUsername)
  await page.getByTestId('password-input').fill(password)
  await page.locator('form').getByRole('button', { name: '登录' }).click()
}

test('route guard redirects anonymous users to login with original target', async ({ page }) => {
  await page.goto(`${baseUrl}/record`)

  await page.waitForURL((url) => url.pathname === '/login' && !url.searchParams.has('redirect'))
  await expect(page.getByRole('heading', { name: '初心（ChuXin）' })).toBeVisible()
  await page.getByTestId('role-user').click()
  await page.getByTestId('mode-login').click()
  await page.getByTestId('username-input').fill(userUsername)
  await page.getByTestId('password-input').fill(password)
  await page.locator('form').getByRole('button', { name: '登录' }).click()
  await page.waitForURL(/\/record$/)
})

test('route guard treats reference public error paths as home redirects', async ({ page }) => {
  await page.goto(`${baseUrl}/404`)

  await page.waitForURL((url) => url.pathname === '/')
  await expect(page.getByTestId('home-feature-assessment')).toBeVisible()
})

test('route guard blocks normal users from doctor workspace', async ({ page }) => {
  await login(page, 'user')
  await page.waitForURL((url) => url.pathname !== '/login')

  await page.goto(`${baseUrl}/admin/dashboard`)

  await page.waitForURL(/\/profile$/)
  await expect(page.getByRole('heading', { name: '查看健康报告' })).toBeVisible()
})

test('route guard allows admin workspace and redirects admin root to dashboard', async ({ page }) => {
  await login(page, 'doctor')
  await page.waitForURL(/\/admin\/dashboard$/)
  await expect(page.getByRole('heading', { name: '管理员数据看板' })).toBeVisible()

  await page.goto(`${baseUrl}/admin`)

  await page.waitForURL(/\/admin\/dashboard$/)
  await expect(page.getByRole('heading', { name: '管理员数据看板' })).toBeVisible()
})
