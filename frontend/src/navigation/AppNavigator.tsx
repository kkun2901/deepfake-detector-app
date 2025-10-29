// src/navigation/AppNavigator.tsx
import React from "react";
import { createStackNavigator } from "@react-navigation/stack";

import HomeScreen from "../screens/HomeScreen";
import RecordScreen from "../screens/RecordScreen";
import UploadScreen from "../screens/UploadScreen";
import ResultScreen from "../screens/ResultScreen";
import ReportScreen from "../screens/ReportScreen";
import MetricsScreen from "../screens/MetricsScreen";
import CameraSmokeTest from "../screens/CameraSmokeTest";

export type RootStackParamList = {
  Home: undefined;
  Record: undefined;
  Upload: undefined;
  Result:
    | {
        videoUri?: string;
        timeline?: Array<{ t: number; label: "suspect" | "normal"; score: number }>;
        videoId?: string;
      }
    | undefined;
  Report: { videoUri?: string } | undefined;
  Metrics: undefined;
  CameraSmoke: undefined;
};

const Stack = createStackNavigator<RootStackParamList>();

export default function AppNavigator() {
  return (
    <Stack.Navigator
      initialRouteName="Home" // Home 화면부터 시작
      screenOptions={{ headerTitleAlign: "center" }}
    >
      <Stack.Screen name="CameraSmoke" component={CameraSmokeTest} options={{ title: "카메라 테스트" }} />
      <Stack.Screen name="Home" component={HomeScreen} options={{ title: "🎬 딥페이크 탐지" }} />
      <Stack.Screen name="Record" component={RecordScreen} options={{ title: "녹화하기" }} />
      <Stack.Screen name="Upload" component={UploadScreen} options={{ title: "영상 업로드" }} />
      <Stack.Screen name="Result" component={ResultScreen} options={{ title: "분석 결과" }} />
      <Stack.Screen name="Report" component={ReportScreen} options={{ title: "신고하기" }} />
      <Stack.Screen name="Metrics" component={MetricsScreen} options={{ title: "지표" }} />
    </Stack.Navigator>
  );
}
