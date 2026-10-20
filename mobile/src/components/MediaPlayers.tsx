import React from "react";
import { Image, Text, View, Linking } from "react-native";
import {
  useAudioPlayer,
  useAudioPlayerStatus,
  setAudioModeAsync,
} from "expo-audio";
import { useVideoPlayer, VideoView } from "expo-video";
import { Button } from "./UI";
import { styles as s } from "../theme";
import type { MobileApi, Media } from "../api/client";
export function AudioPlayer({
  source,
}: {
  source: { uri: string; headers?: Record<string, string> };
}) {
  const player = useAudioPlayer(source);
  const status = useAudioPlayerStatus(player);
  return (
    <Button
      secondary
      label={status.playing ? "Пауза" : "▶ Прослушать"}
      onPress={() => {
        if (status.playing) player.pause();
        else
          void setAudioModeAsync({
            allowsRecording: false,
            playsInSilentMode: true,
          }).then(() => {
            if (status.didJustFinish) void player.seekTo(0);
            player.play();
          });
      }}
    />
  );
}
function VideoPlayer({
  source,
}: {
  source: { uri: string; headers?: Record<string, string> };
}) {
  const player = useVideoPlayer(source);
  return (
    <VideoView
      player={player}
      style={{ height: 220, width: "100%", borderRadius: 12 }}
      nativeControls
    />
  );
}
export function MediaItem({ api, item }: { api: MobileApi; item: Media }) {
  const source = api.mediaSource(item.id);
  return (
    <View style={s.card}>
      {item.media_type === "photo" ? (
        <Image
          accessibilityLabel={item.file_name}
          source={source}
          resizeMode="contain"
          style={{ width: "100%", height: 240, borderRadius: 12 }}
        />
      ) : item.media_type === "video" ? (
        <VideoPlayer source={source} />
      ) : item.media_type === "audio" ? (
        <AudioPlayer source={source} />
      ) : (
        <Button secondary label="Открыть документ" onPress={()=>void Linking.openURL(source.uri)}/>
      )}
      <Text style={s.small}>{item.file_name}</Text>
    </View>
  );
}
