/** Encode decoded microphone samples as a mono PCM16 WAV accepted by the API. */
export function encodeMonoWav(
  channels: readonly Float32Array[],
  sampleRate: number,
): ArrayBuffer {
  const frames = channels[0]?.length || 0;
  if (
    !frames ||
    !Number.isInteger(sampleRate) ||
    sampleRate <= 0 ||
    channels.some((channel) => channel.length !== frames)
  ) {
    throw new Error(
      "Не удалось прочитать запись голоса. Попробуйте записать её ещё раз.",
    );
  }
  const buffer = new ArrayBuffer(44 + frames * 2);
  const view = new DataView(buffer);
  const text = (offset: number, value: string) => {
    for (let i = 0; i < value.length; i++)
      view.setUint8(offset + i, value.charCodeAt(i));
  };
  text(0, "RIFF");
  view.setUint32(4, 36 + frames * 2, true);
  text(8, "WAVE");
  text(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  text(36, "data");
  view.setUint32(40, frames * 2, true);
  for (let frame = 0; frame < frames; frame++) {
    let sample = 0;
    for (const channel of channels) sample += channel[frame] / channels.length;
    sample = Number.isFinite(sample) ? Math.max(-1, Math.min(1, sample)) : 0;
    view.setInt16(
      44 + frame * 2,
      Math.round(sample * (sample < 0 ? 32768 : 32767)),
      true,
    );
  }
  return buffer;
}
interface DecodedAudio {
  numberOfChannels: number;
  sampleRate: number;
  getChannelData(channel: number): Float32Array;
}
interface BrowserAudioContext {
  decodeAudioData(data: ArrayBuffer): Promise<DecodedAudio>;
  close(): Promise<void>;
}
/** Browser-only conversion; native HIGH_QUALITY already records AAC in MP4. */
export async function recordingToWav(uri: string): Promise<Blob> {
  const Context =
    (
      globalThis as unknown as {
        AudioContext?: new () => BrowserAudioContext;
        webkitAudioContext?: new () => BrowserAudioContext;
      }
    ).AudioContext ||
    (
      globalThis as unknown as {
        webkitAudioContext?: new () => BrowserAudioContext;
      }
    ).webkitAudioContext;
  if (!Context)
    throw new Error(
      "Браузер не поддерживает обработку записи голоса. Используйте приложение на телефоне.",
    );
  const context = new Context();
  try {
    const response = await fetch(uri);
    if (!response.ok) throw new Error("Не удалось прочитать запись голоса.");
    const decoded = await context.decodeAudioData(await response.arrayBuffer());
    const channels = Array.from(
      { length: decoded.numberOfChannels },
      (_, index) => decoded.getChannelData(index),
    );
    return new Blob([encodeMonoWav(channels, decoded.sampleRate)], {
      type: "audio/wav",
    });
  } finally {
    await context.close();
  }
}
