# 빠른 시작 가이드

## 현재 상태 ✅

프로젝트 설정이 완료되었습니다:
- ✅ 백엔드 폴더 구성 완료
- ✅ 프론트엔드 폴더 구성 완료
- ✅ Firebase 통합 완료 (deepfake-fc59d)
- ✅ API URL 설정 완료 (10.56.56.5:8000)

## 다음에 할 일

### 1. 가상환경 설정 및 패키지 설치

```bash
cd backend

# 가상환경 생성
python -m venv venv

# 가상환경 활성화
venv\Scripts\activate

# 패키지 설치 (시간이 좀 걸림)
pip install -r ..\requirements.txt
```

### 2. 백엔드 서버 실행

```bash
# 가상환경이 활성화된 상태에서
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

또는 배치 파일 사용:
```bash
.\run_server.bat
```

### 3. 프론트엔드 실행 (다른 터미널)

```bash
cd frontend
npm install  # 이미 설치됨
npm start
```

## Firebase Storage 규칙 확인 ⚠️

Firebase Console에서 Storage 규칙이 설정되어 있는지 확인하세요:

https://console.firebase.google.com/project/deepfake-fc59d/storage/rules

개발용 규칙:
```
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /{allPaths=**} {
      allow read, write: if true;
    }
  }
}
```

## 현재 API 엔드포인트

- **기본 URL**: `http://10.56.56.5:8000`
- **개발 모드**: `__DEV__` 환경에서 자동으로 연결
- **프로덕션**: 별도 설정 필요

## 문제 해결

### 백엔드가 시작되지 않음
- Firebase 키 파일 확인: `backend/firebase-key.json`
- 가상환경 활성화 확인
- Python 버전 확인 (3.8 이상)

### 프론트엔드 연결 안 됨
- 컴퓨터 IP 확인: `ipconfig`
- 같은 WiFi 연결 확인
- 방화벽 8000 포트 허용

## 파일 위치

- 백엔드: `backend/`
- 프론트엔드: `frontend/`
- Firebase 키: `backend/firebase-key.json` (Git에 업로드 안 됨)
- 설정 가이드: `INTEGRATION_GUIDE.md`, `FIREBASE_SETUP_GUIDE.md`


