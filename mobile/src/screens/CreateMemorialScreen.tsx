import React, { useState } from "react";
import { Switch, Text, View } from "react-native";
import type { MobileApi } from "../api/client";
import { Button, ErrorText, Field, Screen, message } from "../components/UI";
import { styles as s, colors } from "../theme";
export function CreateMemorialScreen({
  api,
  onCreated,
  onBack,
}: {
  api: MobileApi;
  onCreated: (id: number) => void;
  onBack: () => void;
}) {
  const [name, setName] = useState(""),
    [description, setDescription] = useState(""),
    [birth, setBirth] = useState(""),
    [death, setDeath] = useState(""),
    [isPublic, setPublic] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const create = async () => {
    setError("");
    setBusy(true);
    try {
      for (const date of [birth, death])
        if (
          date &&
          (!/^\d{4}-\d{2}-\d{2}$/.test(date) ||
            Number.isNaN(Date.parse(date)) ||
            new Date(date).toISOString().slice(0, 10) !== date)
        )
          throw Error("Укажите существующую дату в формате ГГГГ-ММ-ДД.");
      if (birth && death && birth > death)
        throw Error("Дата ухода не может быть раньше даты рождения.");
      const person = await api.createMemorial({
        name: name.trim(),
        description: description.trim() || undefined,
        birth_date: birth ? `${birth}T00:00:00` : undefined,
        death_date: death ? `${death}T00:00:00` : undefined,
        is_public: isPublic,
      });
      onCreated(person.id);
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <Screen title="Новая страница" onBack={onBack}>
      <Text style={s.title}>С чего начнётся история?</Text>
      <Text style={s.subtitle}>
        Достаточно имени. Фотографии и воспоминания можно добавить позже.
      </Text>
      <Field label="Имя и фамилия" value={name} onChangeText={setName} />
      <Field
        label="О человеке"
        multiline
        value={description}
        onChangeText={setDescription}
      />
      <Field
        label="Дата рождения · необязательно"
        placeholder="ГГГГ-ММ-ДД"
        value={birth}
        onChangeText={setBirth}
      />
      <Field
        label="Дата ухода · если применимо"
        placeholder="ГГГГ-ММ-ДД"
        value={death}
        onChangeText={setDeath}
      />
      <View style={[s.card, s.row]}>
        <View style={s.grow}>
          <Text style={s.text}>Публичная страница</Text>
          <Text style={s.small}>Разрешить просмотр по ссылке</Text>
        </View>
        <Switch
          accessibilityLabel="Публичная страница"
          value={isPublic}
          onValueChange={setPublic}
          trackColor={{ true: colors.primary }}
        />
      </View>
      <ErrorText error={error} />
      <Button
        label="Создать страницу"
        onPress={() => void create()}
        disabled={!name.trim()}
        busy={busy}
      />
    </Screen>
  );
}
