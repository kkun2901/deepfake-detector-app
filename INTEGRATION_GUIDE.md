# 백엔드-프론트엔드 통합 가이드

## ⚠️ 필수 주의사항

### 1. 환경 설정
```
✅ 백엔드 (Python)
- Python 3.8 이상
- pip 설치

✅ 프론트엔드 (React Native 앱)
- Node.js 설치
- npm 또는 yarn
- React Native/Expo 개발 환경

✅ Python 패키지 설치
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Firebase 키 파일 (필수!)
```
⚠️ 중요: firebase-key.json 파일을 프로젝트 루트에 복사해야 함
이 파일이 없으면 백엔드가 실행되지 않습니다!
```

### 3. 백엔드 API 엔드포인트 확인

#### 📌 사용 가능한 API 엔드포인트:
```
기본 URL: http://localhost:8000

1. 영상 분석 (동기 처리)
   POST /analyze-video/
   - user_id: string (Form)
   - video: file (Form)
   
2. 영상 분석 (비동기 처리) ⭐ 추천
   POST /analysis-server/start-analysis
   - user_id: string (Form)
   - video: file (Form)
   
3. 분석 결과 조회
   GET /analysis-server/get-result/{analysis_id}
   
4. PDF 보고서 다운로드
   GET /download-report/pdf/{video_id}
   
5. Excel 보고서 다운로드
   GET /download-report/excel/{video_id}
```

### 4. API URL 설정 (매우 중요!)

#### ⚠️ React Native 앱은 localhost를 사용할 수 없음!

#### 백엔드:
- 기본 포트: `8000`
- 변경하려면: `run_server.bat` 수정
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 프론트엔드 (React Native):
```typescript
// ❌ 작동 안 함: http://localhost:8000
// ✅ 실제 IP 주소 사용해야 함

// Windows에서 IP 확인
ipconfig  # IPv4 주소 찾기 (예: 192.168.0.100)

// src/api/index.ts 또는 설정 파일
const API_BASE_URL = 'http://192.168.0.100:8000';  // 실제 IP로 변경
```

#### 📱 같은 WiFi에 연결되어야 함
- 백엔드 실행 컴퓨터와 모바일 기기가 같은 WiFi에 연결
- 또는 ngrok 사용 (외부 접근용)

### 5. CORS 설정

✅ 백엔드는 모든 origin을 허용하도록 설정됨:
```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6. 필수 디렉토리 구조
```
프로젝트/
├── app/                  # 백엔드 (backend 폴더)
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   └── utils/
├── venv/                 # Python 가상환경
├── firebase-key.json    # ⚠️ 필수 파일
├── requirements.txt      # Python 패키지 목록
├── run_server.bat      # 서버 실행 스크립트
└── [프론트엔드 파일들]  # .gitignore로 제외됨
```

### 7. 서버 실행 순서

#### 백엔드 시작:
```bash
# Windows
run_server.bat

# 또는 직접 실행
venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 백엔드 실행 확인:
```bash
# 브라우저에서 확인 (컴퓨터에서)
http://localhost:8000/

# 터미널에서 확인
curl http://localhost:8000/
# 응답: {"message":"Deepfake Detection API Running"}

# 같은 네트워크의 다른 기기에서 확인
http://[컴퓨터IP]:8000/  # 예: http://192.168.0.100:8000/
```

#### React Native 앱 실행:
```bash
# Expo 사용 시
cd frontend  # 또는 프론트엔드 폴더
npm install
npx expo start

# React Native CLI 사용 시
cd frontend
npm install
npx react-native run-android  # 또는 run-ios
```

### 8. 통합 테스트 체크리스트

```bash
✅ 1. 백엔드 서버 실행 확인
curl http://localhost:8000/
# 또는
curl http://[컴퓨터IP]:8000/

✅ 2. React Native 앱에서 API 호출 테스트
# 앱 실행 후:
- 영상 업로드 테스트
- 분석 결과 조회 테스트
- 보고서 다운로드 테스트

✅ 3. 네트워크 연결 확인
- 컴퓨터와 모바일이 같은 WiFi에 연결되었는지 확인
- 방화벽이 8000 포트를 막지 않는지 확인

✅ 4. CORS 에러 확인 (있는 경우)
- React Native는 일반적으로 CORS 문제 없음
- 만약 문제가 있으면 백엔드 CORS 설정 확인
```

### 8-1. React Native 앱 설정 예시

```typescript
// src/api/index.ts
const API_BASE_URL = __DEV__ 
  ? 'http://192.168.0.100:8000'  // 개발용 - 실제 IP로 변경
  : 'https://your-production-url.com';  // 프로덕션용

