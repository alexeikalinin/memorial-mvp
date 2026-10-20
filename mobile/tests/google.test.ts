import { test } from "node:test";
import assert from "node:assert/strict";
import { googleResult, GOOGLE_RETURN_URI } from "../src/auth/googleResult";
const code = "x".repeat(43);
const attempt = "y".repeat(43);
test("Google callback matches original attempt and returns only a one-use handoff code", () =>
  assert.equal(
    googleResult(
      `${GOOGLE_RETURN_URI}?attempt=${attempt}&code=${code}`,
      attempt,
    ),
    code,
  ));
test("wrong origin, scheme, attempt, error or malformed handoff cannot start a session", () => {
  for (const url of [
    `https://evil.example/oauth/callback?attempt=${attempt}&code=${code}`,
    `vspomin://evil/callback?attempt=${attempt}&code=${code}`,
    `${GOOGLE_RETURN_URI}?attempt=wrong&code=${code}`,
    `${GOOGLE_RETURN_URI}?attempt=${attempt}&error=denied`,
    `${GOOGLE_RETURN_URI}?attempt=${attempt}&code=short`,
  ])
    assert.throws(() => googleResult(url, attempt));
});
