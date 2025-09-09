from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch

# GPU 사용 여부 확인
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 모델1
processor1 = AutoImageProcessor.from_pretrained("prithivMLmods/Deep-Fake-Detector-v2-Model")
model1 = AutoModelForImageClassification.from_pretrained("prithivMLmods/Deep-Fake-Detector-v2-Model").to(device)

# 모델2
processor2 = AutoImageProcessor.from_pretrained("google/vit-base-patch16-224-in21k")
model2 = AutoModelForImageClassification.from_pretrained("google/vit-base-patch16-224-in21k").to(device)

def map_label(label: str):
    lower = label.lower()
    if "fake" in lower: return "FAKE"
    elif "real" in lower: return "REAL"
    elif label in ["0", "LABEL_0"]: return "REAL"
    elif label in ["1", "LABEL_1"]: return "FAKE"
    return "REAL"

def predict_image(image_path: str):
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
