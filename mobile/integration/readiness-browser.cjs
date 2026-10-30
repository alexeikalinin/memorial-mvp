/** Synthetic UI audit. Requires readiness_server.py, Vite :5188 and Expo web :8081. */
const {chromium,expect}=require('../../e2e/node_modules/@playwright/test');
const fs=require('node:fs');const path=require('node:path');
const out=path.resolve('artifacts/mobile-readiness-2026-10-30');fs.mkdirSync(out,{recursive:true});
(async()=>{const browser=await chromium.launch();const ctx=await browser.newContext();const p=await ctx.newPage();p.setDefaultTimeout(12000);const errors=[];p.on('pageerror',e=>errors.push(e.message));
try{
 await p.setViewportSize({width:390,height:844});await p.goto('http://localhost:8081');
 await p.getByLabel('Электронная почта').fill('mobile-qa@example.com');await p.getByLabel('Пароль',{exact:true}).fill('MobileTest123!');await p.getByRole('button',{name:'Войти',exact:true}).click();
 await expect(p.getByText('Мои страницы',{exact:true})).toBeVisible();
 console.log('HOME',await p.locator('body').innerText());
 await p.getByRole('button').filter({hasText:'Соколова Александра'}).click();
 await expect(p.getByRole('button',{name:/^Воспоминания/})).toBeVisible();console.log('OVERVIEW',await p.locator('body').innerText());await p.screenshot({path:path.join(out,'overview-390.png'),fullPage:true});
 for(const width of [320,430,768]){await p.setViewportSize({width,height:900});await expect.poll(()=>p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await p.screenshot({path:path.join(out,`overview-${width}.png`),fullPage:true});}
 await p.setViewportSize({width:390,height:844});
 for(const name of [/^Родные/,/^История жизни/,/^Фото и записи/,/^Воспоминания/]){
 await p.getByRole('button',{name}).click();await p.waitForTimeout(350);console.log(String(name),await p.locator('body').innerText());await p.screenshot({path:path.join(out,`${String(name).replace(/[^а-яa-z]/gi,'')}-390.png`),fullPage:true});await p.getByRole('button',{name:'Назад',exact:true}).click();}
 const web=await ctx.newPage();const login=await ctx.request.post('http://127.0.0.1:8000/api/v1/auth/login',{data:{email:'mobile-qa@example.com',password:'MobileTest123!'}});const token=(await login.json()).access_token;
 await web.goto('http://localhost:5188/login');await web.evaluate(t=>localStorage.setItem('authToken',t),token);
 for(const route of ['/memorials/1','/m/3'])for(const width of [1280,768,430,390,320]){
 await web.setViewportSize({width,height:900});await web.goto('http://localhost:5188'+route);await web.locator('.appearance-display-name').waitFor();await web.evaluate(()=>document.fonts.ready);await web.waitForTimeout(300);
 const audit=await web.evaluate(()=>{const box=s=>{const r=document.querySelector(s)?.getBoundingClientRect();return r&&{left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height}};return {hero:box('.memorial-hero,.public-hero'),name:box('.appearance-item-name'),portrait:box('.memorial-hero-img,.memorial-hero-empty,.public-portrait-wrap'),dates:box('.appearance-item-dates'),quote:box('.appearance-item-quote'),nameStyle:getComputedStyle(document.querySelector('.appearance-display-name')).overflowWrap,datesText:document.querySelector('.appearance-display-dates').textContent,overflow:document.documentElement.scrollWidth>innerWidth}});
 console.log('HERO',route,width,JSON.stringify(audit));expect(audit.overflow).toBe(false);expect(audit.nameStyle).toBe('normal');expect(audit.name.left).toBeGreaterThanOrEqual(audit.portrait.right+8);expect(audit.quote.left).toBeGreaterThanOrEqual(audit.hero.left);expect(audit.name.top).toBeGreaterThanOrEqual(audit.hero.top);expect(audit.name.right).toBeLessThanOrEqual(audit.hero.right+1);expect(audit.dates.top).toBeGreaterThanOrEqual(audit.portrait.bottom);expect(Math.abs((audit.dates.left+audit.dates.right-audit.portrait.left-audit.portrait.right)/2)).toBeLessThan(2);
 await web.screenshot({path:path.join(out,`hero-${route.includes('memorials')?'owner':'public'}-${width}.png`),fullPage:true});
 }
 if(errors.length)throw Error(errors.join('\n'));console.log('READINESS PASS');
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
