import React from "react";
import { Alert, Linking, Platform, Text, View } from "react-native";
import type { MobileApi, User } from "../api/client";
import { Button, Row, Screen } from "../components/UI";
import { styles as s } from "../theme";
export function ProfileScreen({
  api,
  user,
  onLogout,
  onBack,
}: {
  api: MobileApi;
  user: User;
  onLogout: () => void;
  onBack: () => void;
}) {
  return (
    <Screen title="Профиль" onBack={onBack}>
      <Text style={s.title}>{user.full_name || user.username}</Text>
      <Text style={s.subtitle}>{user.email}</Text>
      <View style={s.card}>
        <Text style={s.h2}>Один семейный архив</Text>
        <Text style={s.text}>
          Сохранённые материалы доступны на сайте и в приложении с этим
          аккаунтом.
        </Text>
        <Text style={s.small}>
          Для обновления вернитесь на страницу и потяните список вниз. Черновики
          остаются на текущем экране.
        </Text>
      </View>
      <Row
        title="Аккаунт и подписка"
        body="Управление в веб-версии"
        onPress={() => void Linking.openURL(api.websiteUrl('/pricing'))}
      />
      <Row
        title="Помощь"
        body="Открыть сайт"
        onPress={() => void Linking.openURL("https://vspomin.ai")}
      />
      {__DEV__ && <Text style={s.small}>Сервер: {api.getBaseUrl()}</Text>}
      <Button
        secondary
        label="Выйти из аккаунта"
        onPress={() =>
          Platform.OS === "web"
            ? onLogout()
            : Alert.alert(
                "Выйти из аккаунта?",
                "Несохранённые черновики будут закрыты.",
                [
                  { text: "Отмена", style: "cancel" },
                  {
                    text: "Выйти",
                    onPress: onLogout,
                  },
                ],
              )
        }
      />
    </Screen>
  );
}
