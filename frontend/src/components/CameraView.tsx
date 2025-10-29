import React, { useEffect, useRef, useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from "react-native";
import { Camera, CameraView, useCameraPermissions } from "expo-camera";

export default function CameraViewComponent() {
  const cameraRef = useRef<CameraView>(null);

  // 카메라 권한 훅
  const [permission, requestPermission] = useCameraPermissions();
  // 마이크 권한은 Camera API로 요청
  const [hasMic, setHasMic] = useState<boolean | null>(null);

  const [ready, setReady] = useState(false);
  const [recording, setRecording] = useState(false);
  const [lastUri, setLastUri] = useState<string | null>(null);
  const [facing, setFacing] = useState<"front" | "back">("back");
  const [mountError, setMountError] = useState<string | null>(null);

  // 마이크 권한 요청
  useEffect(() => {
    (async () => {
      const mic = await Camera.requestMicrophonePermissionsAsync();
      setHasMic(mic.status === "granted");
    })();
  }, []);

  // 카메라 초기화 타임아웃 (10초)
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (!ready) {
        console.log("카메라 초기화 타임아웃 - 강제로 ready 처리");
        setReady(true);
      }
    }, 10000);

    return () => clearTimeout(timeout);
  }, [ready]);

  // 언마운트 시 녹화 중지(세션 누수 방지)
  useEffect(() => {
    return () => {
      // @ts-ignore - 타입 정의 이슈 회피
      cameraRef.current?.stopRecording?.();
    };
  }, []);

  const ensurePermissions = async () => {
    if (!permission?.granted) await requestPermission();
    if (!hasMic) {
      const mic = await Camera.requestMicrophonePermissionsAsync();
      setHasMic(mic.status === "granted");
    }
  };

  const startRecording = async () => {
    if (!ready || !cameraRef.current) {
      Alert.alert("잠시만요", "카메라가 아직 준비되지 않았습니다.");
      return;
    }
    if (!hasMic) {
      Alert.alert("권한 필요", "마이크 권한이 필요합니다.");
      await ensurePermissions();
      return;
    }
    try {
      setRecording(true);
      const res = await cameraRef.current.recordAsync({ maxDuration: 60 });
      if (res?.uri) {
        setLastUri(res.uri);
        Alert.alert("녹화 완료", res.uri);
      }
    } catch (e: any) {
      Alert.alert("녹화 오류", e?.message ?? "녹화에 실패했습니다.");
    } finally {
      setRecording(false);
    }
  };

  const stopRecording = () => {
    // @ts-ignore
    cameraRef.current?.stopRecording?.();
  };

  if (!permission) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
        <Text style={styles.dim}>권한 상태 확인 중…</Text>
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={styles.center}>
        <Text style={styles.dim}>카메라 권한이 필요합니다.</Text>
        <TouchableOpacity style={styles.button} onPress={requestPermission}>
          <Text style={styles.btnText}>권한 허용</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CameraView
        ref={cameraRef}
        style={styles.camera}
        facing={facing}
        mode="video"
        videoQuality="1080p" // 해상도는 prop으로!
        onCameraReady={() => {
          console.log("카메라 초기화 완료");
          setReady(true);
          setMountError(null);
        }}
        onMountError={(e: any) => {
          console.log("카메라 마운트 에러:", e);
          const msg = e?.message ?? e?.nativeEvent?.message ?? "카메라 초기화 실패";
          setMountError(msg);
          // 에러가 있어도 5초 후 강제로 ready 처리
          setTimeout(() => setReady(true), 5000);
        }}
      />

      <View style={styles.controls}>
        <TouchableOpacity
          style={[styles.button, styles.switch]}
          onPress={() =>
            setFacing((prev) => (prev === "back" ? "front" : "back"))
          }
          disabled={recording}
        >
          <Text style={styles.btnText}>전/후면 전환</Text>
        </TouchableOpacity>

        {!recording ? (
          <TouchableOpacity
            style={[styles.button, styles.record]}
            onPress={startRecording}
          >
            <Text style={styles.btnText}>● 녹화 시작</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={[styles.button, styles.stop]}
            onPress={stopRecording}
          >
            <Text style={styles.btnText}>■ 정지</Text>
          </TouchableOpacity>
        )}

        {lastUri && (
          <Text style={styles.last} numberOfLines={1}>
            {lastUri}
          </Text>
        )}
      </View>

      {(!ready || mountError) && (
        <View style={styles.overlay}>
          {!mountError && <ActivityIndicator />}
          <Text style={styles.dim}>{mountError || "카메라 초기화 중…"}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000" },
  camera: { flex: 1, borderRadius: 12, overflow: "hidden" },
  controls: {
    position: "absolute",
    bottom: 24,
    left: 0,
    right: 0,
    flexDirection: "row",
    justifyContent: "space-around",
    alignItems: "center",
  },
  button: {
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 999,
    backgroundColor: "#222",
  },
  switch: { backgroundColor: "#374151" },
  record: { backgroundColor: "#dc2626" },
  stop: { backgroundColor: "#6b7280" },
  btnText: { color: "#fff", fontWeight: "600" },
  last: { color: "#e5e7eb", marginTop: 6, fontSize: 12, textAlign: "center" },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#000",
  },
  dim: { color: "#9ca3af", marginTop: 6 },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "rgba(0,0,0,0.35)",
  },
});
