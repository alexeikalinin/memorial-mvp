import React, { useCallback, useRef, useState } from "react";
import {
  AppState,
  Image,
  Pressable,
  Text,
  TextInput,
  View,
} from "react-native";
import { useFocusEffect } from "expo-router";
import type { MobileApi, User, Memorial } from "../api/client";
import {
  Button,
  Empty,
  ErrorText,
  Logo,
  Screen,
  message,
  years,
} from "../components/UI";
import { styles as s, colors } from "../theme";
export function MemorialListScreen({
  api,
  user,
  onOpen,
  onCreate,
  onProfile,
}: {
  api: MobileApi;
  user: User;
  onOpen: (id: number) => void;
  onCreate: () => void;
  onProfile: () => void;
}) {
  const [items, setItems] = useState<Memorial[]>([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [search, setSearch] = useState("");
  const generation = useRef(0);
  const load = useCallback(async () => {
    const request = ++generation.current;
    setLoading(true);
    try {
      const items = await api.listMemorials();
      if (request !== generation.current) return;
      setItems(items);
      setError("");
    } catch (e) {
      if (request === generation.current) setError(message(e));
    } finally {
      if (request === generation.current) setLoading(false);
    }
  }, [api]);
  useFocusEffect(
    useCallback(() => {
      void load();
      const sub = AppState.addEventListener("change", (state) => {
        if (state === "active") void load();
      });
      return () => {
        generation.current++;
        sub.remove();
      };
    }, [load]),
  );
  return (
    <Screen refreshing={loading} onRefresh={() => void load()}>
      <View style={[s.row, { justifyContent: "space-between" }]}>
        <Logo />
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Открыть профиль"
          onPress={onProfile}
          style={{
            width: 46,
            height: 46,
            borderRadius: 23,
            backgroundColor: colors.warm,
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Text style={{ fontSize: 18, color: colors.primary }}>
            {(user.full_name || user.email || "Я").slice(0, 1).toUpperCase()}
          </Text>
        </Pressable>
      </View>
      <Text style={[s.small, { marginTop: 16, letterSpacing: 1.2 }]}>
        СЕМЕЙНЫЙ АРХИВ
      </Text>
      <Text style={s.title}>Мои страницы</Text>
      <Text style={s.subtitle}>
        Люди, истории и мгновения, которые хочется сохранить.
      </Text>
      <Button label="+ Создать страницу" onPress={onCreate} />
      <TextInput
        accessibilityLabel="Поиск по имени"
        style={s.input}
        placeholder="Найти близкого по имени"
        value={search}
        onChangeText={setSearch}
      />
      <ErrorText error={error} />
      {error && (
        <Button
          secondary
          label="Повторить загрузку"
          onPress={() => void load()}
        />
      )}{" "}
      {!loading && !error && !items.length && (
        <Empty
          title="Первая семейная история"
          body="Создайте страницу близкого. Материалы будут доступны в этом аккаунте и на сайте."
        />
      )}
      {items
        .filter((item) =>
          item.name.toLocaleLowerCase().includes(search.toLocaleLowerCase()),
        )
        .map((item) => (
          <Pressable
            accessibilityRole="button"
            key={item.id}
            onPress={() => onOpen(item.id)}
            style={[s.card, s.row]}
          >
            {item.cover_photo_id ? (
              <Image
                source={api.mediaSource(item.cover_photo_id)}
                style={{ width: 66, height: 82, borderRadius: 30 }}
              />
            ) : (
              <View
                style={{
                  width: 66,
                  height: 82,
                  borderRadius: 30,
                  backgroundColor: colors.warm,
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Text style={[s.h2, { color: colors.primary }]}>
                  {item.name.slice(0, 1)}
                </Text>
              </View>
            )}
            <View style={s.grow}>
              <Text style={[s.h2, { fontSize: 23 }]}>{item.name}</Text>
              <Text style={s.small}>{years(item)}</Text>
              <Text style={s.small}>{item.current_user_role === 'owner' ? 'Владелец' : item.current_user_role === 'editor' ? 'Редактор' : 'Просмотр'}</Text>
              <Text numberOfLines={2} style={s.small}>
                {item.description || "Открыть страницу и воспоминания"}
              </Text>
            </View>
            <Text style={{ fontSize: 25, color: colors.primary }}>›</Text>
          </Pressable>
        ))}
      <Text style={s.small}>
        Потяните вниз, чтобы получить последние изменения с других устройств.
      </Text>
    </Screen>
  );
}
