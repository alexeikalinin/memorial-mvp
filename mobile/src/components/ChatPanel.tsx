import React, { useState } from "react";
import { Switch, Text, View } from "react-native";
import type { MobileApi } from "../api/client";
import { Button, ErrorText, Field, message } from "./UI";
import { AudioPlayer } from "./MediaPlayers";
import { styles as s, colors } from "../theme";
type Entry = {
  role: "question" | "answer";
  text: string;
  sources?: string[];
  audio?: string | null;
};
export function ChatPanel({ api, id }: { api: MobileApi; id: number }) {
  const [question, setQuestion] = useState(""),
    [entries, setEntries] = useState<Entry[]>([]),
    [busy, setBusy] = useState(false),
    [audio, setAudio] = useState(false),
    [error, setError] = useState("");
  const ask = async () => {
    const text = question.trim();
    if (!text) return;
    setBusy(true);
    setError("");
    setEntries((old) => [...old, { role: "question", text }]);
    setQuestion("");
    try {
      const result = await api.chat(id, text, audio);
      setEntries((old) => [
        ...old,
        {
          role: "answer",
          text: result.answer,
          sources: result.sources,
          audio: result.audio_url
            ? api.resolveMediaUrl(result.audio_url)
            : null,
        },
      ]);
      if (result.audio_error)
        setError("Ответ готов, но озвучивание сейчас недоступно.");
    } catch (e) {
      setError(message(e));
      setQuestion(text);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <Text style={s.title}>Разговор</Text>
      <Text style={s.subtitle}>
        AI отвечает по сохранённым воспоминаниям. Это не сам человек; ответы
        можно сверять с источниками.
      </Text>
      <View style={[s.card, s.row]}>
        <Text style={[s.text, s.grow]}>Озвучивать ответы</Text>
        <Switch
          value={audio}
          onValueChange={setAudio}
          accessibilityLabel="Озвучивать ответы"
          trackColor={{ true: colors.primary }}
        />
      </View>
      {entries.map((entry, index) => (
        <View
          key={index}
          style={[
            s.card,
            entry.role === "question" && {
              backgroundColor: colors.warm,
              marginLeft: 24,
            },
          ]}
        >
          <Text style={s.small}>
            {entry.role === "question" ? "Вы" : "Ответ по воспоминаниям"}
          </Text>
          <Text selectable style={s.text}>
            {entry.text}
          </Text>
          {entry.audio && <AudioPlayer source={{ uri: entry.audio }} />}
          {!!entry.sources?.length && (
            <View style={{ gap: 8 }}>
              <Text style={[s.small, { fontWeight: "600" }]}>Источники</Text>
              {entry.sources.map((source, i) => (
                <Text selectable key={i} style={s.small}>
                  {source}
                </Text>
              ))}
            </View>
          )}
        </View>
      ))}
      <Field
        label="Ваш вопрос"
        multiline
        value={question}
        onChangeText={setQuestion}
      />
      <ErrorText error={error} />
      <Button
        label="Отправить"
        disabled={!question.trim()}
        busy={busy}
        onPress={() => void ask()}
      />
      <Text style={s.small}>
        История этого разговора хранится только до выхода с экрана.
      </Text>
    </>
  );
}
