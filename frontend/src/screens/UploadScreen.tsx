import React, { useState } from 'react';
import { View, Text, Button, Alert, StyleSheet } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { analyzeVideo } from '../api';
import { RootStackParamList } from '../navigation/AppNavigator';
import { uploadVideoAsync } from '../api/uploadToFirebase';

type NavigationProp = StackNavigationProp<RootStackParamList, 'Upload'>;

export default function UploadScreen() {
  const [videoUri, setVideoUri] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const navigation = useNavigation<NavigationProp>();

  const pickVideo = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Videos,
      allowsEditing: false,
      quality: 1,
    });

    if (!result.canceled && result.assets?.length) {
      const uri = result.assets[0].uri;
      setVideoUri(uri);
    }
  };

  const handleAnalyze = async () => {
    if (!videoUri) {
      Alert.alert('영상이 선택되지 않았습니다.');
      return;
    }

    try {
      setUploading(true);
      const filename = `video_${Date.now()}.mp4`;
      const firebaseUrl = await uploadVideoAsync(videoUri, filename);

      const res = await analyzeVideo(firebaseUrl, 'user123');
      navigation.navigate('Result', { videoId: res.videoId });
    } catch (error) {
      console.error(error);
      Alert.alert('업로드 또는 분석 실패', '다시 시도해주세요.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Button title="영상 선택" onPress={pickVideo} />
      {videoUri && <Text style={styles.text}>선택된 영상: {videoUri}</Text>}
      <Button
        title={uploading ? '업로드 중...' : '분석 요청'}
        onPress={handleAnalyze}
        disabled={!videoUri || uploading}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 20 },
  text: { marginVertical: 10 },
});
