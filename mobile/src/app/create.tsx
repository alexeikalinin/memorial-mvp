import { Redirect, router } from "expo-router";
import { useSession } from "../auth/session";
import { CreateMemorialScreen } from "../screens/CreateMemorialScreen";
export default function Create() {
  const { api, user, ready } = useSession();
  if (!ready) return null;
  if (!user) return <Redirect href="/" />;
  return (
    <CreateMemorialScreen
      api={api}
      onBack={() => router.back()}
      onCreated={(id) => router.replace(`/m/${id}`)}
    />
  );
}
