import React, { useEffect, useMemo, useState } from "react";
import { View, Text, StyleSheet, ActivityIndicator, ScrollView, Alert } from "react-native";
import { useRoute, RouteProp, useNavigation } from "@react-navigation/native";
import { StackNavigationProp } from "@react-navigation/stack";
import type { RootStackParamList } from "../navigation/AppNavigator";
import { fetchAnalysisResult } from "../api";
import Timeline from "../components/Timeline";
import VideoPlayer from "../components/VideoPlayer";
import type { TimelineItem } from "../types/common";

// --------- 타입들 ---------
type R = RouteProp<RootStackParamList, "Result">;
type Nav = StackNavigationProp<RootStackParamList, "Result">;

type ServerTimelineItem = {
  start: number;
  end: number;
  ensemble_result: "real" | "fake";
  confidence: number; // 서버가 0~1 또는 0~100을 줄 수 있음
};

// --------- 유틸 ---------
const normalizeScore = (v: unknown): number => {
  const n = Number(v);
  if (!isFinite(n) || isNaN(n)) return 0;
  if (n > 1.000001) return Math.min(n / 100, 1); // 100기반이면 0~1로
  if (n < 0) return 0;
  return Math.min(n, 1);
};
const toLabel = (x: any): "suspect" | "normal" => (x === "suspect" ? "suspect" : "normal");

export default function ResultScreen() {
  const route = useRoute<R>();
  const navigation = useNavigation<Nav>();
  const params = route.params ?? {};

  const [loading, setLoading] = useState(false);
  const [serverTL, setServerTL] = useState<ServerTimelineItem[] | null>(null);

  // 파라미터(유연하게 받되 내부에선 엄격 타입으로 변환)
  const videoUri = (params as any)?.videoUri as string | undefined;
  const passedTimelineRaw = (params as any)?.timeline as unknown;
  const legacyVideoId = (params as any)?.videoId as string | undefined;

  // 서버 조회 (타임라인이 안 넘어오고 videoId만 있을 때)
  useEffect(() => {
    const needFetch = !Array.isArray(passedTimelineRaw) && !!legacyVideoId;
    if (!needFetch) return;

    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const result = await fetchAnalysisResult(legacyVideoId!);
        const tl = Array.isArray(result?.timeline) ? (result.timeline as ServerTimelineItem[]) : null;

        if (!cancelled) {
          if (tl && tl.length > 0) setServerTL(tl);
          else {
            setServerTL([]);
            Alert.alert("결과 없음", "타임라인 데이터를 찾을 수 없습니다.");
          }
        }
      } catch (err: any) {
        console.error(err);
        if (!cancelled) Alert.alert("불러오기 실패", err?.message ?? "결과를 불러오지 못했습니다.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [legacyVideoId, passedTimelineRaw]);

  // 파라미터로 온 타임라인을 안전하게 TimelineItem[]로 변환
  const passedTimeline: TimelineItem[] | undefined = useMemo(() => {
    if (!Array.isArray(passedTimelineRaw)) return undefined;
    return passedTimelineRaw
      .map((it: any): TimelineItem => ({
        t: Number(it?.t),
        label: toLabel(it?.label),
        score: normalizeScore(it?.score),
      }))
      .filter((it) => isFinite(it.t));
  }, [passedTimelineRaw]);

  // 최종 타임라인
  const unifiedTimeline: TimelineItem[] = useMemo(() => {
    if (passedTimeline && passedTimeline.length > 0) return passedTimeline;
    if (serverTL) {
      return serverTL
        .map(
          (it): TimelineItem => ({
            t: (Number(it.start) + Number(it.end)) / 2,
            label: it.ensemble_result === "fake" ? "suspect" : "normal",
            score: normalizeScore(it.confidence),
          })
        )
        .filter((it) => isFinite(it.t));
    }
    return [];
  }, [passedTimeline, serverTL]);

  const maxScore = useMemo(() => {
    if (unifiedTimeline.length === 0) return 0;
    return Math.max(...unifiedTimeline.map((x) => normalizeScore(x.score)));
  }, [unifiedTimeline]);

  const risk = useMemo(() => {
    const HIGH = 0.85,
      MID = 0.6,
      WARN = 0.3;
    if (maxScore > HIGH) return "높음";
    if (maxScore > MID) return "중간";
    if (maxScore > WARN) return "주의";
    return "낮음";
  }, [maxScore]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
        <Text style={styles.dim}>결과 불러오는 중…</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 24 }}>
      <Text style={styles.title}>🔎 탐지 결과</Text>

      <View style={styles.card}>
        <Text style={styles.line}>
          최대 의심 점수: <Text style={styles.bold}>{(maxScore * 100).toFixed(1)}%</Text>
        </Text>
        <Text style={styles.line}>위험도: {risk}</Text>
      </View>

      {videoUri ? (
        <>
          <Text style={styles.header}>영상</Text>
          <VideoPlayer uri={videoUri} />
        </>
      ) : null}

      <Text style={styles.header}>타임라인</Text>
      {unifiedTimeline.length > 0 ? (
        <Timeline data={unifiedTimeline} />
      ) : (
        <Text style={styles.dim}>표시할 타임라인이 없습니다.</Text>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 22, fontWeight: "700", marginBottom: 12 },
  header: { marginTop: 16, marginBottom: 8, fontSize: 18, fontWeight: "700" },
  card: {
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#e5e7eb",
    backgroundColor: "#fff",
    marginBottom: 8,
  },
  line: { color: "#374151", marginBottom: 4 },
  bold: { fontWeight: "700", color: "#111827" },
  dim: { color: "#6b7280" },
});
