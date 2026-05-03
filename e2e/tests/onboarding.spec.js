import { test, expect } from '@playwright/test'

const SS = 'test-results/tutorial-audit'

test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => {
    localStorage.removeItem('onboarding_dismissed_v1')
    localStorage.removeItem('onboarding_chat_tried')
  })
})

// Helper: register a fresh user and land on home
async function registerFreshUser(page) {
  const ts = Date.now()
  const email = `ob_test_${ts}@example.com`
  await page.goto('/register')
  await page.fill('input[name="email"]', email)
  await page.fill('input[name="username"]', `obtest${ts}`)
  await page.fill('input[name="password"]', 'TestPass123!')
  await page.click('button[type="submit"]')
  await page.waitForURL(/\/(app\/)?$|\/memorials|\/home/, { timeout: 10000 })
  await page.waitForTimeout(800)
  return email
}

test('Onboarding: новый пользователь видит чеклист — 0 of 4', async ({ page }) => {
  await registerFreshUser(page)
  await page.goto('/')
  await page.waitForLoadState('networkidle')

  const checklist = page.locator('.ob-wrap')
  await expect(checklist).toBeVisible({ timeout: 5000 })
  await expect(checklist.locator('.ob-progress')).toHaveText('0 of 4 done')

  // Все 4 шага не выполнены
  const steps = checklist.locator('.ob-step:not(.ob-step--done)')
  await expect(steps).toHaveCount(4)

  await checklist.scrollIntoViewIfNeeded()
  await page.waitForTimeout(300)
  await page.screenshot({ path: `${SS}/onboarding-0-of-4.png` })
})

test('Onboarding: шаг 1 выполнен после создания мемориала', async ({ page }) => {
  await registerFreshUser(page)

  // Создаём мемориал
  await page.goto('/memorials/new')
  await page.waitForLoadState('networkidle')
  await page.fill('input[name="name"], input[placeholder*="name"], input[placeholder*="Name"]', 'Test Person')
  await page.click('button[type="submit"]')
  await page.waitForURL(/\/memorials\/\d+/, { timeout: 10000 })

  // Возвращаемся на главную
  await page.goto('/')
  await page.waitForLoadState('networkidle')

  const checklist = page.locator('.ob-wrap')
  await expect(checklist).toBeVisible({ timeout: 5000 })
  await expect(checklist.locator('.ob-progress')).toHaveText('1 of 4 done')

  // Шаг "Create memorial" отмечен
  const doneSteps = checklist.locator('.ob-step--done')
  await expect(doneSteps).toHaveCount(1)

  await checklist.scrollIntoViewIfNeeded()
  await page.waitForTimeout(300)
  await page.screenshot({ path: `${SS}/onboarding-1-of-4.png` })
})

test('Onboarding: dismiss скрывает чеклист', async ({ page }) => {
  await registerFreshUser(page)
  await page.goto('/')
  await page.waitForLoadState('networkidle')

  const checklist = page.locator('.ob-wrap')
  await expect(checklist).toBeVisible({ timeout: 5000 })
  await checklist.locator('.ob-dismiss').click()
  await expect(checklist).not.toBeVisible()
  await page.screenshot({ path: `${SS}/onboarding-dismissed.png` })
})

test('Onboarding: шаг 4 (chat) выполнен после открытия вкладки', async ({ page }) => {
  await registerFreshUser(page)

  // Создаём мемориал
  await page.goto('/memorials/new')
  await page.waitForLoadState('networkidle')
  await page.fill('input[name="name"], input[placeholder*="name"], input[placeholder*="Name"]', 'Chat Test Person')
  await page.click('button[type="submit"]')
  await page.waitForURL(/\/memorials\/\d+/, { timeout: 10000 })

  // Кликаем на Chat вкладку
  const chatTab = page.locator('button', { hasText: /chat/i }).first()
  await chatTab.click()
  await page.waitForTimeout(300)

  // localStorage должен быть выставлен
  const val = await page.evaluate(() => localStorage.getItem('onboarding_chat_tried'))
  expect(val).toBe('1')

  await page.screenshot({ path: `${SS}/onboarding-chat-flagged.png` })
})
