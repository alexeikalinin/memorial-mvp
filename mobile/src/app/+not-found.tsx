import { Link } from "expo-router";
import { View, Text } from "react-native";
export default function NotFound() {
  return (
    <View style={{ flex: 1, justifyContent: "center", padding: 24 }}>
      <Text>Страница не найдена</Text>
      <Link href="/">Мои страницы</Link>
    </View>
  );
}
