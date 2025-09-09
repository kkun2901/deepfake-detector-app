from fastapi import APIRouter
from fastapi.responses import FileResponse
import os, uuid
from app.utils.helpers import get_analysis_result
from app.services.report_generator import generate_pdf_report, generate_excel_report

router = APIRouter()

@router.get("/pdf/{video_id}", summary="Download PDF Report")
async def download_pdf(video_id: str):
    data = get_analysis_result(video_id)
    if not data:
        return {"error": "결과를 찾을 수 없습니다."}
    output_path = os.path.join("temp", f"{uuid.uuid4()}.pdf")
    generate_pdf_report(data, output_path)
    return FileResponse(output_path, media_type="application/pdf", filename=f"{video_id}.pdf")

@router.get("/excel/{video_id}", summary="Download Excel Report")
async def download_excel(video_id: str):
    data = get_analysis_result(video_id)
    if not data:
        return {"error": "결과를 찾을 수 없습니다."}
    output_path = os.path.join("temp", f"{uuid.uuid4()}.xlsx")
    generate_excel_report(data, output_path)
    return FileResponse(output_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=f"{video_id}.xlsx")
