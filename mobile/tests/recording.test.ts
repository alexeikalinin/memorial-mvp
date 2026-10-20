import { test } from "node:test";
import assert from "node:assert/strict";
import { encodeMonoWav } from "../src/media/recording";
test("browser microphone becomes valid PCM16 mono WAV accepted by existing backend", () => {
  const buffer = encodeMonoWav(
    [new Float32Array([-1, 0, 1]), new Float32Array([-1, 0, 1])],
    16000,
  );
  const view = new DataView(buffer);
  const text = (n: number, len: number) =>
    String.fromCharCode(...new Uint8Array(buffer, n, len));
  assert.equal(text(0, 4), "RIFF");
  assert.equal(text(8, 4), "WAVE");
  assert.equal(view.getUint16(22, true), 1);
  assert.equal(view.getUint32(24, true), 16000);
  assert.equal(view.getUint32(40, true), 6);
  assert.equal(view.getInt16(44, true), -32768);
  assert.equal(view.getInt16(48, true), 32767);
});
test("invalid microphone data fails before upload", () => {
  assert.throws(() => encodeMonoWav([], 16000));
  assert.throws(() => encodeMonoWav([new Float32Array(1)], 0));
  assert.throws(() =>
    encodeMonoWav([new Float32Array(1), new Float32Array(2)], 16000),
  );
});
