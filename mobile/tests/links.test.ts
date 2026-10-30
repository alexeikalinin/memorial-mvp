import {test} from 'node:test';
import assert from 'node:assert/strict';
import {memorialPath} from '../src/navigation/links';
import {MobileApi} from '../src/api/client';
test('existing website QR and native dev links resolve to same person',()=>{for(const link of ['https://vspomin.ai/app/m/319#chat','https://vspomin.ai/m/319','vspomin:///m/319','vspomin://m/319','/app/m/319'])assert.equal(memorialPath(link),'/m/319');});
test('untrusted and malformed deep links cannot rewrite app routes',()=>{for(const link of ['https://evil.example/m/319','https://vspomin.ai.evil.example/m/319','https://user:pw@vspomin.ai/m/319','//evil.example/m/319','/m/0','/m/9007199254740992','/m/abc'])assert.equal(memorialPath(link),null);});
test('shared URLs point to deployed SPA under /app, not the landing page',()=>{const api=new MobileApi('https://api.example/api/v1',{get:async()=>null,set:async()=>{},clear:async()=>{}});assert.equal(api.publicPageUrl(319),'https://vspomin.ai/app/m/319');assert.equal(api.websiteUrl('/memorials/319'),'https://vspomin.ai/app/memorials/319');});
test('production-root configuration keeps invitation links inside the deployed SPA',()=>{const previous=process.env.EXPO_PUBLIC_WEB_URL;try{process.env.EXPO_PUBLIC_WEB_URL='https://vspomin.ai';const api=new MobileApi('https://api.example/api/v1',{get:async()=>null,set:async()=>{},clear:async()=>{}});assert.equal(api.websiteUrl('/contribute/invite'),'https://vspomin.ai/app/contribute/invite');}finally{if(previous===undefined)delete process.env.EXPO_PUBLIC_WEB_URL;else process.env.EXPO_PUBLIC_WEB_URL=previous;}});
