import { Redirect } from "expo-router";
// ASWebAuthenticationSession consumes the callback; this route handles a Router fallback.
export default function OAuthCallback() {
  return <Redirect href="/" />;
}
