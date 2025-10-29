import React, { useEffect, useRef, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from "react-native";
import { Camera } from "expo-camera";
import * as ImagePicker from "expo-image-picker";
import { useNavigation } from "@react-navigation/native";
import { StackNavigationProp } from "@react-navigation/stack";
import type { RootStackParamList } from "../navigation/AppNavigator";
import { uploadVideoAsync } from "../api/uploadToFirebase";
import { analyzeVideo } from "../api";

type Nav = StackNavigationProp<RootStackParamList, "Record">;

export default function RecordScreen() {
  const navigation = useNavigation<Nav>();
  const cameraRef = useRef<Camera>(null);
  const [camPerm, setCamPerm] = useState<any>(null);
  const requestCamPerm = async () => {
    const result = await Camera.requestCameraPermissionsAsync();
    setCamPerm(result);
    console.log("카메라 권한:", result);
    return result;
  };
  const [hasMic, setHasMic] = useState<boolean | null>(null);
  const [ready, setReady] = useState(false);
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [facing, setFacing] = useState<"front" | "back">("back");
  const [mode, setMode] = useState<"camera" | "gallery" | "select">("select");
  const [cameraKey, setCameraKey] = useState(0);
  const recordingRef = useRef<Promise<any> | null>(null);
  const [initTimeout, setInitTimeout] = useState(false);

  // 초기 권한 요청
  useEffect(() => {
    requestCamPerm();
    (async () => {
      const mic = await Camera.requestMicrophonePermissionsAsync();
      setHasMic(mic.status === "granted");
    })();
  }, []);

  // 카메라 초기화 타임아웃 (5초)
  useEffect(() => {
    if (mode === "camera" && !ready) {
      const timer = setTimeout(() => {
        console.log("카메라 초기화 타임아웃");
        setInitTimeout(true);
        setReady(false);
        Alert.alert(
          "카메라 초기화 실패",
          "에뮬레이터에서 카메라를 사용할 수 없습니다.\n앨범에서 영상을 선택하세요.",
          [
            { text: "취소", onPress: () => setMode("select") },
            { text: "앨범에서 선택", onPress: () => setMode("gallery") }
          ]
        );
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [mode, ready]);

  useEffect(() => {
    return () => {
      // 녹화 중이면 정지
      if (recording && cameraRef.current) {
        // @ts-ignore
        cameraRef.current.stopRecording?.();
      }
    };
  }, [recording]);

  // 모드 전환 시 카메라 재초기화
  useEffect(() => {
    if (mode === "camera") {
      console.log("카메라 모드로 전환, 카메라 재초기화");
      setReady(false);
      setCameraKey(prev => prev + 1);
    }
  }, [mode]);

  const ensurePermissions = async () => {
    if (!camPerm?.granted) await requestCamPerm();
    if (!hasMic) {
      const res = await Camera.requestMicrophonePermissionsAsync();
      setHasMic(res.status === "granted");
    }
  };

  const startRecording = async () => {
    console.log("=== 녹화 시작 시도 ===");
    console.log("상태:", { ready, hasMic, camRef: !!cameraRef.current });
    
    if (!ready) {
      Alert.alert("잠시만요", "카메라가 아직 준비되지 않았습니다.");
      return;
    }
    
    try {
      console.log("1. 권한 재확인 중...");
      
      const micPermission = await Camera.requestMicrophonePermissionsAsync();
      if (micPermission.status !== "granted") {
        Alert.alert("권한 필요", "마이크 권한이 필요합니다.");
        return;
      }
      
      if (!cameraRef.current) {
        throw new Error("Camera 참조가 없습니다.");
      }
      
      console.log("2. 카메라 안정화 대기...");
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      console.log("3. 녹화 상태 설정...");
      setRecording(true);
      
      console.log("4. 녹화 시작 - recordAsync 호출 (옵션 없이)");
      
      // 녹화 시작 - 백그라운드에서 처리 (옵션 없이 시도)
      recordingRef.current = cameraRef.current.recordAsync()
      .then((result: any) => {
        console.log("녹화 완료! URI:", result?.uri);
        setRecording(false);
        if (result?.uri) {
          handleAnalyze(result.uri).catch((e: any) => {
            console.error("분석 오류:", e);
          });
        }
      })
      .catch((e: any) => {
        console.error("녹화 실패:", e);
        Alert.alert("녹화 오류", `녹화에 실패했습니다: ${e?.message || "알 수 없는 오류"}`);
        setRecording(false);
      });
      
      console.log("녹화 시작 완료 - Promise:", recordingRef.current);
      
    } catch (e: any) {
      console.error("=== 녹화 오류 상세 ===");
      console.error("오류:", e);
      Alert.alert("녹화 오류", `녹화를 시작할 수 없습니다: ${e?.message || "알 수 없는 오류"}`);
      setRecording(false);
    }
  };

  const stopRecording = async () => {
    if (cameraRef.current && recording) {
      console.log("녹화 정지 중...");
      try {
        cameraRef.current.stopRecording();
      } catch (e: any) {
        console.error("녹화 정지 오류:", e);
      }
    }
  };

  const pickVideoFromGallery = async () => {
    try {
      console.log("앨범에서 영상 선택 시작...");
      
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Videos,
        allowsEditing: true,
        quality: 1,
        videoMaxDuration: 60,
      });

      console.log("앨범 선택 결과:", result);

      if (!result.canceled && result.assets && result.assets[0]) {
        console.log("선택된 영상:", result.assets[0]);
        await handleAnalyze(result.assets[0].uri);
      } else {
        console.log("사용자가 선택을 취소했습니다.");
      }
    } catch (e: any) {
      console.error("앨범 선택 오류 상세:", e);
      Alert.alert("앨범 선택 오류", `영상을 선택할 수 없습니다: ${e?.message || e?.toString() || "알 수 없는 오류"}`);
    }
  };

  const handleAnalyze = async (localUri: string) => {
    if (busy) return;
    try {
      console.log("영상 분석 시작:", localUri);
      setBusy(true);
      
      const filename = `recorded_${Date.now()}.mp4`;
      console.log("파일명:", filename);
      
      // Firebase 업로드 시도, 실패 시 로컬 파일 사용
      let videoUrl = localUri;
      try {
        console.log("Firebase 업로드 시도...");
        const firebaseUrl = await uploadVideoAsync(localUri, filename);
        console.log("Firebase 업로드 완료:", firebaseUrl);
        videoUrl = firebaseUrl;
      } catch (firebaseError: any) {
        console.warn("Firebase 업로드 실패, 로컬 파일 사용:", firebaseError);
        Alert.alert(
          "업로드 실패", 
          "Firebase 업로드에 실패했습니다. 로컬 파일로 분석을 진행합니다.",
          [{ text: "확인", onPress: () => {} }]
        );
      }
      
      console.log("딥페이크 분석 시작... URL:", videoUrl);
      const res: any = await analyzeVideo(videoUrl, "user123");
      console.log("분석 결과:", res);
      
      const timeline = Array.isArray(res?.timeline) ? res.timeline : undefined;
      console.log("타임라인:", timeline);
      
      navigation.navigate("Result", {
        videoUri: videoUrl,
        timeline,
      });
    } catch (e: any) {
      console.error("분석 과정 오류 상세:", e);
      Alert.alert("분석 실패", `분석 중 오류가 발생했습니다: ${e?.message || e?.toString() || "알 수 없는 오류"}`);
    } finally {
      setBusy(false);
    }
  };

  if (!camPerm || hasMic === null) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
        <Text style={styles.dim}>권한 상태 확인 중…</Text>
      </View>
    );
  }

  if (!camPerm.granted) {
    return (
      <View style={styles.center}>
        <Text style={styles.dim}>카메라 권한이 필요합니다.</Text>
        <TouchableOpacity style={[styles.button, styles.record]} onPress={requestCamPerm}>
          <Text style={styles.btnText}>권한 허용</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!hasMic) {
    return (
      <View style={styles.center}>
        <Text style={styles.dim}>마이크 권한이 필요합니다.</Text>
        <TouchableOpacity style={[styles.button, styles.record]} onPress={ensurePermissions}>
          <Text style={styles.btnText}>권한 다시 요청</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // 초기 선택 화면
  if (mode === "select") {
    return (
      <View style={styles.selectContainer}>
        <View style={styles.selectHeader}>
          <Text style={styles.selectTitle}>딥페이크 분석</Text>
          <Text style={styles.selectSubtitle}>영상을 선택해주세요</Text>
        </View>

        <View style={styles.selectButtons}>
          <TouchableOpacity
            style={styles.selectButton}
            onPress={() => setMode("camera")}
            disabled={busy}
          >
            <Text style={styles.selectButtonIcon}>📷</Text>
            <Text style={styles.selectButtonTitle}>카메라로 녹화</Text>
            <Text style={styles.selectButtonSubtitle}>실시간으로 영상을 녹화하여 분석</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.selectButton}
            onPress={() => setMode("gallery")}
            disabled={busy}
          >
            <Text style={styles.selectButtonIcon}>🎬</Text>
            <Text style={styles.selectButtonTitle}>앨범에서 선택</Text>
            <Text style={styles.selectButtonSubtitle}>기존 영상을 선택하여 분석</Text>
          </TouchableOpacity>
        </View>

        {busy && (
          <View style={styles.busyOverlay}>
            <ActivityIndicator size="large" color="#2563eb" />
            <Text style={styles.busyText}>처리 중...</Text>
          </View>
        )}
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {mode === "camera" ? (
        <Camera
          key={cameraKey}
          ref={cameraRef}
          style={styles.camera}
          type={facing as any}
          onCameraReady={() => {
            console.log("Camera 컴포넌트 준비 완료");
            setReady(true);
            setInitTimeout(false);
          }}
          onMountError={(error) => {
            console.error("카메라 마운트 오류:", error);
            Alert.alert("카메라 오류", "카메라를 사용할 수 없습니다.\n앨범에서 영상을 선택해주세요.", [
              { text: "확인", onPress: () => setMode("gallery") }
            ]);
          }}
        />
      ) : (
        <View style={styles.galleryPlaceholder}>
          <Text style={styles.galleryText}>🎬</Text>
          <Text style={styles.gallerySubtitle}>앨범에서 영상 선택</Text>
          <Text style={styles.gallerySubtext}>아래 버튼을 눌러 갤러리에서 영상을 선택하세요</Text>
          <Text style={styles.galleryHint}>• 최대 60초 영상</Text>
          <Text style={styles.galleryHint}>• MP4, MOV 형식 지원</Text>
        </View>
      )}

      <View style={styles.modeToggle}>
        <TouchableOpacity
          style={[styles.modeButton, mode === "camera" && styles.modeButtonActive]}
          onPress={() => setMode("camera")}
          disabled={busy}
        >
          <Text style={[styles.modeButtonText, mode === "camera" && styles.modeButtonTextActive]}>
            📷 카메라
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.modeButton, mode === "gallery" && styles.modeButtonActive]}
          onPress={() => setMode("gallery")}
          disabled={busy}
        >
          <Text style={[styles.modeButtonText, mode === "gallery" && styles.modeButtonTextActive]}>
            🎬 앨범
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.modeButton, styles.backButton]}
          onPress={() => setMode("select")}
          disabled={busy}
        >
          <Text style={styles.modeButtonText}>← 뒤로</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.controls}>
        {mode === "camera" ? (
          <>
            {!recording ? (
              <TouchableOpacity
                style={[styles.button, styles.record]}
                onPress={startRecording}
                disabled={busy}
              >
                <Text style={styles.btnText}>{busy ? "처리 중…" : "● 녹화 시작"}</Text>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity style={[styles.button, styles.stop]} onPress={stopRecording}>
                <Text style={styles.btnText}>■ 정지</Text>
              </TouchableOpacity>
            )}

            <TouchableOpacity
              style={[styles.button, styles.secondary]}
              onPress={() => setFacing((p) => (p === "back" ? "front" : "back"))}
              disabled={recording || busy}
            >
              <Text style={styles.btnText}>카메라 전환</Text>
            </TouchableOpacity>
          </>
        ) : (
          <TouchableOpacity
            style={[styles.button, styles.record]}
            onPress={pickVideoFromGallery}
            disabled={busy}
          >
            <Text style={styles.btnText}>{busy ? "처리 중…" : "🎬 앨범에서 선택"}</Text>
          </TouchableOpacity>
        )}
      </View>

      {((mode === "camera" && !ready) || busy) && (
        <View style={styles.overlay}>
          <ActivityIndicator />
          <Text style={styles.dim}>
            {mode === "camera" && !ready ? "카메라 초기화 중…" : "업로드/분석 중…"}
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  // 초기 선택 화면 스타일
  selectContainer: { 
    flex: 1, 
    backgroundColor: "#000", 
    paddingHorizontal: 20, 
    paddingTop: 60 
  },
  selectHeader: { 
    alignItems: "center", 
    marginBottom: 60 
  },
  selectTitle: { 
    fontSize: 28, 
    fontWeight: "bold", 
    color: "#fff", 
    marginBottom: 8 
  },
  selectSubtitle: { 
    fontSize: 16, 
    color: "#9ca3af" 
  },
  selectButtons: { 
    gap: 20 
  },
  selectButton: { 
    backgroundColor: "#1f2937", 
    borderRadius: 16, 
    padding: 24, 
    alignItems: "center",
    borderWidth: 2,
    borderColor: "transparent"
  },
  selectButtonIcon: { 
    fontSize: 48, 
    marginBottom: 16 
  },
  selectButtonTitle: { 
    fontSize: 20, 
    fontWeight: "bold", 
    color: "#fff", 
    marginBottom: 8 
  },
  selectButtonSubtitle: { 
    fontSize: 14, 
    color: "#9ca3af", 
    textAlign: "center" 
  },
  busyOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0,0,0,0.8)",
    justifyContent: "center",
    alignItems: "center"
  },
  busyText: {
    color: "#fff",
    marginTop: 16,
    fontSize: 16
  },

  // 기존 스타일들
  container: { flex: 1, backgroundColor: "#000" },
  camera: { flex: 1 },
  galleryPlaceholder: { 
    flex: 1, 
    justifyContent: "center", 
    alignItems: "center", 
    backgroundColor: "#1f2937",
    paddingHorizontal: 20
  },
  galleryText: { fontSize: 64, marginBottom: 16 },
  gallerySubtitle: { color: "#fff", fontSize: 20, fontWeight: "bold", marginBottom: 8 },
  gallerySubtext: { color: "#9ca3af", fontSize: 16, textAlign: "center", marginBottom: 16 },
  galleryHint: { color: "#6b7280", fontSize: 14, marginBottom: 4 },
  modeToggle: { 
    position: "absolute", 
    top: 50, 
    left: 20, 
    right: 20, 
    flexDirection: "row", 
    backgroundColor: "rgba(0,0,0,0.7)", 
    borderRadius: 25, 
    padding: 4 
  },
  modeButton: { 
    flex: 1, 
    paddingVertical: 8, 
    paddingHorizontal: 16, 
    borderRadius: 20, 
    alignItems: "center" 
  },
  modeButtonActive: { backgroundColor: "#2563eb" },
  backButton: { backgroundColor: "#374151", flex: 0.5 },
  modeButtonText: { color: "#9ca3af", fontWeight: "600" },
  modeButtonTextActive: { color: "#fff" },
  controls: { position: "absolute", bottom: 28, alignSelf: "center", gap: 10, width: "90%" },
  button: { paddingVertical: 12, borderRadius: 12, alignItems: "center" },
  record: { backgroundColor: "#dc2626" },
  stop: { backgroundColor: "#6b7280" },
  secondary: { backgroundColor: "#1f2937" },
  btnText: { color: "#fff", fontWeight: "700" },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#000" },
  dim: { color: "#9ca3af", marginTop: 6, textAlign: "center" },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "rgba(0,0,0,0.35)",
    paddingHorizontal: 16,
  },
});
