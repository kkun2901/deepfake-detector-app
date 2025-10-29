import librosa
import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer
import os
import tempfile
from typing import Dict, List, Tuple

# 음성 인식 라이브러리들을 안전하게 처리
WHISPER_AVAILABLE = False
SPEECH_RECOGNITION_AVAILABLE = False

# Whisper 시도 (더 안전한 방법)
try:
    import platform
    if platform.system() == "Windows":
        # Windows에서는 Whisper를 완전히 건너뛰기
        print("Windows 환경: Whisper 대신 SpeechRecognition을 사용합니다.")
        WHISPER_AVAILABLE = False
    else:
        # Linux/Mac에서는 Whisper 사용
        import whisper
        WHISPER_AVAILABLE = True
        print("Whisper 라이브러리가 사용 가능합니다.")
except Exception as e:
    print(f"Whisper 라이브러리 로딩 실패: {e}")
    WHISPER_AVAILABLE = False

# SpeechRecognition 라이브러리 시도 (모든 OS에서 사용 가능)
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
    print("SpeechRecognition 라이브러리가 사용 가능합니다.")
except Exception as e:
    print(f"SpeechRecognition 라이브러리 로딩 실패: {e}")
    SPEECH_RECOGNITION_AVAILABLE = False

# Sentence-BERT 임포트를 더 안전하게 처리
SENTENCE_BERT_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_BERT_AVAILABLE = True
    print("Sentence-BERT 라이브러리가 사용 가능합니다.")
except Exception as e:
    print(f"Sentence-BERT 라이브러리 로딩 실패: {e}")
    SENTENCE_BERT_AVAILABLE = False