export const uploadVideo = async (video: FormData) => {
  const response = await fetch(`${API_BASE_URL}/analyze-video/`, {
    method: 'POST',
    body: video,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.json();
};
```

### 9. 주요 파일 위치

```
백엔드:
- 메인 앱: app/main.py
- API 엔드포인트: app/api/endpoints/
- 설정: app/core/config.py
- Firebase: app/core/firebase.py

프론트엔드 (React Native):
- API 호출 코드: frontend/src/api/
- 설정 파일: package.json, app.json, tsconfig.json
- 앱 진입점: App.tsx
```

### 10. 문제 해결

#### 문제: 백엔드가 시작되지 않음
```bash
# Firebase 키 확인
ls firebase-key.json

# 가상환경 활성화 확인
which python  # venv 폴더 내어야 함
```

#### 문제: 모바일 앱에서 서버에 연결할 수 없음
```bash
# ✅ 1. IP 주소 확인
ipconfig  # Windows

# ✅ 2. 방화벽 확인
# Windows 방화벽에서 8000 포트 허용

# ✅ 3. 백엔드가 0.0.0.0으로 바인딩되어 있는지 확인
# uvicorn app.main:app --host 0.0.0.0 --port 8000

# ✅ 4. 같은 WiFi에 연결되어 있는지 확인
# 컴퓨터와 모바일 모두 같은 네트워크에 있어야 함
```

#### 문제: CORS 에러
```bash
# React Native는 일반적으로 CORS 문제 없음
# 웹에서 테스트 중이라면:
# 백엔드 app/main.py의 CORS 설정 확인
# allow_origins=["*"] 되어있는지 확인
```

#### 문제: API 500 에러
```bash
# 백엔드 터미널에서 에러 로그 확인
# 필수 파일 누락 확인 (firebase-key.json)
# 모델 파일 존재 확인
```

### 11. 프로덕션 배포 시 주의사항

```bash
⚠️ 보안
- CORS 설정 변경: allow_origins=["*"] → 특정 도메인만
- firebase-key.json 절대 GitHub에 업로드하지 말 것
- 민감한 정보는 환경 변수로 관리

⚠️ 성능
- 멀티프로세싱 설정 조정 (워커 수)
- 메모리 사용량 모니터링
- temp/ 폴더 정기적으로 삭제
```

### 12. 개발 워크플로우

```bash
# 1. 백엔드 변경 후 GitHub에 푸시
cd backend
git add app/ requirements.txt .gitignore
git commit -m "Backend updates"
git push origin main

# 2. 프론트엔드에서 백엔드 pull
cd /path/to/frontend/computer
git pull origin main

# 3. 백엔드 재시작
run_server.bat
```

### 13. Git 브랜치 전략 (선택)

```bash
# Git이 이미 설정되어 있으므로 바로 사용 가능
# 프론트엔드는 .gitignore로 제외되어 백엔드만 push됨
```

---

## 🎯 빠른 시작 (5분 안에 시작)

### React Native 앱 + 백엔드 연결:

```bash
# 1. 컴퓨터 IP 확인
ipconfig  # IPv4 주소 기록 (예: 192.168.0.100)

# 2. 백엔드 서버 실행 (컴퓨터)
cd backend
run_server.bat

# 3. 프론트엔드에서 API URL 수정
# frontend/src/api/index.ts 파일 열기
# API_BASE_URL을 실제 IP로 변경:
# const API_BASE_URL = 'http://192.168.0.100:8000';

# 4. React Native 앱 실행
cd frontend
npx expo start
# 또는
npx react-native run-android

# 5. 앱에서 API 테스트
# 영상 업로드 → 분석 시작 → 결과 조회
```

### 주의사항:
- ⚠️ 컴퓨터와 모바일이 **같은 WiFi**에 연결되어 있어야 함
- ⚠️ React Native는 **localhost를 못 찾음** → 반드시 실제 IP 주소 사용
- ⚠️ 방화벽에서 **8000 포트 허용** 필요

---

## 📞 참고

- 백엔드 GitHub: https://github.com/kkun2901/deepfake-detector-app
- API 문서: http://localhost:8000/docs (FastAPI 자동 생성)
- Python 버전: 3.8+
- FastAPI 버전: 0.104.1
