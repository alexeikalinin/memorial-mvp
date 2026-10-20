import React, { createContext, useContext, useEffect, useState } from "react";
import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";
import { MobileApi, User, ApiError } from "../api/client";

const sessionKey = "vspomin.mobile.session";
const endpoint =
  process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000/api/v1";
// Browser preview uses memory only; native builds use Keychain/Keystore.
let webToken: string | null = null;
export const api: MobileApi = new MobileApi(endpoint, {
  get: async (): Promise<string | null> => {
    if (Platform.OS === "web") return webToken;
    const raw = await SecureStore.getItemAsync(sessionKey);
    if (!raw) return null;
    try {
      const saved = JSON.parse(raw);
      return saved.baseUrl === api.getBaseUrl() &&
        typeof saved.token === "string"
        ? saved.token
        : null;
    } catch {
      return null;
    }
  },
  set: (token) =>
    Platform.OS === "web"
      ? Promise.resolve(void (webToken = token))
      : SecureStore.setItemAsync(
          sessionKey,
          JSON.stringify({ baseUrl: api.getBaseUrl(), token }),
        ),
  clear: () =>
    Platform.OS === "web"
      ? Promise.resolve(void (webToken = null))
      : SecureStore.deleteItemAsync(sessionKey),
});
interface Session {
  api: MobileApi;
  user: User | null;
  ready: boolean;
  error: string | null;
  authenticated: () => Promise<void>;
  logout: () => Promise<void>;
  retry: () => void;
}
const Context = createContext<Session | null>(null);
export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    api.onUnauthorized = () => setUser(null);
    (async () => {
      try {
        if (Platform.OS !== "web") {
          const guest = await SecureStore.getItemAsync("vspomin.mobile.guest");
          if (guest) api.setGuestId(guest);
          else
            await SecureStore.setItemAsync(
              "vspomin.mobile.guest",
              api.getGuestId(),
            );
        }
        await api.hydrate();
        if (api.hasSession()) {
          const current = await api.me();
          if (active) setUser(current);
        }
        if (active) setError(null);
      } catch (e) {
        if (active) {
          if (e instanceof ApiError && e.status === 401) setUser(null);
          else
            setError(
              e instanceof Error ? e.message : "Не удалось восстановить сессию",
            );
        }
      } finally {
        if (active) setReady(true);
      }
    })();
    return () => {
      active = false;
      api.onUnauthorized = undefined;
    };
  }, [attempt]);
  async function authenticated() {
    setUser(await api.me());
    setError(null);
  }
  async function logout() {
    await api.logout();
    setUser(null);
    setError(null);
  }
  return (
    <Context.Provider
      value={{
        api,
        user,
        ready,
        error,
        authenticated,
        logout,
        retry: () => {
          setReady(false);
          setAttempt((n) => n + 1);
        },
      }}
    >
      {children}
    </Context.Provider>
  );
}
export function useSession() {
  const value = useContext(Context);
  if (!value) throw new Error("SessionProvider required");
  return value;
}
