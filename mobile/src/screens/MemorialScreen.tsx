import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  AppState,
  Image,
  Linking,
  Share,
  Text,
  View,
  Switch,
  BackHandler,
  Alert,
} from "react-native";
import { useFocusEffect } from "expo-router";
import * as ImagePicker from "expo-image-picker";
import * as DocumentPicker from "expo-document-picker";
import type {
  MobileApi,
  Memorial,
  Memory,
  Relationship,
  TimelineItem,
} from "../api/client";
import {
  Button,
  Empty,
  ErrorText,
  Field,
  Row,
  Screen,
  message,
  years,
} from "../components/UI";
import { MemoryComposer } from "../components/MemoryComposer";
import { PublicMemoryComposer } from "../components/PublicMemoryComposer";
import { MediaItem } from "../components/MediaPlayers";
import { ChatPanel } from "../components/ChatPanel";
import { styles as s, colors } from "../theme";
type Section =
  | "overview"
  | "memories"
  | "materials"
  | "chat"
  | "relatives"
  | "timeline"
  | "manage";
const labels: Record<Section, string> = {
  overview: "Страница близкого",
  memories: "Воспоминания",
  materials: "Материалы",
  chat: "Разговор",
  relatives: "Родные",
  timeline: "История жизни",
  manage: "Управление",
};
const relationshipLabels: Record<string, string> = {
  parent: "Родитель",
  child: "Ребёнок",
  spouse: "Супруг / супруга",
  sibling: "Брат / сестра",
  grandparent: "Бабушка / дедушка",
  grandchild: "Внук / внучка",
  other: "Родственник",
  step_parent: "Отчим / мачеха",
  step_child: "Пасынок / падчерица",
  adoptive_parent: "Приёмный родитель",
  adoptive_child: "Приёмный ребёнок",
  half_sibling: "Брат / сестра",
  partner: "Партнёр",
  ex_spouse: "Бывший супруг / супруга",
  custom: "Близкий человек",
};
function MemorialContent({
  api,
  id,
  onBack,
  onOpen,
}: {
  api: MobileApi;
  id: number;
  onBack: () => void;
  onOpen: (id: number) => void;
}) {
  const [person, setPerson] = useState<Memorial | null>(null),
    [section, setSection] = useState<Section>("overview"),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [compose, setCompose] = useState(false),
    [uploading, setUploading] = useState(false),
    [relatives, setRelatives] = useState<Relationship[]>([]),
    [timeline, setTimeline] = useState<TimelineItem[]>([]),
    [pending, setPending] = useState<Memory[]>([]),
    [editName, setEditName] = useState(""),
    [editDescription, setEditDescription] = useState(""),
    [saving, setSaving] = useState(false);
  const generation = useRef(0);
  const editDirty = useRef(false);
  const load = useCallback(async () => {
    const request = ++generation.current;
    setLoading(true);
    try {
      const result = await api.getMemorial(id);
      if (request !== generation.current) return;
      setPerson(result);
      if (!editDirty.current) {
        setEditName(result.name);
        setEditDescription(result.description || "");
      }
      setError("");
    } catch (e) {
      if (request === generation.current) setError(message(e));
    } finally {
      if (request === generation.current) setLoading(false);
    }
  }, [api, id]);
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
  const back = useCallback(() => {
    if (compose) setCompose(false);
    else if (section !== "overview") setSection("overview");
    else onBack();
  }, [compose, section, onBack]);
  useEffect(() => {
    const sub = BackHandler.addEventListener("hardwareBackPress", () => {
      if (section === "overview" && !compose) return false;
      back();
      return true;
    });
    return () => sub.remove();
  }, [back, section, compose]);
  const open = async (next: Section) => {
    setSection(next);
    setError("");
    try {
      if (next === "relatives") setRelatives(await api.getRelationships(id));
      if (next === "timeline") setTimeline(await api.getTimeline(id));
      if (next === "manage" && person?.current_user_role === "owner")
        setPending(await api.getPendingMemories(id));
    } catch (e) {
      setError(message(e));
    }
  };
  const upload = async (kind: "photos" | "file") => {
    setError("");
    try {
      let files: {
        uri: string;
        name: string;
        mimeType?: string;
        file?: Blob;
      }[] = [];
      if (kind === "photos") {
        const result = await ImagePicker.launchImageLibraryAsync({
          mediaTypes: ["images", "videos"],
          allowsMultipleSelection: true,
          quality: 0.9,
        });
        if (result.canceled) return;
        files = result.assets.map((asset) => ({
          uri: asset.uri,
          name:
            asset.fileName ||
            `photo-${Date.now()}.${asset.type === "video" ? "mp4" : "jpg"}`,
          mimeType: asset.mimeType,
          file: asset.file,
        }));
      } else {
        const result = await DocumentPicker.getDocumentAsync({
          type: ["audio/*", "image/*", "video/*"],
          multiple: true,
          copyToCacheDirectory: true,
        });
        if (result.canceled) return;
        files = result.assets.map((asset) => ({
          uri: asset.uri,
          name: asset.name,
          mimeType: asset.mimeType,
          file: asset.file,
        }));
      }
      setUploading(true);
      for (const file of files) await api.uploadMedia(id, file);
      await load();
      setSection("materials");
    } catch (e) {
      await load();
      setError(message(e));
    } finally {
      setUploading(false);
    }
  };
  const canRead = !!person?.current_user_role;
  const canEdit =
    person?.current_user_role === "owner" ||
    person?.current_user_role === "editor";
  const save = async () => {
    setSaving(true);
    setError("");
    try {
      await api.updateMemorial(id, {
        name: editName.trim(),
        description: editDescription.trim(),
      });
      editDirty.current = false;
      await load();
    } catch (e) {
      setError(message(e));
    } finally {
      setSaving(false);
    }
  };
  const moderate = async (memoryId: number, approve: boolean) => {
    try {
      setSaving(true);
      if (approve) await api.approveMemory(id, memoryId);
      else await api.rejectMemory(id, memoryId);
      setPending(await api.getPendingMemories(id));
      await load();
    } catch (e) {
      setError(message(e));
    } finally {
      setSaving(false);
    }
  };
  const invite = async () => {
    try {
      setSaving(true);
      const result = await api.invite(id);
      await Share.share({ message: result.invite_url });
    } catch (e) {
      setError(message(e));
    } finally {
      setSaving(false);
    }
  };
  return (
    <Screen
      title={
        section === "overview" ? person?.name || "Страница" : labels[section]
      }
      onBack={back}
      refreshing={loading}
      onRefresh={() => void load()}
    >
      <ErrorText error={error} />
      {!person && !loading && (
        <Button
          secondary
          label="Повторить загрузку"
          onPress={() => void load()}
        />
      )}{" "}
      {person && (
        <>
          {section === "overview" && (
            <>
              <View style={s.hero}>
                {person.cover_photo_id ? (
                  <Image
                    accessibilityLabel={person.name}
                    source={api.mediaSource(person.cover_photo_id)}
                    style={s.portrait}
                  />
                ) : (
                  <View
                    style={[
                      s.portrait,
                      { alignItems: "center", justifyContent: "center" },
                    ]}
                  >
                    <Text style={[s.title, { color: colors.primary }]}>
                      {person.name.slice(0, 1)}
                    </Text>
                  </View>
                )}
                <Text style={[s.title, { textAlign: "center" }]}>
                  {person.name}
                </Text>
                <Text style={s.subtitle}>{years(person)}</Text>
                <Text style={s.small}>
                  {person.is_public
                    ? "Публичная страница"
                    : "Семейная страница · доступ ограничен"}
                </Text>
              </View>
              {person.description && (
                <Text selectable style={s.text}>
                  {person.description}
                </Text>
              )}
              {(canEdit || person.is_public) && (
                <Button
                  label="+ Добавить воспоминание"
                  onPress={() => {
                    setCompose(true);
                    setSection("memories");
                  }}
                />
              )}
              {canRead && (
                <>
                  <Row
                    title="Воспоминания"
                    body={`${person.memories?.length || 0} сохранённых историй`}
                    onPress={() => void open("memories")}
                  />
                  <Row
                    title="Фото и записи"
                    body={`${person.media?.length || 0} материалов`}
                    onPress={() => void open("materials")}
                  />
                </>
              )}
              <Row
                title="Разговор по воспоминаниям"
                body="С источниками и голосовыми ответами"
                onPress={() => void open("chat")}
              />
              <View style={{ height: 4 }} />
              {canRead && (
                <>
                  <Row
                    title="Родные"
                    body="Близкие люди и родственные связи"
                    onPress={() => void open("relatives")}
                  />
                  <Row
                    title="История жизни"
                    body="Воспоминания по датам событий"
                    onPress={() => void open("timeline")}
                  />
                </>
              )}
              {person.is_public && (
                <Button
                  secondary
                  label="Поделиться страницей"
                  onPress={() =>
                    void Share.share({ message: api.publicPageUrl(id) })
                  }
                />
              )}{" "}
              {canEdit && (
                <Button
                  secondary
                  label="Управление страницей"
                  onPress={() => void open("manage")}
                />
              )}
            </>
          )}
          {section === "memories" && (
            <>
              <Text style={s.title}>Воспоминания</Text>
              {compose ? (
                canEdit ? (
                  <MemoryComposer
                    api={api}
                    id={id}
                    onSaved={() => {
                      setCompose(false);
                      void load();
                    }}
                    onCancel={() => setCompose(false)}
                  />
                ) : (
                  <PublicMemoryComposer
                    api={api}
                    id={id}
                    onSaved={() => {
                      setCompose(false);
                      Alert.alert(
                        "Спасибо за историю",
                        "Воспоминание отправлено владельцу на рассмотрение.",
                      );
                    }}
                    onCancel={() => setCompose(false)}
                  />
                )
              ) : (
                (canEdit || person.is_public) && (
                  <Button
                    label="+ Сохранить историю"
                    onPress={() => setCompose(true)}
                  />
                )
              )}{" "}
              {canRead && !person.memories?.length && (
                <Empty
                  title="История начинается с малого"
                  body="Любимая фраза, семейная традиция или один памятный день — всё это заслуживает сохранения."
                />
              )}
              {canRead &&
                person.memories?.map((memory) => (
                  <View key={memory.id} style={s.card}>
                    {memory.title && <Text style={s.h2}>{memory.title}</Text>}
                    <Text selectable style={s.text}>
                      {memory.content}
                    </Text>
                    <Text style={s.small}>
                      {memory.contributor_name || "Семейное воспоминание"}
                      {memory.event_date
                        ? ` · ${memory.event_date.slice(0, 10)}`
                        : ""}
                    </Text>
                  </View>
                ))}
            </>
          )}
          {section === "materials" && canRead && (
            <>
              <Text style={s.title}>Фото и записи</Text>
              {canEdit && (
                <>
                  <Button
                    label="Добавить фото или видео"
                    busy={uploading}
                    onPress={() => void upload("photos")}
                  />
                  <Button
                    secondary
                    label="Выбрать аудио или файл"
                    disabled={uploading}
                    onPress={() => void upload("file")}
                  />
                </>
              )}
              {!person.media?.length && (
                <Empty
                  title="Семейный альбом"
                  body="Здесь появятся фотографии, видео и записи голоса."
                />
              )}
              {person.media?.map((item) => (
                <MediaItem key={item.id} api={api} item={item} />
              ))}
            </>
          )}
          {section === "chat" && <ChatPanel api={api} id={id} />}
          {section === "relatives" && canRead && (
            <>
              <Text style={s.title}>Родные</Text>
              <Text style={s.subtitle}>
                Ближайшие связи без сложной схемы. Выберите человека, чтобы
                открыть его страницу.
              </Text>
              {!relatives.length && (
                <Empty
                  title="Семейные связи"
                  body="Связи, добавленные на сайте, появятся здесь. Управление деревом пока доступно в веб-версии."
                />
              )}
              {relatives.map((relative) => (
                <Row
                  key={relative.id}
                  title={
                    relative.related_memorial_name || "Страница родственника"
                  }
                  body={
                    relative.custom_label ||
                    relationshipLabels[relative.relationship_type] ||
                    relative.relationship_type
                  }
                  onPress={() => onOpen(relative.related_memorial_id)}
                />
              ))}
              <Text style={s.small}>
                Родственная связь не открывает доступ к закрытым материалам.
              </Text>
            </>
          )}
          {section === "timeline" && canRead && (
            <>
              <Text style={s.title}>История жизни</Text>
              {!timeline.length && (
                <Empty
                  title="События жизни"
                  body="Добавьте дату события к воспоминанию — оно появится в хронологии."
                />
              )}
              {timeline.map((event, index) => (
                <View
                  key={`${event.type}-${event.id}-${index}`}
                  style={[
                    s.card,
                    { borderLeftWidth: 3, borderLeftColor: colors.accent },
                  ]}
                >
                  <Text style={s.small}>{event.date_label || event.year}</Text>
                  {event.title && <Text style={s.h2}>{event.title}</Text>}
                  <Text selectable style={s.text}>
                    {event.content}
                  </Text>
                </View>
              ))}
            </>
          )}
          {section === "manage" && canEdit && (
            <>
              <Text style={s.title}>Управление</Text>
              <Field
                label="Имя"
                value={editName}
                onChangeText={(value) => {
                  editDirty.current = true;
                  setEditName(value);
                }}
              />
              <Field
                label="О человеке"
                multiline
                value={editDescription}
                onChangeText={(value) => {
                  editDirty.current = true;
                  setEditDescription(value);
                }}
              />
              <Button
                label="Сохранить изменения"
                busy={saving}
                disabled={!editName.trim()}
                onPress={() => void save()}
              />
              {person.current_user_role === "owner" && (
                <>
                  <View style={[s.card, s.row]}>
                    <View style={s.grow}>
                      <Text style={s.text}>Публичная страница</Text>
                      <Text style={s.small}>Просмотр по ссылке и QR</Text>
                    </View>
                    <Switch
                      value={person.is_public}
                      accessibilityLabel="Публичная страница"
                      trackColor={{ true: colors.primary }}
                      onValueChange={(value) => {
                        void api
                          .updateMemorial(id, { is_public: value })
                          .then(() => load())
                          .catch((e) => setError(message(e)));
                      }}
                    />
                  </View>
                  <Button
                    secondary
                    label="Пригласить поделиться историей"
                    busy={saving}
                    onPress={() => void invite()}
                  />
                  <Text style={s.h2}>На рассмотрении · {pending.length}</Text>
                  {pending.map((memory) => (
                    <View key={memory.id} style={s.card}>
                      <Text style={s.small}>{memory.contributor_name}</Text>
                      <Text style={s.text}>{memory.content}</Text>
                      <Button
                        label="Опубликовать"
                        disabled={saving}
                        onPress={() => void moderate(memory.id, true)}
                      />
                      <Button
                        secondary
                        label="Отклонить"
                        disabled={saving}
                        onPress={() => void moderate(memory.id, false)}
                      />
                    </View>
                  ))}
                </>
              )}
              <Row
                title="Оформление и настройка голоса"
                body="Открыть полную веб-версию"
                onPress={() =>
                  void Linking.openURL(api.websiteUrl(`/memorials/${id}`))
                }
              />
            </>
          )}
        </>
      )}
    </Screen>
  );
}

export function MemorialScreen(
  props: React.ComponentProps<typeof MemorialContent>,
) {
  return <MemorialContent key={props.id} {...props} />;
}
