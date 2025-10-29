from fastapi import APIRouter
from fastapi.responses import FileResponse
import os, uuid
from app.utils.helpers import get_analysis_result
from app.services.report_generator import generate_pdf_report, generate_excel_report

router = APIRouter()

# temp 디렉토리 생성 함수
def ensure_temp_dir():
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    return temp_dir

@router.get("/pdf/{video_id}", summary="Download PDF Report")
async def download_pdf(video_id: str):
    try:
        print(f"PDF 다운로드 요청: {video_id}")
        
        data = get_analysis_result(video_id)
        if not data:
            print(f"분석 결과를 찾을 수 없음: {video_id}")
            return {"error": "결과를 찾을 수 없습니다."}
        
        print(f"분석 결과 발견: {video_id}")
        
        # temp 디렉토리 확인 및 생성
        temp_dir = ensure_temp_dir()
        
        # 고유한 파일명 생성
        unique_filename = f"{uuid.uuid4()}.pdf"
        output_path = os.path.join(temp_dir, unique_filename)
        
        print(f"PDF 생성 시작: {output_path}")
        
        # PDF 보고서 생성
        generate_pdf_report(data, output_path)
        
        # 파일이 생성되었는지 확인
        if not os.path.exists(output_path):
            print(f"PDF 파일 생성 실패: {output_path}")
            return {"error": "보고서 생성에 실패했습니다."}
        
        file_size = os.path.getsize(output_path)
        print(f"PDF 파일 생성 완료: {output_path}, 크기: {file_size} bytes")
        
        return FileResponse(
            output_path, 
            media_type="application/pdf", 
            filename=f"deepfake_report_{video_id}.pdf",
            headers={"Content-Disposition": f"attachment; filename=deepfake_report_{video_id}.pdf"}
        )
    except Exception as e:
        print(f"PDF 다운로드 오류: {e}")
        return {"error": f"PDF 다운로드 중 오류가 발생했습니다: {str(e)}"}

@router.get("/excel/{video_id}", summary="Download Excel Report")
async def download_excel(video_id: str):
    try:
        print(f"Excel 다운로드 요청: {video_id}")
        
        data = get_analysis_result(video_id)
        if not data:
            print(f"분석 결과를 찾을 수 없음: {video_id}")
            return {"error": "결과를 찾을 수 없습니다."}
        
        print(f"분석 결과 발견: {video_id}")
        
        # temp 디렉토리 확인 및 생성
        temp_dir = ensure_temp_dir()
        
        # 고유한 파일명 생성
        unique_filename = f"{uuid.uuid4()}.xlsx"
        output_path = os.path.join(temp_dir, unique_filename)
        
        print(f"Excel 생성 시작: {output_path}")
        
        # Excel 보고서 생성
        generate_excel_report(data, output_path)
        
        # 파일이 생성되었는지 확인
        if not os.path.exists(output_path):
            print(f"Excel 파일 생성 실패: {output_path}")
            return {"error": "보고서 생성에 실패했습니다."}
        
        file_size = os.path.getsize(output_path)
        print(f"Excel 파일 생성 완료: {output_path}, 크기: {file_size} bytes")
        
        return FileResponse(
            output_path, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            filename=f"deepfake_report_{video_id}.xlsx",
            headers={"Content-Disposition": f"attachment; filename=deepfake_report_{video_id}.xlsx"}
        )
    except Exception as e:
        print(f"Excel 다운로드 오류: {e}")
        return {"error": f"Excel 다운로드 중 오류가 발생했습니다: {str(e)}"}
