import { Redirect, router } from "expo-router";
import { useSession } from "../auth/session";
import { ProfileScreen } from "../screens/ProfileScreen";
export default function Profile() {
  const { api, user, ready, logout } = useSession();
  if (!ready) return null;
  if (!user) return <Redirect href="/" />;
  return (
    <ProfileScreen
      api={api}
      user={user}
      onBack={() => router.back()}
      onLogout={async () => {
        await logout();
        router.replace("/");
      }}
    />
  );
}
