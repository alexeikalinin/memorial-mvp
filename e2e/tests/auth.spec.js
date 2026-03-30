import { test, expect } from "@playwright/test";
import { uniqueEmail, uniqueUsername } from "./helpers.js";

test.describe("Аутентификация", () => {
  test("1.1 Регистрация с валидными данными", async ({ page }) => {
    const email = uniqueEmail();
    const username = uniqueUsername();

    await page.goto("/register");
    await page.fill('[name="email"], input[type="email"]', email);
    await page.fill('[name="username"]', username);
    await page.fill('[name="full_name"], [name="fullName"]', "Test User");
    await page.fill('[name="password"], input[type="password"]', "testpassword123");
    await page.click('button[type="submit"]');

    // Должны попасть на главную
    await page.waitForURL("/", { timeout: 10000 });
    await expect(page).toHaveURL("/");
  });

  test("1.4 Вход с правильными credentials", async ({ page }) => {
    const email = uniqueEmail();
    const username = uniqueUsername();

    // Сначала регистрируемся
    await page.goto("/register");
    await page.fill('[name="email"], input[type="email"]', email);
    await page.fill('[name="username"]', username);
    await page.fill('[name="full_name"], [name="fullName"]', "Test User");
    await page.fill('[name="password"], input[type="password"]', "testpassword123");
    await page.click('button[type="submit"]');
    await page.waitForURL("/");

    // Выходим
    const logoutBtn = page.locator("text=Выйти, text=Logout, button:has-text('Logout'), button:has-text('Выйти')").first();
    if (await logoutBtn.isVisible()) await logoutBtn.click();

    // Входим
    await page.goto("/login");
    await page.fill('[name="email"], input[type="email"]', email);
    await page.fill('[name="password"], input[type="password"]', "testpassword123");
    await page.click('button[type="submit"]');
    await page.waitForURL("/");
    await expect(page).toHaveURL("/");
  });

  test("1.5 Вход с неверным паролем", async ({ page }) => {
    await page.goto("/login");
    await page.fill('[name="email"], input[type="email"]', "nobody@example.com");
    await page.fill('[name="password"], input[type="password"]', "wrongpassword");
    await page.click('button[type="submit"]');

    // Должна появиться ошибка
    await expect(page.locator(".error, .alert, [role='alert']")).toBeVisible({ timeout: 5000 });
    // Остаёмся на /login
    expect(page.url()).toContain("/login");
  });

  test("1.8 Защищённый роут без логина → редирект на /login", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/login/, { timeout: 5000 });
  });
});
