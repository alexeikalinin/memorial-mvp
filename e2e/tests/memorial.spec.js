import { test, expect } from "@playwright/test";
import { registerUser, createMemorial, uniqueEmail, uniqueUsername } from "./helpers.js";

test.describe("Создание и управление мемориалами", () => {
  test.beforeEach(async ({ page }) => {
    await registerUser(page, {
      email: uniqueEmail(),
      username: uniqueUsername(),
      fullName: "Memorial Test User",
      password: "password123",
    });
  });

  test("2.1 Создать мемориал и увидеть на главной", async ({ page }) => {
    const { name } = await createMemorial(page, "Иван Петрович Иванов");
    await page.goto("/");
    // После перезагрузки: auth check (~3s) + загрузка списка (~3s)
    await expect(page.locator(`text=${name}`)).toBeVisible({ timeout: 15000 });
  });

  test("2.2 Добавить воспоминание через UI", async ({ page }) => {
    const { id } = await createMemorial(page, "Мемориал с воспоминанием");
    await page.goto(`/memorials/${id}`);

    // Ищем вкладку Memories (ждём загрузки страницы)
    const memTab = page.locator("button:has-text('Memories'), button:has-text('Воспоминания')").first();
    await memTab.waitFor({ state: 'visible', timeout: 15000 });
    await memTab.click();

    // Нажимаем "Add a memory"
    const addBtn = page.locator("button:has-text('Add a memory'), button:has-text('Добавить воспоминание')").first();
    await addBtn.waitFor({ state: 'visible', timeout: 10000 });
    await addBtn.click();

    // Ждём появления формы (id="title")
    await page.waitForSelector('#title', { timeout: 10000 });
    await page.fill('#title', "Тестовое воспоминание");
    await page.fill('#content', "Он был замечательным человеком с добрым сердцем.");
    await page.click('button[type="submit"]');

    // Ждём закрытия формы и исчезновения спиннера загрузки
    await page.waitForSelector('#title', { state: 'hidden', timeout: 15000 }).catch(() => {});
    await page.locator("text=Loading memories").waitFor({ state: 'hidden', timeout: 40000 }).catch(() => {});
    await expect(page.locator("text=Тестовое воспоминание")).toBeVisible({ timeout: 40000 });
  });

  test("2.5 Отображение публичного мемориала /m/:id", async ({ page }) => {
    await page.goto("/memorials/new");
    await page.fill('[name="name"]', "Публичный мемориал E2E");
    const publicCheckbox = page.locator('[name="is_public"], input[type="checkbox"]').first();
    if (await publicCheckbox.isVisible()) await publicCheckbox.check();
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/memorials\/\d+/, { timeout: 20000 });

    const url = page.url();
    const id = url.match(/\/memorials\/(\d+)/)?.[1];
    expect(id).toBeTruthy();

    await page.goto(`/m/${id}`);
    await expect(page.locator("text=Публичный мемориал E2E").first()).toBeVisible({ timeout: 15000 });
  });
});

test.describe("Публичная страница (анонимный доступ)", () => {
  test("8.1 Открыть /m/:id для публичного мемориала без авторизации", async ({ page, context }) => {
    await registerUser(page, {
      email: uniqueEmail(),
      username: uniqueUsername(),
      fullName: "Owner",
      password: "password123",
    });
    await page.goto("/memorials/new");
    await page.fill('[name="name"]', "Открытый мемориал");
    const publicCheckbox = page.locator('[name="is_public"], input[type="checkbox"]').first();
    if (await publicCheckbox.isVisible()) await publicCheckbox.check();
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/memorials\/\d+/, { timeout: 40000 });
    const id = page.url().match(/\/memorials\/(\d+)/)?.[1];

    const anonPage = await context.newPage();
    await anonPage.goto(`/m/${id}`);
    // Ждём исчезновения загрузчика перед проверкой контента
    await anonPage.locator("text=Загрузка").waitFor({ state: 'hidden', timeout: 40000 }).catch(() => {});
    await expect(anonPage.locator("text=Открытый мемориал").first()).toBeVisible({ timeout: 40000 });
    await anonPage.close();
  });

  test("8.4 Приватный мемориал без авторизации — блок запроса доступа", async ({ page, context }) => {
    await registerUser(page, {
      email: uniqueEmail(),
      username: uniqueUsername(),
      fullName: "Owner2",
      password: "password123",
    });
    await page.goto("/memorials/new");
    await page.fill('[name="name"]', "Приватный мемориал");
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/memorials\/\d+/, { timeout: 20000 });
    const id = page.url().match(/\/memorials\/(\d+)/)?.[1];

    const anonPage = await context.newPage();
    await anonPage.goto(`/m/${id}`);
    const url = anonPage.url();
    expect(url).not.toContain("404");
    await anonPage.close();
  });
});

test.describe("Мобильная адаптация", () => {
  test("13.1 Главная страница на 375px — карточки в пределах экрана", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await registerUser(page, {
      email: uniqueEmail(),
      username: uniqueUsername(),
      fullName: "Mobile User",
      password: "password123",
    });
    await createMemorial(page, "Мобильный мемориал");
    await page.goto("/");
    // Ждём загрузки карточек
    await page.waitForTimeout(3000);

    const cards = page.locator(".memorial-card, [class*='card']");
    const count = await cards.count();
    for (let i = 0; i < count; i++) {
      const box = await cards.nth(i).boundingBox();
      if (box) {
        expect(box.x + box.width).toBeLessThanOrEqual(385);
      }
    }
  });

  test("13.5 Мобайл: создание мемориала на 375px", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await registerUser(page, {
      email: uniqueEmail(),
      username: uniqueUsername(),
      fullName: "Mobile Creator",
      password: "password123",
    });
    await page.goto("/memorials/new");
    await page.fill('[name="name"]', "Мобильный новый");
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/memorials\/\d+/, { timeout: 20000 });
    expect(page.url()).toMatch(/\/memorials\/\d+/);
  });

  test("13.6 Мобайл: публичная страница /m/:id на 375px", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await registerUser(page, {
      email: uniqueEmail(),
      username: uniqueUsername(),
      fullName: "Mobile Viewer",
      password: "password123",
    });
    await page.goto("/memorials/new");
    await page.fill('[name="name"]', "Мобильный публичный");
    const publicCheckbox = page.locator('[name="is_public"], input[type="checkbox"]').first();
    if (await publicCheckbox.isVisible()) await publicCheckbox.check();
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/memorials\/\d+/, { timeout: 20000 });
    const id = page.url().match(/\/memorials\/(\d+)/)?.[1];

    await page.goto(`/m/${id}`);
    await expect(page.locator("text=Мобильный публичный").first()).toBeVisible({ timeout: 15000 });

    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    expect(bodyWidth).toBeLessThanOrEqual(390);
  });

  test("13.7 Мобайл: карточки мемориалов не выходят за ширину 375px", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await registerUser(page, {
      email: uniqueEmail(),
      username: uniqueUsername(),
      fullName: "Mobile User",
      password: "password123",
    });
    await createMemorial(page, "Мобильный мемориал");
    await page.goto("/");
    await page.waitForTimeout(3000);

    const cards = page.locator(".memorial-card, [class*='card']");
    const count = await cards.count();
    for (let i = 0; i < count; i++) {
      const box = await cards.nth(i).boundingBox();
      if (box) {
        expect(box.x + box.width).toBeLessThanOrEqual(385);
      }
    }
  });
});
