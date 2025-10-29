import React, { useEffect, useRef, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from "react-native";
import { Camera, CameraView } from "expo-camera";
import * as ImagePicker from "expo-image-picker";
import { useNavigation } from "@react-navigation/native";
import { StackNavigationProp } from "@react-navigation/stack";
import type { RootStackParamList } from "../navigation/AppNavigator";
import { uploadVideoAsync } from "../api/uploadToFirebase";
import { analyzeVideo } from "../api";

type Nav = StackNavigationProp<RootStackParamList, "Record">;

export default function RecordScreen() {
  const navigation = useNavigation<Nav>();
  const cameraRef = useRef<any>(null);
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
  const [mountError, setMountError] = useState<string | null>(null);

  // 초기 권한 요청
  useEffect(() => {
    (async () => {
      console.log("초기 권한 요청 시작");
      
      // 카메라 권한 요청
      try {
        const cameraPerm = await Camera.requestCameraPermissionsAsync();
        console.log("카메라 권한 결과:", cameraPerm);
        
        // 권한 거부된 경우에도 상태 설정 (에뮬레이터에서 카메라 없으면 denied)
        if (!cameraPerm.granted) {
          console.log("카메라 권한이 거부되었습니다. 에뮬레이터일 가능성이 높습니다.");
          // 여전히 초기 선택 화면은 보여주기 위해 상태 설정
          setCamPerm(cameraPerm);
        } else {
          setCamPerm(cameraPerm);
        }
      } catch (e) {
        console.error("카메라 권한 요청 오류:", e);
        // 에뮬레이터에서는 카메라를 사용할 수 없으므로 권한 거부 상태로 설정
        setCamPerm({ granted: false });
      }
      
      // 마이크 권한 요청
      try {
        const mic = await Camera.requestMicrophonePermissionsAsync();
        console.log("마이크 권한 결과:", mic);
        setHasMic(mic.status === "granted");
      } catch (e) {
        console.error("마이크 권한 요청 오류:", e);
        setHasMic(false);
      }
    })();
  }, []);

  // 카메라 초기화 타임아웃 (10초)
  useEffect(() => {
    if (mode === "camera" && !ready) {
      const timer = setTimeout(() => {
        console.log("카메라 초기화 타임아웃 - 강제로 ready 처리");
        setReady(true);
      }, 10000);

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
        // @ts-ignore
        cameraRef.current.stopRecording();
      } catch (e: any) {
        console.error("녹화 정지 오류:", e);
      }
    }
  };

  const pickVideoFromGallery = async () => {
    try {
      console.log("앨범에서 영상 선택 시작...");
      
      // 권한 확인 및 요청
      const perm = await ImagePicker.getMediaLibraryPermissionsAsync();
      console.log("현재 미디어 라이브러리 권한 상태:", perm);
      
      if (!perm.granted) {
        console.log("권한이 없어서 권한 요청 중...");
        const ask = await ImagePicker.requestMediaLibraryPermissionsAsync();
        console.log("권한 요청 결과:", ask);
        
        if (!ask.granted) {
          Alert.alert(
            "권한 필요",
            "갤러리에서 영상을 선택하려면 미디어 라이브러리 접근 권한이 필요합니다.\n설정에서 권한을 허용해주세요.",
            [{ text: "확인" }]
          );
          return;
        }
      }
      
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Videos,
        allowsEditing: false, // 에뮬레이터 호환성 향상을 위해 false로 변경
        quality: 1,
        videoMaxDuration: 60,
        allowsMultipleSelection: false,
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
      
      // 프런트엔드에서의 Firebase 업로드를 건너뛰고, 로컬 파일을 바로 백엔드로 전송
      // (백엔드에서 필요 시 Firebase Admin SDK로 저장 가능)
      console.log("딥페이크 분석 시작... URI:", localUri);
      const res: any = await analyzeVideo(localUri, "user123");
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

  // 권한이 거부되었지만, 초기 선택 화면은 표시 (에뮬레이터에서 앨범 선택 가능)
  // 카메라가 필요한 순간에만 경고 표시

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
          onPress={async () => {
            if (!camPerm?.granted) {
              Alert.alert(
                "카메라 권한 필요", 
                "이 기능을 사용하려면 카메라 권한이 필요합니다.\n에뮬레이터에서는 앨범에서 영상을 선택해주세요.",
                [
                  { text: "앨범 선택", onPress: () => setMode("gallery") },
                  { text: "권한 요청", onPress: async () => {
                    const perm = await requestCamPerm();
                    if (perm.granted) {
                      setMode("camera");
                    }
                  }}
                ]
              );
            } else {
              setMode("camera");
            }
          }}
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
        <CameraView
          key={cameraKey}
          ref={cameraRef}
          style={styles.camera}
          facing={facing}
          mode="video"
          videoQuality="720p"
          onCameraReady={() => {
            console.log("CameraView 준비 완료");
            setReady(true);
            setMountError(null);
          }}
          onMountError={(error: any) => {
            console.error("카메라 마운트 오류:", error);
            const msg = error?.message ?? error?.nativeEvent?.message ?? "카메라 초기화 실패";
            setMountError(msg);
            // 에러가 있어도 5초 후 강제로 ready 처리
            setTimeout(() => {
              setReady(true);
              Alert.alert(
                "카메라 경고", 
                "카메라에 문제가 있을 수 있습니다.\n계속 사용할까요?",
                [
                  { text: "앨범 선택", onPress: () => setMode("gallery") },
                  { text: "계속", onPress: () => {} }
                ]
              );
            }, 5000);
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
          {!mountError && <ActivityIndicator />}
          <Text style={styles.dim}>
            {mountError || (mode === "camera" && !ready ? "카메라 초기화 중…" : "업로드/분석 중…")}
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
