# 프로젝트 설정 체크리스트

## ✅ 완료된 항목

1. ✅ 백엔드 폴더 구성 완료
   - `backend/` 폴더 존재
   - `main.py`, `requirements.txt` 존재

2. ✅ 프론트엔드 폴더 구성 완료
   - `frontend/` 폴더 존재
   - `package.json`, `App.tsx`, `app.json` 존재
   - TypeScript 설정 완료

3. ✅ CORS 설정 완료
   - `backend/main.py`에서 모든 origin 허용

4. ✅ API URL 설정
   - `frontend/src/api/index.ts`에서 개발/프로덕션 분리
   - 현재 IP: `10.56.56.5:8000` (__DEV__ 모드 사용)

## ⚠️ 필수 확인 사항

### 1. Firebase 키 파일 (중요!)

```bash
backend/firebase-key.json 파일이 실제 Firebase 키로 교체되어야 합니다.

현재: 플레이스홀더만 있음
필요: Firebase Console에서 키 파일 다운로드
```

**방법:**
1. Firebase Console 접속: https://console.firebase.google.com/
2. 프로젝트 선택: `deepfake-89954`
3. 설정 → 서비스 계정 → 새 비공개 키 생성
4. `backend/firebase-key.json` 파일 교체

### 2. 현재 네트워크 IP 확인

```bash
# 현재 설정된 IP: 10.56.56.5:8000
# 변경이 필요한 경우 frontend/src/api/index.ts 수정
```

**IP 확인 방법:**
```bash
ipconfig  # Windows
ifconfig  # Mac/Linux
```

### 3. 백엔드 서버 실행

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r ..\requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 프론트엔드 실행

```bash
cd frontend
npm install
npm start
```

### 5. 모바일 기기 연결

⚠️ **필수:** 컴퓨터와 모바일이 같은 WiFi에 연결되어야 함

## 📋 개발 워크플로우

### 매일 시작 전

```bash
# 1. IP 확인 (변경되었을 수 있음)
ipconfig

# 2. IP 변경되었다면 frontend/src/api/index.ts 수정
const API_BASE_URL = 'http://[새로운IP]:8000';

# 3. 백엔드 시작
cd backend
venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. 프론트엔드 시작 (다른 터미널)
cd frontend
npm start
```

## 🚨 문제 해결

### 백엔드가 시작되지 않음
- Firebase 키 파일 확인
- Python 가상환경 활성화 확인
- `requirements.txt` 패키지 설치 확인

### 앱에서 서버에 연결 안 됨
- IP 주소 확인 (`ipconfig`)
- 같은 WiFi 연결 확인
- 방화벽에서 8000 포트 허용
- 백엔드가 `--host 0.0.0.0`으로 실행되었는지 확인

### API 500 에러
- 백엔드 터미널에서 로그 확인
- Firebase 키 파일 확인
- 모델 파일 존재 확인

## 📝 참고

- 백엔드 문서: http://localhost:8000/docs
- 현재 백엔드 IP: 10.56.56.5:8000
- 개발 모드: __DEV__ 사용 중
