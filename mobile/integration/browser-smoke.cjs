/** Run after preview_server.py, frontend at 5188 and mobile web export served at 8081. */
const { chromium, expect } = require("../../e2e/node_modules/@playwright/test");
const fs = require("node:fs");
const path = require("node:path");
const out = path.join(__dirname, "../qa");
fs.mkdirSync(out, { recursive: true });
(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const mobile = await context.newPage();
  const web = await context.newPage();
  await mobile.setViewportSize({ width: 390, height: 844 });
  await web.setViewportSize({ width: 1280, height: 900 });
  mobile.setDefaultTimeout(15000);
  web.setDefaultTimeout(15000);
  const errors = [];
  for (const page of [mobile, web])
    page.on("pageerror", (e) => errors.push(e.message));
  try {
    await expect
      .poll(
        async () => {
          try {
            return (
              await context.request.get("http://127.0.0.1:8000/")
            ).status();
          } catch {
            return 0;
          }
        },
        { timeout: 60000 },
      )
      .toBe(200);
    await mobile.goto("http://localhost:8081/");
    await mobile.getByLabel("Электронная почта").fill("mobile-qa@example.com");
    await mobile.getByLabel("Пароль", { exact: true }).fill("MobileTest123!");
    await mobile.getByRole("button", { name: "Войти", exact: true }).click();
    await expect(
      mobile.getByText("Мои страницы", { exact: true }),
    ).toBeVisible();
    console.log("mobile login ready");
    await mobile.screenshot({
      path: path.join(out, "mobile-home.png"),
      fullPage: true,
    });
    await mobile
      .getByRole("button", { name: "+ Создать страницу", exact: true })
      .click();
    const name = "Михаил Соколов · проверка " + Date.now();
    await mobile.getByLabel("Имя и фамилия").fill(name);
    await mobile
      .getByRole("button", { name: "Создать страницу", exact: true })
      .click();
    await expect(
      mobile.getByRole("button", {
        name: "+ Добавить воспоминание",
        exact: true,
      }),
    ).toBeVisible();
    console.log("page created");
    const mid = Number(new URL(mobile.url()).pathname.split("/").at(-1));
    if (!Number.isSafeInteger(mid))
      throw new Error("Missing created memorial id");
    await mobile
      .getByRole("button", { name: "+ Добавить воспоминание", exact: true })
      .click();
    await mobile.getByLabel("Название · необязательно").fill("Из приложения");
    const nativeText =
      "Воспоминание создано в мобильном интерфейсе " + Date.now();
    await mobile
      .getByLabel("Ваше воспоминание", { exact: true })
      .fill(nativeText);
    console.log("saving mobile memory");
    await mobile
      .getByRole("button", { name: "Сохранить", exact: true })
      .click();
    await expect(mobile.getByText(nativeText, { exact: true })).toBeVisible();
    console.log("mobile memory saved; login web");
    await web.goto("http://localhost:5188/login");
    await web.locator('input[name="email"]').fill("mobile-qa@example.com");
    await web.locator('input[name="password"]').fill("MobileTest123!");
    await web.locator('form button[type="submit"]').click();
    await web.waitForURL((url) => !url.pathname.includes("login"));
    console.log("web login ready");
    await web.goto(`http://localhost:5188/memorials/${mid}`);
    // Dismiss tutorial locally; it is unrelated to the transport check.
    await web.evaluate(() => {
      for (const key of [
        "tutorialSeen",
        "tutorialCompleted",
        "hasSeenTutorial",
      ])
        localStorage.setItem(key, "true");
    });
    console.log("web page loaded");
    await web.locator('[data-tour="tab-memories"]').click();
    await expect(web.getByText(nativeText, { exact: true })).toBeVisible();
    await web.locator('[data-tour="memories-add"]').click();
    const webText = "Воспоминание создано на сайте " + Date.now();
    await web.locator("#content").fill(webText);
    await web.locator('.memory-form button[type="submit"]').click();
    await expect(web.getByText(webText, { exact: true })).toBeVisible();
    await web.screenshot({
      path: path.join(out, "web-shared-memories.png"),
      fullPage: true,
    });
    // Refocus triggers foreground refresh; no browser storage/token is shared.
    await mobile.getByRole("button", { name: "Назад", exact: true }).click();
    await mobile.getByRole("button", { name: "Назад", exact: true }).click();
    await expect(
      mobile.getByText("Мои страницы", { exact: true }),
    ).toBeVisible();
    await mobile.getByRole("button").filter({ hasText: name }).click();
    await expect(
      mobile.getByRole("button", {
        name: "+ Добавить воспоминание",
        exact: true,
      }),
    ).toBeVisible();
    await mobile
      .getByRole("button", { name: /^Воспоминания/ })
      .click();
    await expect(mobile.getByText(webText, { exact: true })).toBeVisible();
    await mobile.screenshot({
      path: path.join(out, "mobile-shared-memories.png"),
      fullPage: true,
    });
    // Upload via actual RN-Web document picker, then render the same photo on the website.
    await mobile.getByRole("button", { name: "Назад", exact: true }).click();
    await mobile.getByRole("button", { name: /^Фото и записи/ }).click();
    const chooser = mobile.waitForEvent('filechooser');
    await mobile.getByRole('button', {name:'Выбрать аудио или файл',exact:true}).click();
    const uploadResponse = mobile.waitForResponse(r=>r.url().includes('/media/upload')&&r.request().method()==='POST');
    await (await chooser).setFiles({name:'mobile-family-photo.png',mimeType:'image/png',buffer:fs.readFileSync(path.join(__dirname,'../assets/icon.png'))});
    const uploaded=await (await uploadResponse).json();
    await expect(mobile.getByText('mobile-family-photo.png',{exact:true})).toBeVisible();
    await web.reload();
    await expect(web.getByAltText("mobile-family-photo.png",{exact:true})).toBeVisible();
    if (!uploaded.id) throw new Error("Missing uploaded media id");
    await mobile.screenshot({path:path.join(out,'mobile-materials.png'),fullPage:true});
    await mobile.getByRole("button", { name: "Назад", exact: true }).click();
    await mobile
      .getByRole("button", { name: /^Разговор по воспоминаниям/ })
      .click();
    await mobile.getByLabel("Ваш вопрос").fill("Проверка общего сервера");
    await mobile
      .getByRole("button", { name: "Отправить", exact: true })
      .click();
    await expect(mobile.getByText(/Тест связи: мобильный чат|Проверка: история найдена/)).toBeVisible();
    await mobile.getByRole('button',{name:'Назад',exact:true}).click();
    await mobile.getByRole('button',{name:'Назад',exact:true}).click();
    await expect(mobile.getByText('Мои страницы',{exact:true})).toBeVisible();
    await mobile.setViewportSize({width:320,height:780});
    if(await mobile.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth))throw new Error('320px overflow');
    await mobile.setViewportSize({width:390,height:844});
    await mobile.screenshot({path:path.join(out,'mobile-home.png'),fullPage:true});
    await mobile.getByRole('button',{name:'Открыть профиль',exact:true}).click();
    await mobile.getByRole('button',{name:'Выйти из аккаунта',exact:true}).click();
    await expect(mobile.getByRole('button',{name:'Войти',exact:true})).toBeVisible();
    await web.reload();
    await expect(web.getByAltText('mobile-family-photo.png',{exact:true})).toBeVisible();
    if (errors.length) throw new Error(errors.join("\n"));
    console.log(
      JSON.stringify({
        ok: true,
        mid,
        checks: [
          "mobile login",
          "create page",
          "mobile memory → web UI",
          "web memory → mobile UI",
          "mobile photo picker/upload → web gallery",
          "shared chat transport (AI stub)",
          "no browser runtime errors",
          "320px responsive layout",
          "mobile logout leaves independent web session intact",
        ],
        screenshots: out,
      }),
    );
  } catch (error) {
    console.error(error);
    for (const [name, page] of [
      ["mobile", mobile],
      ["web", web],
    ]) {
      console.error(
        name,
        await page
          .locator("body")
          .innerText({ timeout: 2000 })
          .catch(() => ""),
      );
      await page
        .screenshot({
          path: path.join(out, name + "-failure.png"),
          fullPage: true,
          timeout: 5000,
        })
        .catch(() => {});
    }
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();
