import React from "react";
import { View, StyleSheet, Image, Text } from "react-native";

type Props = { uri: string };

export default function VideoPlayer({ uri }: Props) {
  // 일단 간단한 썸네일/링크 표시로 대체
  return (
    <View style={styles.wrap}>
      <View style={styles.placeholder}>
        <Text style={styles.icon}>🎬</Text>
        <Text style={styles.text}>영상</Text>
        <Text style={styles.uri} numberOfLines={2}>{uri}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { marginVertical: 8 },
  placeholder: {
    width: "100%",
    height: 220,
    backgroundColor: "#f3f4f6",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderRadius: 8,
    justifyContent: "center",
    alignItems: "center",
    padding: 16,
  },
  icon: { fontSize: 48, marginBottom: 8 },
  text: { fontSize: 16, color: "#6b7280", fontWeight: "600" },
  uri: { marginTop: 8, fontSize: 12, color: "#9ca3af", textAlign: "center" }
});
