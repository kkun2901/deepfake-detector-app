// src/api/uploadToFirebase.ts
import { storage } from './firebase';
import { ref, uploadBytesResumable, getDownloadURL } from 'firebase/storage';
import * as FileSystem from 'expo-file-system';

export async function uploadVideoAsync(localUri: string, filename: string): Promise<string> {
  try {
    console.log("Firebase 업로드 시작:", localUri);
    
    // 파일 정보 확인
    const fileInfo = await FileSystem.getInfoAsync(localUri);
    console.log("파일 정보:", fileInfo);
    
    if (!fileInfo.exists) {
      throw new Error("파일이 존재하지 않습니다.");
    }
    
    // Firebase Storage 참조 생성
    const storageRef = ref(storage, `videos/${filename}`);
    
    // 파일을 바이너리로 읽기
    const fileContent = await FileSystem.readAsStringAsync(localUri, {
      encoding: FileSystem.EncodingType.Base64,
    });
    
    console.log("파일 읽기 완료, 크기:", fileContent.length);
    
    // Base64를 바이너리 배열로 변환
    const binaryString = atob(fileContent);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    
    console.log("바이너리 변환 완료, 바이트 수:", bytes.length);
    
    // 메타데이터 설정
    const metadata = {
      contentType: 'video/mp4',
      customMetadata: {
        uploadedAt: new Date().toISOString(),
        originalName: filename
      }
    };

    console.log("Firebase 업로드 시작...");
    
    // uploadBytesResumable 사용 (더 안정적)
    const uploadTask = uploadBytesResumable(storageRef, bytes, metadata);
    
    // 업로드 완료 대기
    const snapshot = await uploadTask;
    console.log("업로드 완료:", snapshot);
    
    // 다운로드 URL 가져오기
    const downloadURL = await getDownloadURL(snapshot.ref);
    console.log("다운로드 URL:", downloadURL);
    
    return downloadURL;
  } catch (error) {
    console.error("Firebase 업로드 오류:", error);
    throw error;
  }
}
