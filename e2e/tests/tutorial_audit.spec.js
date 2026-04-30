import { test, expect } from '@playwright/test'
import path from 'path'

const SS_DIR = path.resolve('test-results/tutorial-audit')

// Очищаем demo_tutorial_v1 перед каждым тестом, чтобы туториал начинался заново
test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => {
    localStorage.removeItem('demo_tutorial_v1')
  })
})

test('Step 1 — overlay on /demo (first visit)', async ({ page }) => {
  await page.goto('/demo')
  await page.waitForLoadState('networkidle')

  const overlay = page.locator('.dt-overlay')
  await expect(overlay).toBeVisible({ timeout: 5000 })

  const card = page.locator('.dt-card')
  await expect(card).toBeVisible()

  // Проверяем контент
  await expect(card.locator('.dt-emoji')).toHaveText('👨‍👩‍👧‍👦')
  await expect(card.locator('.dt-title')).toHaveText('4 families. 5 generations.')
  await expect(card.locator('.dt-btn-primary')).toHaveText("Let's go →")
  await expect(card.locator('.dt-btn-skip')).toHaveText('Skip tutorial')

  await page.screenshot({ path: `${SS_DIR}/step1-overlay.png`, fullPage: false })
})

test('Step 2 — hint after clicking family card', async ({ page }) => {
  await page.goto('/demo')
  await page.waitForLoadState('networkidle')

  // Шаг 1 видим — кликаем "Let's go"
  await page.locator('.dt-btn-primary').click()
  await expect(page.locator('.dt-overlay')).not.toBeVisible()

  // Кликаем на первую семью
  const familyCard = page.locator('.demo-family-card').first()
  await expect(familyCard).toBeVisible({ timeout: 5000 })
  await familyCard.click()

  // Шаг 2 — hint в секции членов семьи
  const hint = page.locator('.dt-hint')
  await expect(hint).toBeVisible({ timeout: 3000 })
  await expect(hint.locator('.dt-hint-title')).toHaveText('Meet the family')

  await page.screenshot({ path: `${SS_DIR}/step2-hint.png`, fullPage: false })
})

test('Step 3 — hint on memorial page (chat section)', async ({ page }) => {
  await page.goto('/demo')
  await page.waitForLoadState('networkidle')

  // Шаг 1 → кликаем Let's go
  await page.locator('.dt-btn-primary').click()

  // Кликаем семью
  await page.locator('.demo-family-card').first().click()
  await page.waitForSelector('.demo-member-card', { timeout: 5000 })

  // Кликаем на первого члена семьи → переходим на /m/:id?demo_step=3
  await page.locator('.demo-member-card').first().click()
  await page.waitForLoadState('networkidle')

  // Убеждаемся что мы на странице мемориала
  await expect(page).toHaveURL(/\/m\/\d+/)

  // Шаг 3 hint должен быть виден в секции chat
  const hint = page.locator('.dt-hint')
  await expect(hint).toBeVisible({ timeout: 5000 })
  await expect(hint.locator('.dt-hint-title')).toHaveText('Chat with the avatar')

  // Scroll hint into view for screenshot (scrollIntoView fires async via useEffect)
  await hint.scrollIntoViewIfNeeded()
  await page.waitForTimeout(400)
  await page.screenshot({ path: `${SS_DIR}/step3-chat-hint.png`, fullPage: false })
})

test('Step 4 — hint on memories tab', async ({ page }) => {
  await page.goto('/demo')
  await page.waitForLoadState('networkidle')

  await page.locator('.dt-btn-primary').click()
  await page.locator('.demo-family-card').first().click()
  await page.waitForSelector('.demo-member-card', { timeout: 5000 })
  await page.locator('.demo-member-card').first().click()
  await page.waitForLoadState('networkidle')

  // Закрываем шаг 3 кликом "Got it →"
  await expect(page.locator('.dt-hint')).toBeVisible({ timeout: 5000 })
  await page.locator('.dt-hint-close').click()

  // Кликаем вкладку Memories
  const memoriesTab = page.locator('.public-nav button', { hasText: /Memories/ })
  await expect(memoriesTab).toBeVisible()
  await memoriesTab.click()

  // Шаг 4 hint
  const hint = page.locator('.dt-hint')
  await expect(hint).toBeVisible({ timeout: 3000 })
  await expect(hint.locator('.dt-hint-title')).toHaveText('Memories power the avatar')

  await page.screenshot({ path: `${SS_DIR}/step4-memories-hint.png`, fullPage: false })
})

test('Step 5 — one big family hint', async ({ page }) => {
  await page.goto('/demo')
  await page.waitForLoadState('networkidle')

  await page.locator('.dt-btn-primary').click()
  await page.locator('.demo-family-card').first().click()
  await page.waitForSelector('.demo-member-card', { timeout: 5000 })
  await page.locator('.demo-member-card').first().click()
  await page.waitForLoadState('networkidle')

  // Step 3 → закрыть
  await expect(page.locator('.dt-hint')).toBeVisible({ timeout: 5000 })
  await page.locator('.dt-hint-close').click()

  // Memories tab
  await page.locator('.public-nav button', { hasText: /Memories/ }).click()

  // Step 4 видим
  await expect(page.locator('.dt-hint')).toBeVisible({ timeout: 3000 })
  await expect(page.locator('.dt-hint .dt-hint-title')).toHaveText('Memories power the avatar')

  // Step 4 → закрыть → step 5
  await page.locator('.dt-hint-close').click()
  await expect(page.locator('.dt-hint')).toBeVisible({ timeout: 2000 })
  await expect(page.locator('.dt-hint .dt-hint-title')).toHaveText('One big family')
  // Verify updated text (no hardcoded "Sean")
  await expect(page.locator('.dt-hint .dt-hint-text')).toContainText('connected across generations')

  await page.locator('.dt-hint').scrollIntoViewIfNeeded()
  await page.waitForTimeout(300)
  await page.screenshot({ path: `${SS_DIR}/step5-one-big-family.png`, fullPage: false })
})

test('Skip tutorial — overlay skip clears all steps', async ({ page }) => {
  await page.goto('/demo')
  await page.waitForLoadState('networkidle')

  await page.locator('.dt-btn-skip').click()

  // Overlay должен исчезнуть
  await expect(page.locator('.dt-overlay')).not.toBeVisible()

  // localStorage должен быть "done"
  const val = await page.evaluate(() => localStorage.getItem('demo_tutorial_v1'))
  expect(val).toBe('done')

  await page.screenshot({ path: `${SS_DIR}/skip-tutorial.png`, fullPage: false })
})

test('No tutorial on /demo when already done', async ({ page }) => {
  // page.addInitScript runs AFTER context.addInitScript (beforeEach clears),
  // so setting "done" here wins on first navigation
  await page.addInitScript(() => {
    localStorage.setItem('demo_tutorial_v1', 'done')
  })
  await page.goto('/demo')
  await page.waitForLoadState('networkidle')

  await expect(page.locator('.dt-overlay')).not.toBeVisible()
  await expect(page.locator('.dt-hint')).not.toBeVisible()

  await page.screenshot({ path: `${SS_DIR}/no-tutorial-when-done.png`, fullPage: false })
})
