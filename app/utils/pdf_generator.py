from fpdf import FPDF
import os
from datetime import datetime


class MissingKoreanFontError(FileNotFoundError):
    """Raised when the required Korean font file is not available."""
    pass

# Define path for a Korean font file.
# Assumes NanumGothic.ttf will be placed in static/fonts/
FONT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'fonts'))
os.makedirs(FONT_DIR, exist_ok=True) # Ensure the directory exists
KOREAN_FONT_PATH = os.path.join(FONT_DIR, "NanumGothic.ttf")

def _add_korean_font(pdf_instance):
    """Helper function to add Korean font to the PDF instance."""
    if os.path.exists(KOREAN_FONT_PATH):
        pdf_instance.add_font("NanumGothic", "", KOREAN_FONT_PATH, uni=True)
        pdf_instance.set_font("NanumGothic", size=12)
        return True
    raise MissingKoreanFontError(
        (
            "Korean font 'NanumGothic.ttf' was not found in app/static/fonts/. "
            "Install the font (e.g. via 'sudo apt-get install fonts-nanum') or "
            "place the TTF file in that directory."
        )
    )

def generate_prescription_pdf(patient_name, patient_rrn, department, prescriptions, total_fee):
    pdf = FPDF()
    pdf.add_page()
    _add_korean_font(pdf)

    # Title
    pdf.set_font_size(20)
    pdf.cell(0, 15, txt="처방전 (Prescription)", ln=True, align="C")
    pdf.ln(5)

    # Header Information
    pdf.set_font_size(12)
    current_date = datetime.now().strftime("%Y-%m-%d")
    pdf.cell(0, 7, txt=f"발행일: {current_date}", ln=True, align="R")
    pdf.cell(0, 7, txt="기관명: 중앙대 보건소", ln=True)
    pdf.cell(0, 7, txt=f"환자 성명: {patient_name}", ln=True)
    pdf.cell(0, 7, txt=f"주민등록번호: {patient_rrn}", ln=True)
    pdf.cell(0, 7, txt=f"진료과: {department}", ln=True)
    pdf.ln(5)

    # Prescriptions Table Header
    pdf.set_font_size(14)
    pdf.cell(0, 10, txt="처방내역", ln=True)
    pdf.set_font_size(11) # Slightly smaller for table content
    pdf.cell(130, 10, txt="처방명 (항목)", border=1)
    pdf.cell(50, 10, txt="금액 (원)", border=1, ln=True, align="R")

    # Prescriptions Table Rows
    if prescriptions:
        for item in prescriptions:
            # Ensure text fits, potentially use multi_cell if names are very long
            pdf.cell(130, 10, txt=str(item.get("name", "N/A")), border=1)
            pdf.cell(50, 10, txt=f"{item.get('fee', 0):,.0f}", border=1, ln=True, align="R")
    else:
        pdf.cell(180, 10, txt="처방 내역이 없습니다.", border=1, ln=True, align="C")

    # Total Fee
    pdf.set_font_size(12)
    pdf.cell(130, 10, txt="총계 (Total Fee)", border=1, align="R")
    pdf.cell(50, 10, txt=f"{total_fee:,.0f}", border=1, ln=True, align="R")
    pdf.ln(10)

    # Footer/Notes
    pdf.set_font_size(10)
    pdf.multi_cell(0, 7, txt="위와 같이 처방합니다.\n\n\n의사명: 김중앙 (서명/날인)")
    pdf.ln(5)
    pdf.cell(0, 7, txt="* 이 처방전은 발행일로부터 7일간 유효합니다.", ln=True)


    return pdf.output(dest='S').encode('latin-1')

def generate_medical_confirmation_pdf(patient_name, patient_rrn, disease_name):
    pdf = FPDF()
    pdf.add_page()
    _add_korean_font(pdf)

    # Title
    pdf.set_font_size(20)
    pdf.cell(0, 15, txt="진료확인서 (Medical Confirmation)", ln=True, align="C")
    pdf.ln(5)

    # Information
    pdf.set_font_size(12)
    current_date = datetime.now().strftime("%Y-%m-%d")
    pdf.cell(0, 7, txt=f"발행일: {current_date}", ln=True, align="R")
    pdf.cell(0, 7, txt="기관명: 중앙대 보건소", ln=True)
    pdf.cell(0, 7, txt=f"환자 성명: {patient_name}", ln=True)
    pdf.cell(0, 7, txt=f"주민등록번호: {patient_rrn}", ln=True)
    pdf.cell(0, 7, txt=f"진단명 (병명): {disease_name}", ln=True) # Department used as disease name
    pdf.ln(10)

    # Confirmation Statement
    # Using a more detailed confirmation text
    confirmation_text = (
        f"상기 환자는 위와 같은 진단명으로 {current_date} 본원에서 진료를 받았음을 확인합니다.\n\n"
        "This is to confirm that the patient named above received medical treatment at our clinic "
        f"on {current_date} for the diagnosis mentioned.\n\n"
        "진료의견: 안정가료 및 처방약 복용 요망.\n"
        "(Medical Opinion: Rest and medication as prescribed.)"
    )
    pdf.multi_cell(0, 7, txt=confirmation_text)
    pdf.ln(15)

    # Doctor's Confirmation
    pdf.set_font_size(12)
    pdf.cell(0, 10, txt="담당의사: 김중앙 (Dr. Kim, Joongang)", ln=True, align="R")
    pdf.cell(0, 10, txt="중앙대학교 보건소 (CAU Health Center)", ln=True, align="R")
    pdf.ln(5)
    # Placeholder for stamp/signature image if available
    # pdf.image("path/to/stamp.png", x=pdf.get_x() + 120, y=pdf.get_y() -10, w=30)


    return pdf.output(dest='S').encode('latin-1')
