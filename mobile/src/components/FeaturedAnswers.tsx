import { GUEST_ANSWERS_ENABLED } from "../config";
import React, { useCallback, useEffect, useState } from "react";
import { Text, View } from "react-native";
import type { MobileApi, SavedAnswer, GuestAnswer } from "../api/client";
import { Button, ErrorText, message } from "./UI";
import { AudioPlayer } from "./MediaPlayers";
import { styles as s } from "../theme";

export function FeaturedAnswers({api, id, owner = false, question, onLoaded, memoryId}: {api: MobileApi; id: number; owner?: boolean; question?: string; memoryId?: number; onLoaded?: (rows: SavedAnswer[]) => void}) {
  const [rows, setRows] = useState<SavedAnswer[]>([]);
  const [guests, setGuests] = useState<GuestAnswer[]>([]);
  const [open, setOpen] = useState(Boolean(memoryId));
  const [expanded, setExpanded] = useState<number | null>(null);
  const [showStale, setShowStale] = useState(false);
  const [selected, setSelected] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<{cacheId: number; id: string; uri: string} | null>(null);
  const revoice = async (row: SavedAnswer) => {
    setBusy(true); setError("");
    try { const result = await api.revoiceAnswer(id, row); if (!result.audio_url || !result.audio_preview_id || !result.answer_cache_id) throw new Error(result.audio_error || "Не удалось создать дубль"); setPreview({cacheId: result.answer_cache_id, id: result.audio_preview_id, uri: api.resolveMediaUrl(result.audio_url)}); }
    catch(e) {setError(message(e));} finally {setBusy(false);}
  };
  const choose = async (accept: boolean) => {
    if (!preview) return;
    setBusy(true);
    try {await api.chooseAudio(preview.cacheId, preview.id, accept);setPreview(null);await load();}
    catch(e) {setError(message(e));} finally {setBusy(false);}
  };
  const load = useCallback(async () => {
    try { if (owner) { const data = await api.savedAnswers(id); setRows(data); onLoaded?.(data); } else setGuests(await api.guestAnswers(id)); setError(""); }
    catch(e) { if (owner) setError(message(e)); }
  }, [api, id, owner, onLoaded]);
  useEffect(() => {
    if (question) return;
    let active = true;
    if (owner) api.savedAnswers(id).then(data => {if (active) {setRows(data); onLoaded?.(data);}}).catch(e => {if (active) setError(message(e));});
    else api.guestAnswers(id).then(data => {if (active) setGuests(data);}).catch(() => {});
    return () => {active = false;};
  }, [api, id, owner, question, onLoaded]);
  const update = async (row: SavedAnswer, publish: boolean, variant = row.audio_variant, position = row.position ?? rows.filter(r => r.featured).length) => {
    setBusy(true);
    try { await api.selectAnswer(row.cache_id, publish, variant, Math.min(4, position)); await load(); }
    catch(e) { setError(message(e)); }
    finally { setBusy(false); }
  };
  if (!owner) return guests.length ? <View style={s.card}>
    <Text style={s.h2}>Знакомство с аватаром</Text>
    <Text style={s.small}>Готовые ответы семьи — не расходуют пять свободных вопросов.</Text>
    {guests.map(row => <View key={row.id} style={{gap: 10}}>
      <Button secondary label={row.question} onPress={() => setSelected(row.id)} />
      {selected === row.id ? <><Text selectable style={s.text}>{row.answer}</Text>{row.audio_url ? <AudioPlayer source={{uri: api.resolveMediaUrl(row.audio_url)}} /> : null}</> : null}
    </View>)}
  </View> : null;
  return <View style={s.card}>
    <Button secondary label={memoryId ? "Озвученные ответы" : GUEST_ANSWERS_ENABLED ? `Ответы и озвучка · Для гостей ${rows.filter(r => r.featured).length}/5` : "Ответы и озвучка"} onPress={() => {setOpen(!open); void load();}} />
    {open ? <>
      <Text style={s.small}>{GUEST_ANSWERS_ENABLED ? "Выбранные текст и аудио станут доступны посетителям публичной страницы и приглашённым в чат. Проверьте, что в них нет закрытых семейных сведений." : "Здесь хранятся ответы по воспоминаниям и готовая озвучка."}</Text>
      <ErrorText error={error} />
      {!rows.length ? <Text style={s.small}>Задайте вопрос аватару — сохранённый ответ появится здесь.</Text> : null}
      {rows.some(row => row.stale && !row.featured) ? <Button secondary label={showStale ? "Скрыть устаревшие ответы" : "Показать устаревшие ответы"} onPress={() => setShowStale(!showStale)} /> : null}
      {rows.filter(row => (!memoryId || (row.source_memory_ids.includes(memoryId) && row.audio_variants.length > 0)) && (!question || row.question.trim().toLowerCase() === question.trim().toLowerCase()) && (showStale || !row.stale || row.featured)).map(row => <View key={row.cache_id} style={s.card}>
        <Button secondary label={`${row.question} · ${row.featured ? "Выбран" : row.audio_variants.length ? "Есть озвучка" : "Текст"}`} onPress={() => setExpanded(expanded === row.cache_id ? null : row.cache_id)} />
        {question || expanded === row.cache_id ? <><Text selectable style={s.text}>{row.answer}</Text>
        <Text style={s.small}>{row.stale ? "Нужно проверить — задайте вопрос снова" : row.audio_variants.length ? "Озвучка сохранена" : "Только текст"}</Text>
        {row.sources.map((source, i) => <Text style={s.small} key={i}>{source}</Text>)}
        {row.audio_variants.map((variant, i) => <View key={variant.key} style={{gap: 8}}>
          <AudioPlayer source={{uri: api.resolveMediaUrl(variant.audio_url)}} />
          {GUEST_ANSWERS_ENABLED && row.featured ? <Button secondary disabled={busy || row.stale} label={row.audio_variant === variant.key ? "✓ Выбранная озвучка" : `Выбрать озвучку ${i + 1}`} onPress={() => void update(row, true, variant.key)} /> : null}
        </View>)}
        {preview?.cacheId === row.cache_id ? <View style={s.card}><Text style={s.small}>Новый дубль. Прежняя запись активна до вашего выбора.</Text><AudioPlayer source={{uri: preview.uri}} /><Button label="Использовать этот вариант" disabled={busy} onPress={() => void choose(true)} /><Button secondary label="Оставить прежний" disabled={busy} onPress={() => void choose(false)} /></View> : null}
        <Button secondary disabled={busy || row.stale || preview !== null} label="Создать новый дубль (платно)" onPress={() => void revoice(row)} />
        {GUEST_ANSWERS_ENABLED ? <Button secondary disabled={busy || (row.stale && !row.featured)} label={row.featured ? "Убрать из предложенных" : "Предлагать гостям"} onPress={() => void update(row, !row.featured, row.audio_variant || row.audio_variants[0]?.key || null)} /> : null}
        {GUEST_ANSWERS_ENABLED && row.featured ? <Button secondary label={`Позиция ${1 + (row.position ?? 0)} · изменить`} disabled={busy || row.stale} onPress={() => void update(row, true, row.audio_variant, ((row.position ?? 0) + 1) % 5)} /> : null}
      </> : null}</View>)}
    </> : null}
  </View>;
}
