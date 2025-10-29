# 딥페이크 탐지 앱

딥페이크 비디오와 오디오를 탐지하는 통합 애플리케이션입니다.

## 프로젝트 구조

```
deepfake_frontend_expo_template/
├── backend/              # Python FastAPI 백엔드
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── utils/
│   └── main.py
├── frontend/             # React Native Expo 프론트엔드
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── navigation/
│   │   ├── screens/
│   │   └── types/
│   └── package.json
└── requirements.txt      # Python 의존성
```

## 시작하기

### 백엔드 서버 실행

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

백엔드는 `http://localhost:8000`에서 실행됩니다.

### 프론트엔드 실행

```bash
cd frontend
npm install
npm start
```

## API 엔드포인트

- `POST /analyze-video` - 비디오 분석
- `GET /get-result/{video_id}` - 분석 결과 조회
- `POST /submit-report` - 리포트 제출
- `GET /download-report/{report_id}` - 리포트 다운로드

## 기술 스택

### 백엔드
- FastAPI
- PyTorch, Transformers
- Whisper (음성 인식)
- OpenCV (비디오 처리)

### 프론트엔드
- React Native + Expo
- TypeScript
- Firebase Storage
- React Navigation

