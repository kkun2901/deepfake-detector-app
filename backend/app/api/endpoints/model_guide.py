from fastapi import APIRouter
from app.utils.helpers import get_analysis_result
from typing import Dict, Any
import json

router = APIRouter()

@router.get("/model-guide/{video_id}", summary="Get Model Development Guide")
async def get_model_development_guide(video_id: str):
    """
    딥페이크 탐지 모델 제작을 위한 가이드 정보 제공
    
    포함 내용:
    - 데이터셋 정보 (2)
    - 라벨링 규격 (3) 
    - 기준 모델 (5)
    - 학습/평가 세팅 (6)
    """
    try:
        # 분석 결과 가져오기
        analysis_result = get_analysis_result(video_id)
        if not analysis_result:
            return {"error": "분석 결과를 찾을 수 없습니다."}
        
        # 모델 개발 가이드 생성
        guide = create_model_development_guide(analysis_result)
        
        return guide
        
    except Exception as e:
        return {"error": str(e)}

def create_model_development_guide(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """모델 개발 가이드 생성"""
    
    # 2. 데이터셋 정보
    dataset_info = {
        "video_metadata": {
            "video_id": analysis_result.get("videoId"),
            "video_name": analysis_result.get("video_name"),
            "duration": analysis_result.get("video_info", {}).get("duration"),
            "fps": analysis_result.get("video_info", {}).get("fps"),
            "total_frames": analysis_result.get("video_info", {}).get("frame_count"),
            "extracted_frames": analysis_result.get("video_info", {}).get("frame_rate_used"),
            "analysis_timestamp": analysis_result.get("analysis_timestamp")
        },
        "frame_extraction_strategy": {
            "method": "동적 간격 추출",
            "frame_rate": analysis_result.get("video_info", {}).get("frame_rate_used"),
            "total_extracted": len(analysis_result.get("raw_frame_results", [])),
            "extraction_logic": "영상 길이에 따라 프레임 추출 간격 자동 조정"
        },
        "data_quality": {
            "resolution_estimate": "1920x1080 (추정)",
            "compression": "MP4 형식",
            "lighting": "자연광 (추정)",
            "camera_angle": "정면 (추정)",
            "background": "단색 배경 (추정)"
        }
    }
    
    # 3. 라벨링 규격
    labeling_spec = {
        "data_structure": {
            "video_id": "고유 식별자 (UUID)",
            "frame_idx": "time 필드로 관리 (초 단위)",
            "label": "REAL 또는 FAKE",
            "confidence": "0.0-1.0 범위의 신뢰도 점수",
            "bbox": "전체 프레임 사용 (얼굴 탐지 생략)"
        },
        "labeling_criteria": {
            "REAL": "원본 영상, 자연스러운 얼굴 움직임",
            "FAKE": "딥페이크, 인공적으로 생성된 얼굴",
            "confidence_threshold": "0.5 이상을 신뢰할 만한 결과로 판단"
        },
        "current_labels": {
            "total_frames": len(analysis_result.get("raw_frame_results", [])),
            "real_frames": len([r for r in analysis_result.get("raw_frame_results", []) if r.get("ensemble_result") == "REAL"]),
            "fake_frames": len([r for r in analysis_result.get("raw_frame_results", []) if r.get("ensemble_result") == "FAKE"]),
            "overall_result": analysis_result.get("summary", {}).get("overall_result")
        }
    }
    
    # 5. 기준 모델(Baseline)
    baseline_models = {
        "current_models": {
            "model1": {
                "name": "prithivMLmods/Deep-Fake-Detector-v2-Model",
                "type": "Vision Transformer (ViT)",
                "architecture": "ViT-base-patch16-224",
                "purpose": "딥페이크 탐지 전용 모델"
            },
            "model2": {
                "name": "google/vit-base-patch16-224-in21k",
                "type": "Vision Transformer (ViT)",
                "architecture": "ViT-base-patch16-224",
                "purpose": "일반 이미지 분류 모델 (ImageNet 사전훈련)"
            }
        },
        "ensemble_strategy": {
            "method": "다수결 + 신뢰도 기반",
            "decision_logic": "두 모델의 결과가 다를 경우 신뢰도가 높은 모델의 결과 선택",
            "confidence_calculation": "두 모델의 평균 신뢰도",
            "fallback": "CPU 환경에서는 하나의 모델만 사용하여 메모리 절약"
        },
        "implementation_code": {
            "model_loading": """
# 모델 로딩 코드
from transformers import AutoImageProcessor, AutoModelForImageClassification
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

processor1 = AutoImageProcessor.from_pretrained("prithivMLmods/Deep-Fake-Detector-v2-Model")
model1 = AutoModelForImageClassification.from_pretrained(
    "prithivMLmods/Deep-Fake-Detector-v2-Model",
    torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
    low_cpu_mem_usage=True
).to(device)
            """,
            "inference_code": """
# 추론 코드
def predict_image(image_path: str):
    image = Image.open(image_path).convert("RGB")
    
    # 모델1 추론
    inputs1 = processor1(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs1 = model1(**inputs1)
        probs1 = torch.nn.functional.softmax(outputs1.logits, dim=-1)
        conf1, pred1 = torch.max(probs1, dim=1)
    
    # 앙상블 결과
    final_label = "FAKE" if [label1, label2].count("FAKE") >= 1 else "REAL"
    avg_confidence = (conf1.item() + conf2.item()) / 2
    
    return {
        "ensemble_result": final_label,
        "confidence": avg_confidence
    }
            """
        }
    }
    
    # 6. 학습/평가 세팅
    training_evaluation = {
        "current_metrics": {
            "confidence_scoring": "각 모델별 신뢰도 점수 (0.0-1.0)",
            "ensemble_result": "다수결 + 평균 신뢰도",
            "segment_analysis": "스마트 타임라인 기반 구간별 분석",
            "overall_judgment": "전체 영상에 대한 REAL/FAKE 판정"
        },
        "performance_analysis": {
            "model_comparison": {
                "model1_avg_confidence": calculate_model_avg_confidence(analysis_result, "model1"),
                "model2_avg_confidence": calculate_model_avg_confidence(analysis_result, "model2"),
                "agreement_rate": calculate_model_agreement(analysis_result)
            },
            "segment_performance": {
                "total_segments": analysis_result.get("summary", {}).get("total_segments"),
                "real_segments": analysis_result.get("summary", {}).get("real_segments"),
                "fake_segments": analysis_result.get("summary", {}).get("fake_segments"),
                "segment_confidence_range": calculate_confidence_range(analysis_result)
            }
        },
        "evaluation_recommendations": {
            "recommended_metrics": [
                "ROC-AUC (Receiver Operating Characteristic)",
                "EER (Equal Error Rate)",
                "F1-Score",
                "AP (Average Precision)",
                "Frame-level Accuracy",
                "Segment-level Accuracy"
            ],
            "calibration_metrics": [
                "Brier Score",
                "Negative Log Likelihood (NLL)"
            ],
            "cross_dataset_generalization": "다른 데이터셋에서의 일반화 성능 테스트 권장"
        },
        "training_recommendations": {
            "data_split": "train/val/test (Subject-disjoint 권장)",
            "early_stopping": "검증 손실 기반 조기 종료",
            "learning_rate": "스케줄러 사용 (Cosine Annealing 등)",
            "reproducibility": "시드 고정 및 재현성 로그 필수"
        }
    }
    
    return {
        "model_development_guide": {
            "dataset_information": dataset_info,
            "labeling_specification": labeling_spec,
            "baseline_models": baseline_models,
            "training_evaluation_setting": training_evaluation
        },
        "generated_at": analysis_result.get("analysis_timestamp"),
        "guide_version": "1.0"
    }

def calculate_model_avg_confidence(analysis_result: Dict[str, Any], model_name: str) -> float:
    """모델별 평균 신뢰도 계산"""
    frame_results = analysis_result.get("raw_frame_results", [])
    if not frame_results:
        return 0.0
    
    confidences = []
    for frame in frame_results:
        model_data = frame.get(model_name, {})
        confidence = model_data.get("confidence", 0.0)
        confidences.append(confidence)
    
    return round(sum(confidences) / len(confidences), 4) if confidences else 0.0

def calculate_model_agreement(analysis_result: Dict[str, Any]) -> float:
    """모델 간 일치율 계산"""
    frame_results = analysis_result.get("raw_frame_results", [])
    if not frame_results:
        return 0.0
    
    agreements = 0
    for frame in frame_results:
        model1_label = frame.get("model1", {}).get("label", "")
        model2_label = frame.get("model2", {}).get("label", "")
        if model1_label == model2_label:
            agreements += 1
    
    return round(agreements / len(frame_results), 4) if frame_results else 0.0

def calculate_confidence_range(analysis_result: Dict[str, Any]) -> Dict[str, float]:
    """신뢰도 범위 계산"""
    frame_results = analysis_result.get("raw_frame_results", [])
    if not frame_results:
        return {"min": 0.0, "max": 0.0, "avg": 0.0}
    
    confidences = [frame.get("confidence", 0.0) for frame in frame_results]
    
    return {
        "min": round(min(confidences), 4),
        "max": round(max(confidences), 4),
        "avg": round(sum(confidences) / len(confidences), 4)
    }


