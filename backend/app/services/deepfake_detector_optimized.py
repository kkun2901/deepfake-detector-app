from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch
import threading
import time
import gc

# GPU 사용 여부 확인
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 전역 모델 변수들
processor1 = None
model1 = None
processor2 = None
model2 = None
models_loaded = False
loading_lock = threading.Lock()

def load_models():
    """모델들을 필요할 때만 로딩 (메모리 효율적) - 스레드 안전"""
    global processor1, model1, processor2, model2, models_loaded
    
    # 이미 로딩 중이거나 로딩 완료된 경우 대기
    if models_loaded:
        return True
    
    with loading_lock:
        # 이중 체크 (다른 스레드에서 이미 로딩했을 수 있음)
        if models_loaded:
            return True
            
        print("딥페이크 탐지 모델들을 로딩 중...")
        start_time = time.time()
        
        try:
            # 메모리 효율적인 로딩
            processor1 = AutoImageProcessor.from_pretrained("prithivMLmods/Deep-Fake-Detector-v2-Model")
            model1 = AutoModelForImageClassification.from_pretrained(
                "prithivMLmods/Deep-Fake-Detector-v2-Model",
                torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
                low_cpu_mem_usage=True
            ).to(device)
            
            # CPU에서는 하나의 모델만 사용 (메모리 절약)
            if device.type == "cpu":
                print("CPU 환경: 하나의 모델만 사용하여 메모리 절약")
                processor2 = processor1
                model2 = model1
            else:
                processor2 = AutoImageProcessor.from_pretrained("google/vit-base-patch16-224-in21k")
                model2 = AutoModelForImageClassification.from_pretrained(
                    "google/vit-base-patch16-224-in21k",
                    torch_dtype=torch.float16,
                    low_cpu_mem_usage=True
                ).to(device)
            
            models_loaded = True
            loading_time = time.time() - start_time
            print(f"모델 로딩 완료! (소요시간: {loading_time:.2f}초)")
            return True
            
        except Exception as e:
            print(f"모델 로딩 실패: {e}")
            # 기본값 설정
            processor1 = processor2 = None
            model1 = model2 = None
            models_loaded = False
            return False

def ensure_models_loaded():
    """모델이 로딩되었는지 확인하고 필요시 로딩"""
    if not models_loaded:
        return load_models()
    return True

def map_label(label: str):
    """라벨 매핑 함수"""
    lower = label.lower()
    if "fake" in lower: return "FAKE"
    elif "real" in lower: return "REAL"
    elif label in ["0", "LABEL_0"]: return "REAL"
    elif label in ["1", "LABEL_1"]: return "FAKE"
    return "REAL"

def predict_image(image_path: str):
    """이미지 예측 - 최적화된 버전"""
    # 모델 로딩 확인
    if not ensure_models_loaded():
        return {"error": "모델 로딩 실패"}
    
    try:
        image = Image.open(image_path).convert("RGB")

        # 모델1 추론
        inputs1 = processor1(images=image, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs1 = model1(**inputs1)
            probs1 = torch.nn.functional.softmax(outputs1.logits, dim=-1)
            conf1, pred1 = torch.max(probs1, dim=1)
        label1 = map_label(model1.config.id2label[pred1.item()])

        # 모델2 추론
        inputs2 = processor2(images=image, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs2 = model2(**inputs2)
            probs2 = torch.nn.functional.softmax(outputs2.logits, dim=-1)
            conf2, pred2 = torch.max(probs2, dim=1)
        label2 = map_label(model2.config.id2label[pred2.item()])

        # 앙상블 결과
        final_label = "FAKE" if [label1, label2].count("FAKE") >= 1 else "REAL"
        avg_confidence = round((conf1.item() + conf2.item()) / 2, 4)

        # 메모리 정리
        del inputs1, inputs2, outputs1, outputs2, probs1, probs2
        if device.type == "cuda":
            torch.cuda.empty_cache()

        return {
            "model1": {"label": label1, "confidence": round(conf1.item(), 4)},
            "model2": {"label": label2, "confidence": round(conf2.item(), 4)},
            "ensemble_result": final_label,
            "confidence": avg_confidence
        }
        
    except Exception as e:
        print(f"이미지 예측 오류: {e}")
        return {"error": str(e)}

def predict_batch(images: list):
    """배치 예측 - 여러 이미지를 한 번에 처리"""
    if not ensure_models_loaded():
        return [{"error": "모델 로딩 실패"}] * len(images)
    
    results = []
    try:
        for image_path in images:
            result = predict_image(image_path)
            results.append(result)
    except Exception as e:
        print(f"배치 예측 오류: {e}")
        results = [{"error": str(e)}] * len(images)
    
    return results

def cleanup_memory():
    """메모리 정리"""
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()
        print("GPU 메모리 정리 완료")
    else:
        print("CPU 메모리 정리 완료")




