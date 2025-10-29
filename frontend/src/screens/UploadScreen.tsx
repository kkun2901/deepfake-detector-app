import React, { useState } from 'react';
import { View, Text, Button, Alert, StyleSheet, ActivityIndicator } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import { uploadVideoAsync } from '../api/uploadToFirebase';
import { analyzeVideo } from '../api';

type Nav = StackNavigationProp<RootStackParamList, 'Upload'>;

export default function UploadScreen() {
  const navigation = useNavigation<Nav>();
  const [videoUri, setVideoUri] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  
  const ensureMediaPermission = async () => {
    const perm = await ImagePicker.getMediaLibraryPermissionsAsync();
    if (perm.granted) return true;
    const ask = await ImagePicker.requestMediaLibraryPermissionsAsync();
    return ask.granted;
  };

  
  const pickVideo = async () => {
    const ok = await ensureMediaPermission();
    if (!ok) {
      Alert.alert('권한 필요', '갤러리 접근 권한이 필요합니다.');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Videos,
      allowsEditing: false,
      quality: 1,
    });

    if (!result.canceled && result.assets?.[0]?.uri) {
      setVideoUri(result.assets[0].uri);
    }
  };

  
  const handleAnalyze = async () => {
    if (!videoUri) {
      Alert.alert('영상이 선택되지 않았습니다.');
      return;
    }

    try {
      setBusy(true);
      const filename = `video_${Date.now()}.mp4`;
      const firebaseUrl = await uploadVideoAsync(videoUri, filename);

      
      const res: any = await analyzeVideo(firebaseUrl, 'user123');
      const timeline = Array.isArray(res?.timeline) ? res.timeline : undefined;

      
      navigation.navigate('Result', {
        videoUri: firebaseUrl ?? videoUri,
        timeline,
      });
    } catch (error: any) {
      console.error(error);
      Alert.alert('업로드 또는 분석 실패', error?.message ?? '다시 시도해주세요.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <View style={styles.container}>
      <Button title="🎞 영상 선택" onPress={pickVideo} />
      {videoUri && <Text style={styles.text}>선택된 영상: {videoUri}</Text>}

      <View style={{ height: 16 }} />

      <Button
        title={busy ? '처리 중…' : '분석 요청'}
        onPress={handleAnalyze}
        disabled={!videoUri || busy}
        color="#111827"
      />

      {busy && (
        <View style={styles.overlay}>
          <ActivityIndicator size="large" />
          <Text style={styles.dim}>업로드 및 분석 중…</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 20 },
  text: { marginVertical: 10, color: '#374151' },
  overlay: { marginTop: 20, alignItems: 'center' },
  dim: { marginTop: 6, color: '#9ca3af' },
});
