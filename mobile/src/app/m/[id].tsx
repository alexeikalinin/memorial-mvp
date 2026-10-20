import { useLocalSearchParams, router } from "expo-router";
import { Text, View, Button } from "react-native";
import { useSession } from "../../auth/session";
import { MemorialScreen } from "../../screens/MemorialScreen";

export default function Person() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { api, ready, user } = useSession();
  if (!ready) return null;
  const parsed = Number(id);
  if (!Number.isSafeInteger(parsed) || parsed < 1)
    return (
      <View>
        <Text>Некорректная ссылка на страницу</Text>
        <Button title="На главную" onPress={() => router.replace("/")} />
      </View>
    );
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