class AudioProcessor:
    def __init__(self):
        """음성 분석을 위한 모델들 초기화"""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 모델들을 None으로 초기화
        self.whisper_model = None
        self.wav2vec2_model = None
        self.wav2vec2_tokenizer = None
        self.sentence_bert = None
        
        print("음성 분석 프로세서가 초기화되었습니다.")
    
    def load_models(self):
        """메모리 효율적인 모델 로딩"""
        try:
            if self.whisper_model is None and WHISPER_AVAILABLE:
                print("Whisper 모델 로딩 중...")
                self.whisper_model = whisper.load_model("base")
                print("Whisper 모델 로딩 완료!")
            
            if self.wav2vec2_model is None:
                print("Wav2Vec2 모델 로딩 중...")
                self.wav2vec2_model = AutoModel.from_pretrained(
                    "facebook/wav2vec2-base",
                    torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32
                ).to(self.device)
                self.wav2vec2_tokenizer = AutoTokenizer.from_pretrained("facebook/wav2vec2-base")
                print("Wav2Vec2 모델 로딩 완료!")
            
            if self.sentence_bert is None and SENTENCE_BERT_AVAILABLE:
                print("Sentence-BERT 모델 로딩 중...")
                self.sentence_bert = SentenceTransformer("nickprock/csr-multi-sentence-BERTino-cv")
                print("Sentence-BERT 모델 로딩 완료!")
        except Exception as e:
            print(f"모델 로딩 중 오류 발생: {e}")
            # 메모리 부족 시 일부 모델만 로딩
            print("메모리 절약을 위해 일부 기능을 비활성화합니다.")

    def extract_audio_from_video(self, video_path: str) -> str:
        """비디오에서 오디오 추출"""
        try:
            # librosa로 비디오에서 오디오 추출
            audio_data, sample_rate = librosa.load(video_path, sr=16000)
            
            # 임시 오디오 파일로 저장 (soundfile 사용)
            temp_audio_path = os.path.join(tempfile.gettempdir(), f"temp_audio_{os.path.basename(video_path)}.wav")
            
            # soundfile을 사용하여 저장
            import soundfile as sf
            sf.write(temp_audio_path, audio_data, sample_rate)
            
            return temp_audio_path
        except Exception as e:
            print(f"오디오 추출 실패: {e}")
            # librosa.output.write_wav 대신 다른 방법 시도
            try:
                import soundfile as sf
                audio_data, sample_rate = librosa.load(video_path, sr=16000)
                temp_audio_path = os.path.join(tempfile.gettempdir(), f"temp_audio_{os.path.basename(video_path)}.wav")
                sf.write(temp_audio_path, audio_data, sample_rate)
                return temp_audio_path
            except Exception as e2:
                print(f"대체 오디오 추출도 실패: {e2}")
                return None

    def transcribe_audio(self, audio_path: str) -> str:
        """음성을 텍스트로 변환 (다중 백업 시스템)"""
        # 1. Whisper 사용 시도 (Linux/Mac에서만)
        if WHISPER_AVAILABLE and self.whisper_model is not None:
            try:
                result = self.whisper_model.transcribe(audio_path)
                return result["text"].strip()
            except Exception as e:
                print(f"Whisper 음성 인식 실패: {e}")
        
        # 2. SpeechRecognition 사용 시도
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                import speech_recognition as sr
                r = sr.Recognizer()
                
                # 오디오 파일을 WAV 형식으로 변환
                with sr.AudioFile(audio_path) as source:
                    audio = r.record(source)
                
                # Google 음성 인식 사용 (한국어)
                text = r.recognize_google(audio, language='ko-KR')
                return text
            except Exception as e:
                print(f"SpeechRecognition 음성 인식 실패: {e}")
        
        # 3. 기본 텍스트 반환 (음성 인식 실패 시)
        return "음성 인식이 완료되었습니다. (텍스트 추출 실패)"

    def extract_audio_features(self, audio_path: str) -> Dict:
        """librosa로 음성 특징 추출"""
        try:
            # 오디오 로드
            y, sr = librosa.load(audio_path, sr=16000)
            
            # MFCC 특징 추출
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            # 피치 추출
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_mean = np.mean(pitches[pitches > 0]) if np.any(pitches > 0) else 0
            
            # 스펙트럼 중심
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            spectral_centroid_mean = np.mean(spectral_centroids)
            
            # 제로 크로싱 비율
            zcr = librosa.feature.zero_crossing_rate(y)
            zcr_mean = np.mean(zcr)
            
            return {
                "mfcc_mean": np.mean(mfccs, axis=1).tolist(),
                "mfcc_std": np.std(mfccs, axis=1).tolist(),
                "pitch_mean": float(pitch_mean),
                "spectral_centroid_mean": float(spectral_centroid_mean),
                "zero_crossing_rate_mean": float(zcr_mean),
                "duration": len(y) / sr
            }
        except Exception as e:
            print(f"음성 특징 추출 실패: {e}")
            return {}

    def detect_deepvoice_wav2vec2(self, audio_path: str) -> Dict:
        """Wav2Vec2로 딥보이스 탐지"""
        if self.wav2vec2_model is None:
            return {"is_deepvoice": False, "confidence": 0.0, "feature_variance": 0.0, "error": "Wav2Vec2 모델이 로드되지 않았습니다."}
        
        try:
            # 오디오 로드 및 전처리
            y, sr = librosa.load(audio_path, sr=16000)
            
            # Wav2Vec2 입력 형태로 변환
            inputs = self.wav2vec2_tokenizer(y, return_tensors="pt", padding=True, truncation=True, max_length=16000)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 모델 추론
            with torch.no_grad():
                outputs = self.wav2vec2_model(**inputs)
                # 간단한 분류를 위한 특징 추출
                features = outputs.last_hidden_state.mean(dim=1)
                
                # 더미 분류기 (실제로는 별도 훈련된 분류기가 필요)
                # 여기서는 특징의 분산을 기반으로 간단한 판단
                feature_variance = torch.var(features, dim=1).item()
                
                # 임계값 기반 판단 (실제로는 훈련된 모델 필요)
                is_deepvoice = feature_variance > 0.1  # 임계값은 실험적으로 조정 필요
                confidence = min(abs(feature_variance - 0.1) * 10, 1.0)
                
                return {
                    "is_deepvoice": bool(is_deepvoice),
                    "confidence": float(confidence),
                    "feature_variance": float(feature_variance)
                }
        except Exception as e:
            print(f"Wav2Vec2 딥보이스 탐지 실패: {e}")
            return {"is_deepvoice": False, "confidence": 0.0, "feature_variance": 0.0}

    def analyze_speech_text_semantic_mismatch(self, audio_path: str, transcribed_text: str) -> Dict:
        """음성과 텍스트 간 의미적 불일치 분석"""
        if not SENTENCE_BERT_AVAILABLE or self.sentence_bert is None:
            return {"semantic_mismatch": False, "confidence": 0.0, "similarity": 0.0, "error": "Sentence-BERT 모델이 사용할 수 없습니다."}
        
        try:
            if not transcribed_text:
                return {"semantic_mismatch": False, "confidence": 0.0, "similarity": 0.0}
            
            # 텍스트를 여러 구간으로 나누어 분석
            sentences = transcribed_text.split('.')
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) < 2:
                return {"semantic_mismatch": False, "confidence": 0.0, "similarity": 1.0}
            
            # 각 문장의 임베딩 생성
            embeddings = self.sentence_bert.encode(sentences)
            
            # 문장 간 유사도 계산
            similarities = []
            for i in range(len(embeddings) - 1):
                sim = np.dot(embeddings[i], embeddings[i + 1]) / (
                    np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i + 1])
                )
                similarities.append(sim)
            
            avg_similarity = np.mean(similarities) if similarities else 1.0
            
            # 유사도가 낮으면 의미적 불일치 가능성
            semantic_mismatch = avg_similarity < 0.7  # 임계값 조정 가능
            confidence = abs(avg_similarity - 0.7) * 2  # 신뢰도 계산
            
            return {
                "semantic_mismatch": bool(semantic_mismatch),
                "confidence": float(min(confidence, 1.0)),
                "similarity": float(avg_similarity),
                "sentence_count": len(sentences)
            }
        except Exception as e:
            print(f"의미적 불일치 분석 실패: {e}")
            return {"semantic_mismatch": False, "confidence": 0.0, "similarity": 0.0}

    def analyze_audio(self, video_path: str) -> Dict:
        """전체 음성 분석 수행"""
        try:
            print(f"음성 분석 시작: {video_path}")
            
            # 모델들을 먼저 로드
            self.load_models()
            
            # 1. 비디오에서 오디오 추출
            audio_path = self.extract_audio_from_video(video_path)
            if not audio_path:
                return {"error": "오디오 추출 실패"}
            
            # 2. 음성을 텍스트로 변환
            transcribed_text = self.transcribe_audio(audio_path)
            
            # 3. 음성 특징 추출
            audio_features = self.extract_audio_features(audio_path)
            
            # 4. Wav2Vec2 딥보이스 탐지
            deepvoice_result = self.detect_deepvoice_wav2vec2(audio_path)
            
            # 5. 음성-텍스트 의미적 불일치 분석
            semantic_result = self.analyze_speech_text_semantic_mismatch(audio_path, transcribed_text)
            
            # 6. 최종 결과 종합
            # 두 방식 모두에서 위조 탐지되면 최종적으로 위조로 판단
            is_fake_voice = deepvoice_result.get("is_deepvoice", False) or semantic_result.get("semantic_mismatch", False)
            
            # 신뢰도는 두 방식의 평균
            avg_confidence = (deepvoice_result.get("confidence", 0.0) + semantic_result.get("confidence", 0.0)) / 2
            
            result = {
                "transcribed_text": transcribed_text,
                "audio_features": audio_features,
                "deepvoice_detection": deepvoice_result,
                "semantic_analysis": semantic_result,
                "final_result": {
                    "is_fake_voice": is_fake_voice,
                    "confidence": avg_confidence,
                    "label": "FAKE" if is_fake_voice else "REAL"
                }
            }
            
            # 임시 파일 정리
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            print(f"음성 분석 완료: {result['final_result']['label']} (신뢰도: {avg_confidence:.3f})")
            return result
            
        except Exception as e:
            print(f"음성 분석 실패: {e}")
            return {"error": f"음성 분석 실패: {str(e)}"}

# 전역 인스턴스
audio_processor = AudioProcessor()

def analyze_audio_from_video(video_path: str) -> Dict:
    """비디오 파일에서 음성 분석 수행"""
    return audio_processor.analyze_audio(video_path)

