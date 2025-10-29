from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch

# GPU 사용 여부 확인
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 모델 로딩을 지연시키기 위해 None으로 초기화
processor1 = None
model1 = None
processor2 = None
model2 = None

def load_models():
    """모델들을 필요할 때만 로딩 (메모리 효율적)"""
    global processor1, model1, processor2, model2
    
    if processor1 is None:
        print("딥페이크 탐지 모델들을 로딩 중...")
        try:
            # 메모리 효율적인 로딩
            processor1 = AutoImageProcessor.from_pretrained("prithivMLmods/Deep-Fake-Detector-v2-Model")
            model1 = AutoModelForImageClassification.from_pretrained(
                "prithivMLmods/Deep-Fake-Detector-v2-Model",
                torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
                low_cpu_mem_usage=True  # CPU 메모리 사용량 최적화
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
            
            print("모델 로딩 완료!")
        except Exception as e:
            print(f"모델 로딩 실패: {e}")
            # 기본값 설정
            processor1 = processor2 = None
            model1 = model2 = None

def map_label(label: str):
    lower = label.lower()
    if "fake" in lower: return "FAKE"
    elif "real" in lower: return "REAL"
    elif label in ["0", "LABEL_0"]: return "REAL"
    elif label in ["1", "LABEL_1"]: return "FAKE"
    return "REAL"

def predict_image(image_path: str):
    # 모델이 로드되지 않았다면 먼저 로드
    load_models()
    
    image = Image.open(image_path).convert("RGB")

    # 모델1
    inputs1 = processor1(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs1 = model1(**inputs1)
        probs1 = torch.nn.functional.softmax(outputs1.logits, dim=-1)
        conf1, pred1 = torch.max(probs1, dim=1)
    label1 = map_label(model1.config.id2label[pred1.item()])

    # 모델2
    inputs2 = processor2(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs2 = model2(**inputs2)
        probs2 = torch.nn.functional.softmax(outputs2.logits, dim=-1)
        conf2, pred2 = torch.max(probs2, dim=1)
    label2 = map_label(model2.config.id2label[pred2.item()])

    final_label = "FAKE" if [label1, label2].count("FAKE") >= 1 else "REAL"
    avg_confidence = round((conf1.item() + conf2.item()) / 2, 4)

    return {
        "model1": {"label": label1, "confidence": round(conf1.item(), 4)},
        "model2": {"label": label2, "confidence": round(conf2.item(), 4)},
        "ensemble_result": final_label,
        "confidence": avg_confidence
    }
