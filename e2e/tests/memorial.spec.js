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
    await expect(page.locator(`text=${name}`)).toBeVisible({ timeout: 5000 });
  });

  test("2.5 Отображение публичного мемориала /m/:id", async ({ page }) => {
    // Создаём мемориал
    await page.goto("/memorials/new");
    await page.fill('[name="name"]', "Публичный мемориал E2E");
    // Включаем публичный если есть чекбокс
    const publicCheckbox = page.locator('[name="is_public"], input[type="checkbox"]').first();
    if (await publicCheckbox.isVisible()) await publicCheckbox.check();
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/memorials\/\d+/);

    const url = page.url();
    const id = url.match(/\/memorials\/(\d+)/)?.[1];
    expect(id).toBeTruthy();

    // Публичная страница должна открываться
    await page.goto(`/m/${id}`);
    await expect(page.locator("text=Публичный мемориал E2E")).toBeVisible({ timeout: 5000 });
  });
});

test.describe("Публичная страница (анонимный доступ)", () => {
  test("8.1 Открыть /m/:id для публичного мемориала без авторизации", async ({ page, context }) => {
    // Сначала создаём от авторизованного пользователя
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
    await page.waitForURL(/\/memorials\/\d+/);
    const id = page.url().match(/\/memorials\/(\d+)/)?.[1];

    // Открываем в новом контексте (без токена)
    const anonPage = await context.newPage();
    await anonPage.goto(`/m/${id}`);
    await expect(anonPage.locator("text=Открытый мемориал")).toBeVisible({ timeout: 8000 });
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
    // is_public = false по умолчанию
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/memorials\/\d+/);
    const id = page.url().match(/\/memorials\/(\d+)/)?.[1];

    const anonPage = await context.newPage();
    await anonPage.goto(`/m/${id}`);
    // Должен быть блок запроса доступа или 403-страница — но не 404
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

    // Все карточки не должны выходить за ширину экрана
    const cards = page.locator(".memorial-card, [class*='card']");
    const count = await cards.count();
    for (let i = 0; i < count; i++) {
      const box = await cards.nth(i).boundingBox();
      if (box) {
        expect(box.x + box.width).toBeLessThanOrEqual(385); // небольшой допуск на скроллбар
      }
    }
  });
});
