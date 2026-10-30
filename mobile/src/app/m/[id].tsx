import { useLocalSearchParams, router } from "expo-router";
import { Text, View, Button } from "react-native";
import { useSession } from "../../auth/session";
import { MemorialScreen } from "../../screens/MemorialScreen";
import { AuthScreen } from "../../screens/AuthScreen";

export default function Person() {
  const { id, signin } = useLocalSearchParams<{ id: string; signin?: string }>();
  const { api, ready, user, authenticated } = useSession();
  if (!ready) return null;
  const parsed = Number(id);
  if (!Number.isSafeInteger(parsed) || parsed < 1)
    return (
      <View>
        <Text>Некорректная ссылка на страницу</Text>
        <Button title="На главную" onPress={() => router.replace("/")} />
      </View>
    );
  if (signin === "1" && !user)
    return <AuthScreen api={api} onAuthenticated={authenticated} />;
  return (
    <MemorialScreen
      key={`${parsed}:${user?.id ?? "guest"}`}
      api={api}
      id={parsed}
      onBack={() => (router.canGoBack() ? router.back() : router.replace("/"))}
      onOpen={(next) => router.push(`/m/${next}`)}
    />
  );
}
