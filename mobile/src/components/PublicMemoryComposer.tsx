import React, { useState } from "react";
import { Text, View } from "react-native";
import type { MobileApi } from "../api/client";
import { Button, ErrorText, Field, message } from "./UI";
import { styles as s } from "../theme";
export function PublicMemoryComposer({
  api,
  id,
  onSaved,
  onCancel,
}: {
  api: MobileApi;
  id: number;
  onSaved: () => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(""),
    [title, setTitle] = useState(""),
    [content, setContent] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const save = async () => {
    setBusy(true);
    setError("");
    try {
      await api.submitPublicMemory(id, {
        contributor_name: name.trim(),
        title: title.trim() || undefined,
        content: content.trim(),
      });
      onSaved();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <View style={s.card}>
      <Text style={s.h2}>Поделиться воспоминанием</Text>
      <Text style={s.small}>
        Рассказ появится на странице после одобрения владельцем.
      </Text>
      <Field
        label="Ваше имя"
        value={name}
        onChangeText={setName}
        maxLength={100}
      />
      <Field
        label="Название · необязательно"
        value={title}
        onChangeText={setTitle}
        maxLength={255}
      />
      <Field
        label="Воспоминание · от 10 символов"
        value={content}
        onChangeText={setContent}
        multiline
        maxLength={5000}
      />
      <ErrorText error={error} />
      <Button
        label="Отправить на рассмотрение"
        busy={busy}
        disabled={!name.trim() || content.trim().length < 10}
        onPress={() => void save()}
      />
      <Button secondary label="Отмена" onPress={onCancel} disabled={busy} />
    </View>
  );
}
