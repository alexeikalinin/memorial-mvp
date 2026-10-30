import React, { useEffect, useState } from "react";
import { Platform, Text, View } from "react-native";
import {
  AudioModule,
  RecordingPresets,
  setAudioModeAsync,
  useAudioRecorder,
  useAudioRecorderState,
} from "expo-audio";
import type { MobileApi, Memory } from "../api/client";
import { Button, ErrorText, Field, message } from "./UI";
import { AudioPlayer } from "./MediaPlayers";
import { recordingToWav } from "../media/recording";
import { styles as s } from "../theme";
export function MemoryComposer({
  api,
  id,
  onSaved,
  initialMemory,
  onCancel,
}: {
  api: MobileApi;
  id: number;
  onSaved: () => void;
  initialMemory?: Memory;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState(initialMemory?.title || ""),
    [content, setContent] = useState(initialMemory?.content || ""),
    [date, setDate] = useState(initialMemory?.event_date?.slice(0,10) || ""),
    [uri, setUri] = useState<string | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY),
    status = useAudioRecorderState(recorder);
  useEffect(
    () => () => {
      void setAudioModeAsync({ allowsRecording: false }).catch(() => undefined);
    },
    [],
  );
  const toggleRecord = async () => {
    setError("");
    try {
      if (status.isRecording) {
        await recorder.stop();
        setUri(recorder.uri);
        await setAudioModeAsync({ allowsRecording: false });
      } else {
        const permission = await AudioModule.requestRecordingPermissionsAsync();
        if (!permission.granted)
          throw Error("Разрешите доступ к микрофону в настройках телефона.");
        await setAudioModeAsync({
          allowsRecording: true,
          playsInSilentMode: true,
        });
        setUri(null);
        await recorder.prepareToRecordAsync();
        recorder.record();
      }
    } catch (e) {
      setError(message(e));
    }
  };
  const save = async () => {
    setBusy(true);
    setError("");
    try {
      if (
        date &&
        (!/^\d{4}-\d{2}-\d{2}$/.test(date) ||
          Number.isNaN(Date.parse(date)) ||
          new Date(date).toISOString().slice(0, 10) !== date)
      )
        throw Error("Проверьте дату события: ГГГГ-ММ-ДД.");
      if (uri) {
        await api.uploadMedia(id, {
          uri,
          name: `memory-${Date.now()}.${Platform.OS === "web" ? "wav" : "mp4"}`,
          type: Platform.OS === "web" ? "audio/wav" : "audio/mp4",
          file: Platform.OS === "web" ? await recordingToWav(uri) : undefined,
        });
        setUri(null);
      }
      if (content.trim()) {
        const data = {
          title: title.trim() || undefined,
          content: content.trim(),
          event_date: date ? `${date}T00:00:00` : null,
        };
        if(initialMemory)await api.updateMemory(id,initialMemory.id,data);
        else await api.createMemory(id,{...data,event_date:data.event_date || undefined});
      }
      onSaved();
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <View style={s.card}>
      <Text style={s.h2}>{initialMemory ? "Редактировать историю" : "Сохранить историю"}</Text>
      <Field
        label="Название · необязательно"
        value={title}
        onChangeText={setTitle}
      />
      <Field
        label="Ваше воспоминание"
        value={content}
        onChangeText={setContent}
        multiline
      />
      <Field
        label="Дата события · необязательно"
        placeholder="ГГГГ-ММ-ДД"
        value={date}
        onChangeText={setDate}
      />
      <Button
        secondary
        label={
          status.isRecording
            ? `Остановить · ${Math.floor(status.durationMillis / 1000)} сек`
            : "Записать голосом"
        }
        onPress={() => void toggleRecord()}
        disabled={busy}
      />
      {uri ? (
        <>
          <Text style={s.small}>
            Запись сохранится в «Материалах». Текстовое воспоминание сохраняется
            отдельно и используется в разговоре.
          </Text>
          <AudioPlayer source={{ uri }} />
          <Button
            secondary
            label="Удалить запись"
            onPress={() => setUri(null)}
          />
        </>
      ) : null}
      <ErrorText error={error} />
      <Button
        label="Сохранить"
        onPress={() => void save()}
        busy={busy}
        disabled={status.isRecording || (!content.trim() && !uri)}
      />
      <Button
        secondary
        label="Отмена"
        onPress={onCancel}
        disabled={busy || status.isRecording}
      />
    </View>
  );
}
