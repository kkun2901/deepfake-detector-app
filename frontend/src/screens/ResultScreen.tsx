import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, FlatList } from 'react-native';
import { fetchAnalysisResult } from '../api';
import { RouteProp } from '@react-navigation/native';
import { RootStackParamList } from '../navigation/AppNavigator';
type ResultRouteProp = RouteProp<RootStackParamList, 'Result'>;

interface TimelineItem {
  start: number;
  end: number;
  ensemble_result: 'real' | 'fake';
  confidence: number;
}

export default function ResultScreen({ route }: { route: ResultRouteProp }) {
  const { videoId } = route.params;
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadResult = async () => {
      try {
        const result = await fetchAnalysisResult(videoId);
        setTimeline(result.timeline);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadResult();
  }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
        <Text>결과 불러오는 중...</Text>
      </View>
    );
  }

  const renderItem = ({ item }: { item: TimelineItem }) => {
    const isFake = item.ensemble_result === 'fake';
    return (
      <View style={[styles.block, isFake ? styles.fake : styles.real]}>
        <Text style={styles.text}>
          ⏱ {item.start.toFixed(1)} ~ {item.end.toFixed(1)}초
        </Text>
        <Text style={styles.text}>
          결과: {isFake ? '❌ 딥페이크' : '✅ 정상'} | 신뢰도: {(item.confidence * 100).toFixed(1)}%
        </Text>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>🔎 탐지 결과</Text>
      <FlatList
        data={timeline}
        keyExtractor={(_, index) => index.toString()}
        renderItem={renderItem}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  title: { fontSize: 22, fontWeight: 'bold', marginBottom: 10 },
  block: {
    padding: 12,
    borderRadius: 10,
    marginBottom: 10,
  },
  fake: {
    backgroundColor: '#ffe5e5',
    borderLeftWidth: 5,
    borderLeftColor: 'red',
  },
  real: {
    backgroundColor: '#e5ffe5',
    borderLeftWidth: 5,
    borderLeftColor: 'green',
  },
  text: {
    fontSize: 16,
  },
});
