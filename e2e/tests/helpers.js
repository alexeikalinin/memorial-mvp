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
  await page.waitForURL("/", { timeout: 40000 });
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
  await page.waitForURL("/", { timeout: 40000 });
}

/**
 * Создаёт мемориал через UI и возвращает его ID из URL.
 */
export async function createMemorial(page, name = "E2E Test Memorial") {
  await page.goto("/memorials/new");
  await page.fill('[name="name"]', name);
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/memorials\/\d+/, { timeout: 40000 });
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

/**
 * Удаляет тестового пользователя и все его данные через API.
 * Вызывать в afterAll для очистки базы.
 */
export async function cleanupTestUser(page) {
  try {
    const token = await page.evaluate(() => localStorage.getItem('authToken'));
    if (!token) return;
    await page.evaluate(async (t) => {
      // Удаляем все свои мемориалы
      const list = await fetch('/api/v1/memorials/', { headers: { Authorization: `Bearer ${t}` } });
      const memorials = await list.json();
      for (const m of (Array.isArray(memorials) ? memorials : [])) {
        await fetch(`/api/v1/memorials/${m.id}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${t}` },
        }).catch(() => {});
      }
      // Удаляем аккаунт
      await fetch('/api/v1/auth/me', {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${t}` },
      }).catch(() => {});
    }, token);
  } catch { /* best effort */ }
}
