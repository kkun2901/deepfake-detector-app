import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { StackNavigationProp } from '@react-navigation/stack';
import { useNavigation } from '@react-navigation/native';
import { RootStackParamList } from '../navigation/AppNavigator';

type Nav = StackNavigationProp<RootStackParamList, 'Home'>;

export default function HomeScreen() {
  const navigation = useNavigation<Nav>();

  return (
    <View style={styles.container}>
      <Text style={styles.title}>🎬 딥페이크 탐지 앱</Text>

      <TouchableOpacity style={styles.button} onPress={() => navigation.navigate('Upload')}>
        <Text style={styles.buttonText}>📤 영상 업로드</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.button} onPress={() => navigation.navigate('Record')}>
        <Text style={styles.buttonText}>📷 녹화하기</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.ghost} onPress={() => navigation.navigate('Metrics')}>
        <Text style={styles.ghostText}>지표 보기</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, justifyContent: 'center', gap: 16 },
  title: { fontSize: 24, fontWeight: '700', textAlign: 'center', marginBottom: 24 },
  button: { backgroundColor: '#111827', padding: 16, borderRadius: 12 },
  buttonText: { color: 'white', textAlign: 'center', fontSize: 16 },
  ghost: { padding: 12, borderRadius: 12, borderWidth: 1, borderColor: '#ddd' },
  ghostText: { textAlign: 'center', color: '#111827' }
});
