/**
 * Общие хелперы для E2E тестов
 */

const TEST_USER = {
  email: `e2e_${Date.now()}@test.com`,
  username: `e2euser_${Date.now()}`,
  fullName: "E2E Test User",
  password: "e2epassword123",
};

/**
 * Регистрирует нового пользователя через UI и возвращает его данные.
 */
export async function registerUser(page, user = TEST_USER) {
  await page.goto("/register");
  await page.fill('[name="email"], input[type="email"]', user.email);
  await page.fill('[name="username"]', user.username);
  await page.fill('[name="full_name"], [name="fullName"]', user.fullName);
  await page.fill('[name="password"], input[type="password"]', user.password);
  await page.click('button[type="submit"]');
  await page.waitForURL("/");
  return user;
}

/**
 * Логинит пользователя через UI.
 */
export async function loginUser(page, email, password) {
  await page.goto("/login");
  await page.fill('[name="email"], input[type="email"]', email);
  await page.fill('[name="password"], input[type="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL("/");
}

/**
 * Создаёт мемориал через UI и возвращает его ID из URL.
 */
export async function createMemorial(page, name = "E2E Test Memorial") {
  await page.goto("/memorials/new");
  await page.fill('[name="name"]', name);
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/memorials\/\d+/);
  const url = page.url();
  const id = url.match(/\/memorials\/(\d+)/)?.[1];
  return { id, name };
}

/**
 * Генерирует уникальный email для тестов.
 */
export function uniqueEmail() {
  return `test_${Date.now()}_${Math.random().toString(36).slice(2)}@example.com`;
}

export function uniqueUsername() {
  return `user_${Date.now()}_${Math.random().toString(36).slice(2)}`;
}
