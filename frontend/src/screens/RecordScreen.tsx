import React, { useEffect, useRef, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { Camera, CameraType } from 'expo-camera';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import { uploadVideoAsync } from '../api/uploadToFirebase';
import { analyzeVideo } from '../api';

type NavigationProp = StackNavigationProp<RootStackParamList, 'Record'>;

export default function RecordScreen() {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const cameraRef = useRef<Camera>(null);
  const navigation = useNavigation<NavigationProp>();

  // 권한 요청
  useEffect(() => {
    (async () => {
      const { status: cameraStatus } = await Camera.requestCameraPermissionsAsync();
      const { status: micStatus } = await Camera.requestMicrophonePermissionsAsync();
      setHasPermission(cameraStatus === 'granted' && micStatus === 'granted');
    })();
  }, []);

  // 녹화 시작
  const startRecording = async () => {
    if (!isCameraReady) {
      Alert.alert('카메라 준비 중입니다. 잠시만 기다려주세요.');
      return;
    }

    if (cameraRef.current) {
      try {
        setIsRecording(true);
        const video = await cameraRef.current.recordAsync({
          quality: '720p',
          maxDuration: 30,
        });

        const filename = `recorded_${Date.now()}.mp4`;
        const firebaseUrl = await uploadVideoAsync(video.uri, filename);

        const res = await analyzeVideo(firebaseUrl, 'user123');
        navigation.navigate('Result', { videoId: res.videoId });

      } catch (err) {
        console.error(err);
        Alert.alert('녹화 또는 업로드 실패', '다시 시도해주세요.');
      } finally {
        setIsRecording(false);
      }
    }
  };

  const stopRecording = () => {
    if (cameraRef.current) {
      cameraRef.current.stopRecording();
    }
  };

  if (hasPermission === null) return <View />;
  if (hasPermission === false)
    return <Text>카메라/마이크 접근이 거부되었습니다.</Text>;

  return (
    <View style={styles.container}>
      <Camera
        ref={cameraRef}
        style={styles.camera}
        type={CameraType.front}
        onCameraReady={() => setIsCameraReady(true)}
      />
      <View style={styles.controls}>
        <TouchableOpacity
          onPress={isRecording ? stopRecording : startRecording}
          style={[styles.button, isRecording ? styles.stop : styles.record]}
        >
          <Text style={styles.text}>{isRecording ? '정지' : '녹화 시작'}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  camera: { flex: 1 },
  controls: {
    position: 'absolute',
    bottom: 40,
    alignSelf: 'center',
  },
  button: {
    paddingVertical: 10,
    paddingHorizontal: 30,
    borderRadius: 25,
  },
  record: {
    backgroundColor: 'red',
  },
  stop: {
    backgroundColor: 'gray',
  },
  text: {
    color: '#fff',
    fontSize: 18,
  },
});
