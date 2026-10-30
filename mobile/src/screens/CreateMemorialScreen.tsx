import { personDates } from "../utils/personDates";
import { GenderSelect } from "../components/GenderSelect";
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
    [gender, setGender] = useState<"male"|"female"|null>(null),
    [description, setDescription] = useState(""),
    [maiden, setMaiden] = useState(""),
    [birth, setBirth] = useState(""),
    [death, setDeath] = useState(""),
    [isPublic, setPublic] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const create = async () => {
    setError("");
    setBusy(true);
    try {
      const person = await api.createMemorial({
        name: name.trim(),
        description: description.trim() || undefined,
        gender,
        maiden_name: gender === "female" ? maiden.trim() || null : null,
        ...personDates(birth, death),
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
      <GenderSelect value={gender} onChange={setGender} />
      {gender === "female" ? <Field label="Девичья фамилия · необязательно" value={maiden} onChangeText={setMaiden} /> : null}
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
      <Text style={s.small}>Для живого человека оставьте дату ухода пустой.</Text>
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
