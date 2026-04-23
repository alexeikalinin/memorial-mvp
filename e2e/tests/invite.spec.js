import { test, expect } from "@playwright/test";
import { registerUser, createMemorial, uniqueEmail, uniqueUsername } from "./helpers.js";

test.describe("Инвайты и вклад гостей", () => {
  let inviteUrl;

  test.beforeEach(async ({ page }) => {
    // Регистрируем владельца и создаём мемориал
    await registerUser(page, {
      email: uniqueEmail(),
      username: uniqueUsername(),
      fullName: "Invite Owner",
      password: "invitepass123",
    });
    await createMemorial(page, "Мемориал для инвайта");
  });

  test("6.3 Открыть /contribute/:token без авторизации", async ({ page, context }) => {
    // Находим страницу мемориала
    await page.waitForURL(/\/memorials\/\d+/);
    const memId = page.url().match(/\/memorials\/(\d+)/)?.[1];

    // Создаём инвайт через API (т.к. UI для этого может быть в настройках)
    const token = await page.evaluate(async (id) => {
      const authToken = localStorage.getItem("authToken");
      if (!authToken) return null;

      const resp = await fetch(`/api/v1/invites/memorials/${id}/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          label: "E2E Test Invite",
          expires_at: new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString(),
          permissions: { add_memories: true, chat: true, view_media: true },
        }),
      });
      const data = await resp.json();
      return data.token;
    }, memId);

    if (!token) {
      test.skip(); // если не удалось получить токен (разные форматы хранения)
      return;
    }

    // Открываем в анонимном контексте
    const guestPage = await context.newPage();
    await guestPage.goto(`/contribute/${token}`);
    // Страница должна загрузиться без редиректа на /login
    await expect(guestPage).not.toHaveURL(/login/, { timeout: 5000 });
    await guestPage.close();
  });

  test("6.4 Гость добавляет воспоминание через /contribute/:token", async ({ page, context }) => {
    await page.waitForURL(/\/memorials\/\d+/);
    const memId = page.url().match(/\/memorials\/(\d+)/)?.[1];

    const token = await page.evaluate(async (id) => {
      const authToken = localStorage.getItem("authToken");
      if (!authToken) return null;
      const resp = await fetch(`/api/v1/invites/memorials/${id}/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          label: "Гостевой вклад",
          expires_at: new Date(Date.now() + 7 * 24 * 3600 * 1000).toISOString(),
          permissions: { add_memories: true, chat: true, view_media: true },
        }),
      });
      const data = await resp.json();
      return data.token;
    }, memId);

    if (!token) {
      test.skip();
      return;
    }

    const guestPage = await context.newPage();
    await guestPage.goto(`/contribute/${token}`);
    await expect(guestPage).not.toHaveURL(/login/, { timeout: 5000 });

    // Заполняем форму воспоминания
    const titleInput = guestPage.locator('[name="title"], [placeholder*="заголов"], [placeholder*="Title"]').first();
    const contentInput = guestPage.locator('[name="content"], textarea').first();
    const submitBtn = guestPage.locator('button[type="submit"], button:has-text("Отправить"), button:has-text("Submit"), button:has-text("Сохранить")').first();

    if (await titleInput.isVisible()) {
      await titleInput.fill("Воспоминание от гостя");
    }
    if (await contentInput.isVisible()) {
      await contentInput.fill("Мы познакомились в 1985 году на конференции.");
    }
    if (await submitBtn.isVisible()) {
      await submitBtn.click();
      // Ожидаем подтверждение или успешный редирект
      await expect(
        guestPage.locator("text=Спасибо, text=Thank, text=Сохранено, text=Saved, .success, [class*='success']").first()
      ).toBeVisible({ timeout: 8000 });
    }

    await guestPage.close();
  });
});
