import { test } from "node:test";
import assert from "node:assert/strict";
import {
  MobileApi,
  ApiError,
  normalizeBaseUrl,
  type TokenStore,
} from "../src/api/client";

function harness(
  handler: (url: string, init: RequestInit) => Response | Promise<Response>,
) {
  let token: string | null = null;
  const store: TokenStore = {
    get: async () => token,
    set: async (value) => {
      token = value;
    },
    clear: async () => {
      token = null;
    },
  };
  const api = new MobileApi("https://api.example/api/v1", store, ((url, init) =>
    handler(String(url), init || {})) as typeof fetch);
  return { api, token: () => token };
}
const json = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });

test("native login and JSON uploads use the SAME web API contract", async () => {
  const calls: { url: string; init: RequestInit }[] = [];
  const { api, token } = harness((url, init) => {
    calls.push({ url, init });
    return url.endsWith("/auth/login")
      ? json({
          access_token: "test-jwt",
          user: { id: 1, email: "test@example.com" },
        })
      : json({ id: 42, content: "История" });
  });
  await api.login("test@example.com", "password");
  await api.createMemory(7, { content: "История" });
  assert.equal(token(), "test-jwt");
  assert.equal(calls[0].url, "https://api.example/api/v1/auth/login");
  assert.equal(calls[1].url, "https://api.example/api/v1/memorials/7/memories");
  assert.equal(
    new Headers(calls[1].init.headers).get("Authorization"),
    "Bearer test-jwt",
  );
  assert.deepEqual(JSON.parse(calls[1].init.body as string), {
    content: "История",
  });
});

test("my pages excludes public pages without ACL and preserves shared viewer pages", async () => {
  const { api } = harness((url) =>
    url.endsWith("/memorials/")
      ? json([
          { id: 1, name: "Own" },
          { id: 2, name: "Public" },
          { id: 3, name: "Shared" },
        ])
      : json({
          id: Number(url.split("/").at(-1)),
          current_user_role: url.endsWith("/1")
            ? "owner"
            : url.endsWith("/3")
              ? "viewer"
              : null,
        }),
  );
  assert.deepEqual(
    (await api.listMemorials()).map((p) => p.id),
    [1, 3],
  );
});

test("switching endpoint clears credentials before sending requests", async () => {
  let authorization: string | null = null;
  const { api, token } = harness((url, init) => {
    authorization = new Headers(init.headers).get("Authorization");
    return url.endsWith("login")
      ? json({ access_token: "old", user: { id: 1 } })
      : json({ id: 2 });
  });
  await api.login("x@example.com", "password");
  await api.setBaseUrl("https://another.example/api/v1");
  await api.me();
  assert.equal(token(), null);
  assert.equal(authorization, null);
});

test("401 clears saved session, 403 does not log out the user", async () => {
  let status = 403;
  let expired = 0;
  const { api, token } = harness((url) =>
    url.endsWith("login")
      ? json({ access_token: "saved", user: { id: 1 } })
      : json({ detail: "Denied" }, status),
  );
  await api.login("x@example.com", "password");
  api.onUnauthorized = () => {
    expired++;
  };
  await assert.rejects(api.me(), (e: ApiError) => e.status === 403);
  assert.equal(token(), "saved");
  status = 401;
  await assert.rejects(api.me(), (e: ApiError) => e.status === 401);
  assert.equal(token(), null);
  assert.equal(expired, 1);
});

test("multipart retains browser Blob filename, leaves boundary to fetch", async () => {
  let captured: RequestInit = {};
  const { api } = harness((_, init) => {
    captured = init;
    return json({ id: 8 });
  });
  await api.uploadMedia(7, {
    uri: "blob:test",
    name: "семья.wav",
    mimeType: "audio/wav",
    file: new Blob(["audio"], { type: "audio/wav" }),
  });
  assert.ok(captured.body instanceof FormData);
  assert.equal((captured.body.get("file") as File).name, "семья.wav");
  assert.equal(new Headers(captured.headers).get("Content-Type"), null);
});

test("network failure never masquerades as empty data", async () => {
  const { api } = harness(() => {
    throw new Error("offline");
  });
  await assert.rejects(
    api.listMemories(1),
    (e: ApiError) => e.status === 0 && e.message.includes("сервером"),
  );
});

test("remote cleartext, URL credentials and query strings are rejected", () => {
  for (const value of [
    "http://example.com",
    "https://user:password@example.com",
    "https://example.com?token=x",
    "file:///etc/passwd",
  ])
    assert.throws(() => normalizeBaseUrl(value));
  assert.equal(
    normalizeBaseUrl("http://10.0.2.2:8000/"),
    "http://10.0.2.2:8000/api/v1",
  );
});

test("late request after logout cannot return previous account private data", async () => {
  let resolve!: (value: Response) => void;
  const { api } = harness((url) =>
    url.endsWith("login")
      ? json({ access_token: "old", user: { id: 1 } })
      : new Promise((r) => {
          resolve = r;
        }),
  );
  await api.login("x@example.com", "password");
  const request = api.getMemorial(1);
  await api.logout();
  resolve(json({ name: "Private old data" }));
  await assert.rejects(request, (e: ApiError) => e.status === 401);
});

test("contribution invites default to add-only and reuse a valid matching link", async () => {
  const calls: {url: string; init: RequestInit}[] = [];
  const existing = {token: "existing", invite_url: "https://vspomin.ai/app/contribute/existing", permissions: {add_memories: true, chat: false, view_media: false}};
  const {api} = harness((url, init) => {calls.push({url,init});return url.endsWith('/list') ? json([existing]) : json({token: 'new', ...JSON.parse(String(init.body))});});
  assert.equal((await api.invite(7)).token, 'existing');
  assert.equal(calls.length, 1);
  await api.invite(7, true);
  const create = calls.find(call => call.url.endsWith('/create'))!;
  assert.deepEqual(JSON.parse(String(create.init.body)), {expires_days: 30, permissions: {add_memories: true, chat: true, view_media: false}});
});

test('memory edits/deletion and family chat use existing server contracts',async()=>{
 const calls:{url:string;init:RequestInit}[]=[];
 const {api}=harness((url,init)=>{calls.push({url,init});return json({id:12})});
 await api.updateMemory(7,12,{content:'Исправленная история',event_date:null});
 await api.deleteMemory(7,12);
 await api.chat(7,'Кто был в семье?',true,true);
 assert.equal(calls[0].init.method,'PATCH');
 assert.equal(calls[0].url,'https://api.example/api/v1/memorials/7/memories/12');
 assert.equal(JSON.parse(calls[0].init.body as string).event_date,null);
 assert.equal(calls[1].init.method,'DELETE');
 const body=JSON.parse(calls[2].init.body as string);
 assert.equal(body.include_family_memories,true);assert.equal(body.include_audio,true);
});
