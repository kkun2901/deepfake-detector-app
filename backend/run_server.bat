@echo off
echo Starting Deepfake Detection API Server...
echo.

REM Python 가상환경 활성화
if not exist "venv\" (
    echo 가상환경이 없습니다. 생성 중...
    python -m venv venv
    echo.
)

call venv\Scripts\activate.bat

REM 패키지 설치 확인
echo 패키지 설치 확인 중...
pip install -r ..\requirements.txt

echo.
echo 백엔드 서버 시작...
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause

