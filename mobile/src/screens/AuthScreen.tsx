import React, { useState } from "react";
import { Text, View, Linking } from "react-native";
import type { MobileApi } from "../api/client";
import {
  Screen,
  Logo,
  Field,
  Button,
  ErrorText,
  message,
} from "../components/UI";
import { styles as s } from "../theme";
export function AuthScreen({
  api,
  onAuthenticated,
}: {
  api: MobileApi;
  onAuthenticated: () => void | Promise<void>;
}) {
  const [register, setRegister] = useState(false),
    [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [name, setName] = useState(""),
    [username, setUsername] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [server, setServer] = useState(api.getBaseUrl()),
    [config, setConfig] = useState(false);
  const submit = async () => {
    setError("");
    setBusy(true);
    try {
      if (register)
        await api.register(
          username.trim(),
          email.trim(),
          password,
          name.trim(),
        );
      await api.login(email.trim(), password);
      await onAuthenticated();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <Screen>
      <Logo />
      <View style={{ height: 24 }} />
      <Text style={s.title}>Истории, которые{"\n"}остаются с нами</Text>
      <Text style={s.subtitle}>
        Войдите в тот же аккаунт, что и на сайте. Ваши страницы и воспоминания
        будут рядом.
      </Text>
      {register && (
        <>
          <Field
            label="Ваше имя"
            value={name}
            onChangeText={setName}
            textContentType="name"
          />
          <Field
            label="Имя пользователя"
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
          />
        </>
      )}
      <Field
        label="Электронная почта"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
        autoComplete="email"
      />
      <Field
        label="Пароль"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        autoComplete={register ? "new-password" : "current-password"}
      />
      <ErrorText error={error} />
      <Button
        label={register ? "Создать аккаунт" : "Войти"}
        busy={busy}
        disabled={!email.trim() || !password || (register && !username.trim())}
        onPress={() => void submit()}
      />
      <Button
        secondary
        label={register ? "У меня уже есть аккаунт" : "Создать аккаунт"}
        onPress={() => {
          setRegister(!register);
          setError("");
        }}
      />
      <Text style={s.small}>
        Google-вход и восстановление пароля доступны на сайте.
      </Text>
      <Button
        secondary
        label="Открыть сайт"
        onPress={() => void Linking.openURL(api.websiteUrl('/login'))}
      />
      {__DEV__ && <Button
        secondary
        label="Настройки подключения"
        onPress={() => setConfig(!config)}
      />}
      {config && (
        <View style={s.card}>
          <Field
            label="Адрес API"
            value={server}
            onChangeText={setServer}
            autoCapitalize="none"
            autoCorrect={false}
          />
          <Text style={s.small}>
            Для локальной проверки укажите сетевой адрес компьютера, доступный
            телефону.
          </Text>
          <Button
            label="Применить адрес"
            onPress={() => {
              void (async () => {
                try {
                  await api.setBaseUrl(server.trim());
                  setConfig(false);
                  setError("");
                } catch (e) {
                  setError(message(e));
                }
              })();
            }}
          />
        </View>
      )}
    </Screen>
  );
}
