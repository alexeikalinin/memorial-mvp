import { router } from "expo-router";
import { ActivityIndicator, Text, View, Button } from "react-native";
import { useSession } from "../auth/session";
import { AuthScreen } from "../screens/AuthScreen";
import { MemorialListScreen } from "../screens/MemorialListScreen";

export default function Home() {
  const session = useSession();
  if (!session.ready)
    return (
      <View style={{ flex: 1, justifyContent: "center" }}>
        <ActivityIndicator accessibilityLabel="Загрузка аккаунта" />
      </View>
    );
  if (session.error && session.api.hasSession())
    return (
      <View style={{ flex: 1, justifyContent: "center", padding: 24 }}>
        <Text>{session.error}</Text>
        <Button title="Повторить" onPress={session.retry} />
        <Button title="Войти заново" onPress={() => void session.logout()} />
      </View>
    );
  if (!session.user)
    return (
      <AuthScreen api={session.api} onAuthenticated={session.authenticated} />
    );
  return (
    <MemorialListScreen
      api={session.api}
      user={session.user}
      onOpen={(id) => router.push(`/m/${id}`)}
      onCreate={() => router.push("/create")}
      onProfile={() => router.push("/profile")}
    />
  );
}
