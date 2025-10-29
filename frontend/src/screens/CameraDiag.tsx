// src/screens/CameraDiag.tsx
import React, { useEffect, useRef, useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from "react-native";
import { Camera, CameraView, useCameraPermissions } from "expo-camera";

type Facing = "front" | "back";

export default function CameraDiag() {
  const camRef = useRef<CameraView>(null);

  const [camPerm, requestCamPerm] = useCameraPermissions();
  const [hasMic, setHasMic] = useState<boolean | null>(null);

  const [ready, setReady] = useState(false);
  const [recording, setRecording] = useState(false);
  const [facing, setFacing] = useState<Facing>("back");
  const [mountError, setMountError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const mic = await Camera.requestMicrophonePermissionsAsync();
      setHasMic(mic.status === "granted");
    })();
  }, []);

  useEffect(() => {
    return () => {
      // @ts-ignore
      camRef.current?.stopRecording?.();
    };
  }, []);

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
        <TouchableOpacity style={[styles.btn, styles.primary]} onPress={requestCamPerm}>
          <Text style={styles.btnText}>권한 허용</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!hasMic) {
    return (
      <View style={styles.center}>
        <Text style={styles.dim}>마이크 권한이 필요합니다.</Text>
        <TouchableOpacity
          style={[styles.btn, styles.primary]}
          onPress={async () => {
            const mic = await Camera.requestMicrophonePermissionsAsync();
            setHasMic(mic.status === "granted");
          }}
        >
          <Text style={styles.btnText}>마이크 권한 요청</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CameraView
        ref={camRef}
        style={styles.camera}
        facing={facing}
        mode="video"
        videoQuality="720p"
        onCameraReady={() => setReady(true)}
        onMountError={(e: any) => {
          const msg = e?.message ?? e?.nativeEvent?.message ?? "카메라 초기화 실패";
          setMountError(msg);
        }}
      />

      <View style={styles.controls}>
        <TouchableOpacity
          style={[styles.btn, styles.secondary]}
          onPress={() => setFacing((p) => (p === "back" ? "front" : "back"))}
          disabled={recording}
        >
          <Text style={styles.btnText}>전/후면 전환</Text>
        </TouchableOpacity>

        {!recording ? (
          <TouchableOpacity
            style={[styles.btn, styles.primary]}
            onPress={async () => {
              if (!ready || !camRef.current) return;
              try {
                setRecording(true);
                // @ts-ignore
                const res = await camRef.current.recordAsync({ maxDuration: 5 });
                console.log("diag recorded:", res?.uri);
              } finally {
                setRecording(false);
              }
            }}
          >
            <Text style={styles.btnText}>테스트 녹화</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={[styles.btn, styles.danger]}
            onPress={() => {
              // @ts-ignore
              camRef.current?.stopRecording?.();
            }}
          >
            <Text style={styles.btnText}>정지</Text>
          </TouchableOpacity>
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
  camera: { flex: 1 },
  controls: { position: "absolute", bottom: 20, left: 0, right: 0, flexDirection: "row", justifyContent: "space-around" },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#000" },
  dim: { color: "#9ca3af", marginTop: 8 },
  overlay: { ...StyleSheet.absoluteFillObject, justifyContent: "center", alignItems: "center", backgroundColor: "rgba(0,0,0,0.35)" },
  btn: { paddingVertical: 10, paddingHorizontal: 18, borderRadius: 999 },
  primary: { backgroundColor: "#2563eb" },
  secondary: { backgroundColor: "#374151" },
  danger: { backgroundColor: "#ef4444" },
  btnText: { color: "#fff", fontWeight: "700" }
});
