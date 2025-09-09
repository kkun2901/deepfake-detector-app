from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import openpyxl
import os

def generate_pdf_report(data: dict, output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # 제목
    elements.append(Paragraph("Deepfake Detection Report", styles['Title']))
    elements.append(Paragraph(f"Video: {data['video']}", styles['Normal']))
    elements.append(Paragraph(f"Final Label: {data['final_label']}", styles['Normal']))
    elements.append(Paragraph(f"Frames Analyzed: {data['frames_analyzed']}", styles['Normal']))
    elements.append(Paragraph(f"Average Fake Confidence: {data['average_fake_confidence']}", styles['Normal']))
    elements.append(Paragraph(f"Average Real Confidence: {data['average_real_confidence']}", styles['Normal']))

    # 테이블 데이터
    table_data = [["Frame#", "Model1 Label", "Model1 Conf", "Model2 Label", "Model2 Conf", "Ensemble", "Conf"]]
    for idx, frame in enumerate(data["frame_results"]):
        table_data.append([
            idx + 1,
            frame["model1"]["label"], frame["model1"]["confidence"],
            frame["model2"]["label"], frame["model2"]["confidence"],
            frame["ensemble_result"], frame["confidence"]
        ])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)

    doc.build(elements)
    return output_path

def generate_excel_report(data: dict, output_path: str):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Deepfake Report"

    # 헤더
    ws.append(["Frame#", "Model1 Label", "Model1 Conf", "Model2 Label", "Model2 Conf", "Ensemble", "Conf"])

    # 데이터
    for idx, frame in enumerate(data["frame_results"]):
        ws.append([
            idx + 1,
            frame["model1"]["label"], frame["model1"]["confidence"],
            frame["model2"]["label"], frame["model2"]["confidence"],
            frame["ensemble_result"], frame["confidence"]
        ])

    wb.save(output_path)
    return output_path
