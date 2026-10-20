import React from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  RefreshControl,
  ScrollView,
  Text,
  TextInput,
  TextInputProps,
  View,
  Image,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { colors, styles as s } from "../theme";
export function Screen({
  children,
  title,
  onBack,
  refreshing,
  onRefresh,
  right,
}: {
  children: React.ReactNode;
  title?: string;
  onBack?: () => void;
  refreshing?: boolean;
  onRefresh?: () => void;
  right?: React.ReactNode;
}) {
  return (
    <SafeAreaView style={s.screen} edges={["top", "bottom"]}>
      <KeyboardAvoidingView
        style={s.grow}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        {(title || onBack || right) && (
          <View
            style={[
              s.row,
              {
                paddingHorizontal: 18,
                paddingVertical: 12,
                borderBottomWidth: 1,
                borderColor: colors.border,
              },
            ]}
          >
            {onBack && (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Назад"
                onPress={onBack}
                style={{ padding: 8, minHeight: 44, justifyContent: "center" }}
              >
                <Text style={{ fontSize: 17, color: colors.primary }}>
                  ‹ Назад
                </Text>
              </Pressable>
            )}
            <Text
              numberOfLines={1}
              style={[s.text, s.grow, { fontWeight: "600" }]}
            >
              {title}
            </Text>
            {right}
          </View>
        )}
        <ScrollView
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={s.content}
          refreshControl={
            onRefresh ? (
              <RefreshControl
                refreshing={!!refreshing}
                onRefresh={onRefresh}
                tintColor={colors.primary}
              />
            ) : undefined
          }
        >
          {children}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
export function Button({
  label,
  onPress,
  secondary = false,
  disabled = false,
  busy = false,
}: {
  label: string;
  onPress: () => void;
  secondary?: boolean;
  disabled?: boolean;
  busy?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled || busy}
      accessibilityState={{ disabled: disabled || busy, busy }}
      onPress={onPress}
      style={({ pressed }) => ({
        minHeight: 50,
        paddingHorizontal: 18,
        paddingVertical: 13,
        borderRadius: 13,
        backgroundColor: secondary ? colors.warm : colors.primary,
        opacity: disabled || busy ? 0.5 : pressed ? 0.8 : 1,
        alignItems: "center",
        justifyContent: "center",
      })}
    >
      {busy ? (
        <ActivityIndicator color={secondary ? colors.primary : "#fff"} />
      ) : (
        <Text
          style={{
            fontSize: 16,
            fontWeight: "600",
            color: secondary ? colors.primary : "#fff",
            textAlign: "center",
          }}
        >
          {label}
        </Text>
      )}
    </Pressable>
  );
}
export function Field({ label, ...props }: TextInputProps & { label: string }) {
  return (
    <View>
      <Text style={s.label}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        placeholderTextColor={colors.muted}
        style={[
          s.input,
          props.multiline && { minHeight: 130, textAlignVertical: "top" },
        ]}
        {...props}
      />
    </View>
  );
}
export function Empty({ title, body }: { title: string; body: string }) {
  return (
    <View style={[s.card, { paddingVertical: 30 }]}>
      <Text style={s.h2}>{title}</Text>
      <Text style={s.subtitle}>{body}</Text>
    </View>
  );
}
export function Row({
  title,
  body,
  onPress,
  icon = "›",
}: {
  title: string;
  body?: string;
  onPress: () => void;
  icon?: string;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={[s.card, s.row]}
    >
      <View style={s.grow}>
        <Text style={[s.text, { fontWeight: "600" }]}>{title}</Text>
        {body && <Text style={s.small}>{body}</Text>}
      </View>
      <Text style={{ fontSize: 24, color: colors.primary }}>{icon}</Text>
    </Pressable>
  );
}
export function Logo() {
  return (
    <Image
      accessibilityLabel="vspomin.ai — ВСПОМИНАЙ"
      source={require("../../assets/logo-light.png")}
      resizeMode="contain"
      style={{ width: 230, height: 55, alignSelf: "flex-start", flexShrink:1 }}
    />
  );
}
export function ErrorText({ error }: { error: string }) {
  return error ? (
    <Text accessibilityRole="alert" style={s.error}>
      {error}
    </Text>
  ) : null;
}
export const message = (error: unknown) =>
  error instanceof Error
    ? error.message
    : "Не удалось выполнить действие. Попробуйте ещё раз.";
export const years = (person: {
  birth_date?: string | null;
  death_date?: string | null;
}) =>
  [person.birth_date?.slice(0, 4), person.death_date?.slice(0, 4)]
    .filter(Boolean)
    .join(" — ");
