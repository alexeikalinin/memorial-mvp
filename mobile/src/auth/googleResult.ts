export const GOOGLE_RETURN_URI = "vspomin://oauth/callback";
export function googleResult(url: string, attempt: string): string {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    throw new Error("Google вернул некорректный ответ. Повторите вход.");
  }
  if (
    parsed.protocol !== "vspomin:" ||
    parsed.hostname !== "oauth" ||
    parsed.pathname !== "/callback" ||
    parsed.username ||
    parsed.password ||
    parsed.searchParams.get("attempt") !== attempt
  )
    throw new Error("Ответ Google не относится к этой попытке входа.");
  if (parsed.searchParams.has("error"))
    throw new Error("Вход через Google не завершён. Попробуйте ещё раз.");
  const code = parsed.searchParams.get("code");
  if (!code || !/^[A-Za-z0-9_-]{43}$/.test(code))
    throw new Error("Код входа недействителен. Повторите вход.");
  return code;
}
