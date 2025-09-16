import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import HomeScreen from '../screens/HomeScreen';
import RecordScreen from '../screens/RecordScreen';
import UploadScreen from '../screens/UploadScreen';
import ResultScreen from '../screens/ResultScreen';
import ReportScreen from '../screens/ReportScreen';
import MetricsScreen from '../screens/MetricsScreen';

// ✅ 스크린 이름과 파라미터 타입 정의
export type RootStackParamList = {
  Home: undefined;
  Record: undefined;
  Upload: undefined;
  Result: { videoId: string };
  Report: undefined;
  Metrics: undefined;
};

const Stack = createStackNavigator<RootStackParamList>();

export default function AppNavigator() {
  return (
    <Stack.Navigator initialRouteName="Home">
      <Stack.Screen name="Home" component={HomeScreen} />
      <Stack.Screen name="Record" component={RecordScreen} />
      <Stack.Screen name="Upload" component={UploadScreen} />
      <Stack.Screen name="Result" component={ResultScreen} />
      <Stack.Screen name="Report" component={ReportScreen} />
      <Stack.Screen name="Metrics" component={MetricsScreen} />
    </Stack.Navigator>
  );
}
