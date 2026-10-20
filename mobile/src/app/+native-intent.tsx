import { memorialPath } from "../navigation/links";
export function redirectSystemPath({
  path,
}: {
  path: string;
  initial: boolean;
}) {
  try {
    const url = new URL(path);
    if (
      url.protocol === "vspomin:" &&
      url.hostname === "oauth" &&
      url.pathname === "/callback"
    )
      return "/oauth/callback";
  } catch {
    /* Internal paths are handled below. */
  }
  const memorial = memorialPath(path);
  if (memorial) return memorial;
  // Keep internal Router / Expo development paths intact; malformed external links go home.
  if (path.startsWith("/") && !path.startsWith("//")) return path;
  return "/";
}
