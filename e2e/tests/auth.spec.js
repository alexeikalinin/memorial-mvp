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

    // Должны попасть на главную (Supabase cold connection может занять до 25с)
    await page.waitForURL("/", { timeout: 30000 });
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
    await page.waitForURL("/", { timeout: 20000 });

    // Выходим (ждём кнопку до 5s)
    const logoutBtn = page.locator("[data-testid='logout-btn']").first();
    await logoutBtn.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {});
    if (await logoutBtn.isVisible()) await logoutBtn.click();

    // Входим
    await page.goto("/login");
    await page.fill('[name="email"], input[type="email"]', email);
    await page.fill('[name="password"], input[type="password"]', "testpassword123");
    await page.click('button[type="submit"]');
    await page.waitForURL("/", { timeout: 20000 });
    await expect(page).toHaveURL("/");
  });

  test("1.5 Вход с неверным паролем", async ({ page }) => {
    await page.goto("/login");
    await page.fill('[name="email"], input[type="email"]', "nobody@example.com");
    await page.fill('[name="password"], input[type="password"]', "wrongpassword");
    await page.click('button[type="submit"]');

    // Должна появиться ошибка (ждём ответ Supabase до 20с)
    await expect(page.locator(".auth-error, .error, .alert, [role='alert']")).toBeVisible({ timeout: 20000 });
    // Остаёмся на /login
    expect(page.url()).toContain("/login");
  });

  test("1.8 Защищённый роут без логина → редирект на /login", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/login/, { timeout: 5000 });
  });

  test("1.9 Выход из аккаунта → редирект на /login", async ({ page }) => {
    await page.goto("/register");
    await page.fill('[name="email"], input[type="email"]', uniqueEmail());
    await page.fill('[name="username"]', uniqueUsername());
    await page.fill('[name="full_name"], [name="fullName"]', "Logout User");
    await page.fill('[name="password"], input[type="password"]', "logoutpass123");
    await page.click('button[type="submit"]');
    await page.waitForURL("/", { timeout: 20000 });

    const logoutBtn = page.locator("[data-testid='logout-btn']").first();
    await expect(logoutBtn).toBeVisible({ timeout: 8000 });
    await logoutBtn.click();

    await expect(page).toHaveURL(/login/, { timeout: 8000 });
  });
});
