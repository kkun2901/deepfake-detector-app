// src/components/Timeline.tsx
import React from "react";
import { View, Text, StyleSheet } from "react-native";
import type { TimelineItem } from "../types/common";

type Props = { data: TimelineItem[] };

function normalizeScore(score: number): number {
  const s = Number(score);
  if (!isFinite(s) || isNaN(s)) return 0;
  return s > 1.0001 ? Math.min(s / 100, 1) : Math.max(0, Math.min(s, 1));
}

export default function Timeline({ data }: Props) {
  if (!data || data.length === 0) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyText}>표시할 데이터가 없습니다.</Text>
      </View>
    );
  }

  return (
    <View style={styles.wrap}>
      {data.map((it, idx) => {
        const s = normalizeScore(it.score);
        const percentNum = Math.min(100, s * 100); // ← number
        const percentLabel = percentNum.toFixed(1); // ← string(화면 표시용)
        const barColor = it.label === "suspect" ? "#ef4444" : s > 0.6 ? "#f59e0b" : "#10b981";

        return (
          <View key={idx} style={styles.item}>
            <Text style={styles.time}>{it.t.toFixed(1)}s</Text>
            <View style={styles.barWrap}>
              <View
                // width는 `${number}%` 형태의 string을 기대하므로 number에서 조립
                style={[styles.bar, { width: `${percentNum}%`, backgroundColor: barColor }]}
              />
            </View>
            <Text style={[styles.label, it.label === "suspect" && styles.suspect]}>
              {it.label} ({percentLabel}%)
            </Text>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: 8, marginTop: 6 },
  item: { flexDirection: "row", alignItems: "center", gap: 8 },
  time: { width: 60, textAlign: "right", color: "#6b7280", fontVariant: ["tabular-nums"] },
  barWrap: { flex: 1, height: 10, backgroundColor: "#e5e7eb", borderRadius: 6, overflow: "hidden" },
  bar: { height: 10, borderRadius: 6 },
  label: { width: 120, textAlign: "left", color: "#374151" },
  suspect: { color: "#b91c1c", fontWeight: "700" },
  empty: { padding: 12, alignItems: "center" },
  emptyText: { color: "#9ca3af", fontSize: 14 }
});
