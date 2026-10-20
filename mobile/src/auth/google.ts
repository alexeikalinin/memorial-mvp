import { Platform } from "react-native";
import Constants from "expo-constants";
import * as Crypto from "expo-crypto";
import * as WebBrowser from "expo-web-browser";
import { MobileApi, ApiError } from "../api/client";
import { GOOGLE_RETURN_URI, googleResult } from "./googleResult";

export async function signInWithGoogle(api: MobileApi): Promise<boolean> {
  if (Platform.OS === "web" || Constants.executionEnvironment === "storeClient")
    throw new Error(
      "Вход через Google с возвратом в приложение доступен в собственной тестовой сборке. Expo Go и браузерный предпросмотр этот способ входа не поддерживают.",
    );
  const base = api.getBaseUrl();
  const bytes = await Crypto.getRandomBytesAsync(32);
  const verifier = Array.from(bytes, (value) =>
    value.toString(16).padStart(2, "0"),
  ).join("");
  const digest = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    verifier,
    { encoding: Crypto.CryptoEncoding.BASE64 },
  );
  const challenge = digest
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
  let start;
  try {
    start = await api.startGoogle(challenge);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404)
      throw new Error(
        "На сервере ещё не опубликовано дополнение для мобильного Google-входа.",
      );
    throw error;
  }
  // Never open an arbitrary URL supplied by a misconfigured server.
  const authorization = new URL(start.authorization_url);
  if (
    authorization.protocol !== "https:" ||
    authorization.hostname !== "accounts.google.com" ||
    authorization.pathname !== "/o/oauth2/v2/auth"
  )
    throw new Error("Сервер вернул некорректный адрес Google-входа.");
  const result = await WebBrowser.openAuthSessionAsync(
    start.authorization_url,
    GOOGLE_RETURN_URI,
  );
  if (result.type !== "success") return false;
  if (api.getBaseUrl() !== base)
    throw new Error("Сервер изменился во время входа. Повторите вход.");
  const code = googleResult(result.url, start.attempt_id);
  await api.completeGoogle(start.attempt_id, verifier, code);
  return true;
}
