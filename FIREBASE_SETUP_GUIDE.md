# Firebase 설정 가이드

## 현재 상태

✅ **백엔드**: `deepfake-fc59d` 프로젝트로 설정 완료
- 위치: `backend/firebase-key.json`
- Firebase Admin SDK 사용

⚠️ **프론트엔드**: Firebase 설정 업데이트 필요
- 위치: `frontend/src/api/firebase.ts`
- Firebase JS SDK 설정 필요

## 프론트엔드 Firebase 설정 방법

### 1. Firebase Console 접속
https://console.firebase.google.com/

### 2. 프로젝트 선택
- `deepfake-fc59d` 프로젝트 선택

### 3. 앱 추가 (Web 앱으로 추가)
1. 설정 ⚙️ → 프로젝트 설정
2. "내 앱" 섹션에서 "웹" 아이콘 클릭
3. 앱 닉네임 입력 (예: "deepfake-app")
4. Firebase Hosting 체크해도 되고 안 해도 됨

### 4. Firebase 설정 코드 복사
다음 정보를 복사:
```javascript
apiKey: "YOUR_API_KEY"
authDomain: "deepfake-fc59d.firebaseapp.com"
projectId: "deepfake-fc59d"
storageBucket: "deepfake-fc59d.firebasestorage.app"
messagingSenderId: "YOUR_SENDER_ID"
appId: "YOUR_APP_ID"
```

### 5. `frontend/src/api/firebase.ts` 파일 업데이트
복사한 정보로 교체:
```typescript
const firebaseConfig = {
  apiKey: "복사한_API_KEY",
  authDomain: "deepfake-fc59d.firebaseapp.com",
  projectId: "deepfake-fc59d",
  storageBucket: "deepfake-fc59d.firebasestorage.app",
  messagingSenderId: "복사한_SENDER_ID",
  appId: "복사한_APP_ID"
};
```

### 6. Storage 규칙 설정 (중요!)
Firebase Console → Storage → 규칙:
```json
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /{allPaths=**} {
      allow read, write: if true;  // 개발용: 모두 허용
    }
  }
}
```
⚠️ **프로덕션에서는 보안 규칙을 설정해야 합니다!**

## 현재 프로젝트 정보

- **백엔드 프로젝트**: `deepfake-fc59d`
- **Storage Bucket**: `deepfake-fc59d.firebasestorage.app`
- **Service Account**: `firebase-adminsdk-fbsvc@deepfake-fc59d.iam.gserviceaccount.com`

## 빠른 확인 방법

### 백엔드 Firebase 확인
```bash
cd backend
python -c "from core.firebase import db, bucket; print('Firebase 연결 성공!')"
```

### 프론트엔드 Firebase 확인
Expo 앱에서 API 호출 테스트

## 문제 해결

### Firebase 연결 오류
1. `firebase-key.json` 파일 위치 확인
2. Service Account 권한 확인
3. Storage 규칙 확인

### Storage 업로드 실패
1. Storage 규칙이 적절한지 확인
2. Storage가 활성화되어 있는지 확인
3. 네트워크 연결 확인
