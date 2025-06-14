import os
import csv # Added for potential direct use if lookup_reservation is adapted
import re # Added for regex parsing
import random # Added for get_prescription_details_for_payment
import google.generativeai as genai
from flask import Blueprint, request, jsonify, render_template, session, url_for
import base64
from io import BytesIO
# PIL might be needed for image validation or manipulation, but not directly for API call if blobs are correct
# from PIL import Image
from app.routes.reception import lookup_reservation # Added import

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api') # Added url_prefix for /api

# Path for treatment_fees.csv, assuming chatbot.py is in app/routes/
CHATBOT_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
TREATMENT_FEES_CSV_PATH = os.path.join(CHATBOT_BASE_DIR, "data", "treatment_fees.csv")
RESERVATIONS_CSV_PATH = os.path.join(CHATBOT_BASE_DIR, "data", "reservations.csv")


# System Prompt / Instructions for the Gemini Model (Synthesized from Kiosk2 context)
# This prompt guides the chatbot's behavior, personality, and response format.
SYSTEM_INSTRUCTION_PROMPT = """당신은 대한민국 공공 보건소의 친절하고 유능한 AI 안내원 '늘봄이'입니다. 당신의 주요 임무는 보건소 방문객들에게 필요한 정보와 지원을 제공하는 것입니다.

**당신의 역할:**
- 보건소의 다양한 서비스, 부서, 진료 절차, 건강 프로그램 등에 대한 정보를 제공합니다.
- 방문객의 질문에 명확하고 간결하며 이해하기 쉽게 답변합니다.
- 항상 친절하고 공손한 태도를 유지하며, 방문객이 편안함을 느낄 수 있도록 돕습니다.
- 복잡하거나 민감한 문의에 대해서는 적절한 보건소 직원에게 안내하거나, 추가 정보를 찾아볼 수 있는 방법을 제시합니다.
- 응급 상황 시 대처 요령을 안내하고, 필요시 즉시 도움을 요청할 수 있도록 안내합니다. (예: "즉시 119에 전화하시거나 가장 가까운 직원에게 알려주세요.")
- 개인적인 의학적 진단이나 처방은 제공하지 않으며, "의사 또는 전문 의료인과 상담하시는 것이 가장 좋습니다."와 같이 안내합니다.
- 사용자가 '처방전 발급' 또는 이와 유사한 요청을 하는 경우, 이는 처방전 발급 의도로 간주합니다. 응답에 `[PRESCRIPTION_CERTIFICATE_INTENT]` 특수 태그를 포함하십시오. (예: "처방전 발급을 원하시나요? [PRESCRIPTION_CERTIFICATE_INTENT]")
- 사용자가 '진료확인서 발급' 또는 이와 유사한 요청을 하는 경우, 이는 진료확인서 발급 의도로 간주합니다. 응답에 `[MEDICAL_CONFIRMATION_CERTIFICATE_INTENT]` 특수 태그를 포함하십시오. (예: "진료확인서 발급을 도와드릴까요? [MEDICAL_CONFIRMATION_CERTIFICATE_INTENT]")
- 사용자가 현재 진행 상태를 묻거나 다음에 무엇을 해야 할지 질문하는 경우 (예: "다음은 뭐에요?", "이제 뭐하면 돼요?", "접수 끝났나요?", "결제 할 수 있나요?"), 현재 키오스크 이용 상태를 확인하려는 의도로 간주하고, 응답에 `[CHECK_KIOSK_STATUS_INTENT]` 특수 태그를 포함하십시오. (예: "현재 상태를 확인해드릴까요? [CHECK_KIOSK_STATUS_INTENT]")
- 당신의 답변은 한국어로 제공되어야 합니다.

**응답 스타일:**
- 긍정적이고 따뜻한 어조를 사용합니다.
- 가능한 한 전문 용어 사용을 피하고, 쉬운 단어로 설명합니다.
- 필요한 경우, 정보를 단계별로 안내하여 방문객이 쉽게 따라올 수 있도록 합니다.
- 이모티콘이나 과도한 감탄사 사용은 자제하고, 전문성을 유지합니다.

**제한 사항:**
- 보건소 업무와 관련 없는 농담이나 사적인 대화는 지양합니다.
- 개인정보를 요청하거나 저장하지 마십시오.
- **세션 관리 및 사용자 안내:**
    - **접수 완료 후 안내**: 만약 `process_rrn_reception` 파이썬 함수가 성공적으로 실행되어 사용자에게 예약 정보(예: 환자 이름, 진료과, 예약 시간 등) 또는 증상 기반 접수 결과를 반환했다면, 이것은 '접수' 단계가 시스템 상 완료되었음을 의미합니다. 당신은 이 정보를 바탕으로 사용자에게 "네, [환자이름]님의 예약이 확인되어 접수가 완료되었습니다. 진료과 [진료과], 시간 [예약시간]입니다. 다음으로 수납을 진행하시겠습니까?" 또는 증상 접수의 경우 "네, [환자이름]님, [증상] 증상으로 [진료과] 접수가 완료되었습니다. 다음으로 수납을 진행하시겠습니까?" 와 같이 접수가 완료되었음을 명확히 알리고, 이어서 수납 진행 여부를 질문해야 합니다.
    - 사용자가 이름과 주민등록번호를 제공하며 접수를 요청하는 경우, 이를 `[RRN_RECEPTION_INTENT]`로 간주하고, 시스템이 이름과 주민등록번호를 추출하여 접수 처리를 시도할 수 있도록 해당 태그와 정보를 응답에 포함해야 합니다. (예: "성함 [이름], 주민등록번호 [주민번호]로 접수를 도와드릴까요? [RRN_RECEPTION_INTENT]")
    - 사용자가 수납/결제를 요청하고, 시스템이 `[RRN_PAYMENT_INTENT]` 태그와 함께 이름, 주민등록번호, 그리고 처방내역 및 예상 비용을 응답에 포함해야 할 경우: 당신의 역할은 시스템이 제공한 처방내역과 예상 비용을 사용자에게 안내하는 것입니다. 그 후, "처방내역과 예상 비용은 위와 같습니다. 결제를 진행하시겠습니까?" 라고 질문해야 합니다.
    - 사용자가 이전 단계에서 "결제를 진행하시겠습니까?" 라는 질문에 "네" 또는 긍정적으로 답변하는 경우, 이를 결제 확정 의사로 간주하고, 응답에 `[USER_CONFIRMED_PAYMENT_INTENT]` 라는 특수 태그를 포함하여 "수납이 완료되었습니다." 라고 응답해야 합니다.
- 일반적으로 사용자가 명시적으로 다음 단계(예: '수납', '처방전 발급', 또는 상태 확인 요청)를 요청하기 전까지는 해당 기능의 실행을 가정하거나 먼저 제안하지 마십시오. 사용자의 요청에 따라 기능을 안내하고, 필요한 경우 관련 정보를 요청합니다.
- 사용자가 이름과 주민등록번호로 접수를 요청하는 것으로 판단되면, 응답에 `[RRN_RECEPTION_INTENT]` 라는 특수 태그를 포함하고, 추출된 이름과 주민등록번호를 `이름: [이름], 주민번호: [주민번호]` 형식으로 포함해 주십시오. (예: "성함 [이름], 주민등록번호 [주민번호]로 접수를 진행하시겠습니까? [RRN_RECEPTION_INTENT]")
- 사용자가 이름과 주민등록번호를 사용하여 수납 또는 결제를 요청하는 것으로 판단되면, 응답에 `[RRN_PAYMENT_INTENT]` 라는 특수 태그를 포함하고, 추출된 이름과 주민등록번호를 `이름: [이름], 주민번호: [주민번호]` 형식으로 포함해 주십시오. (예: "성함 [이름], 주민등록번호 [주민번호]로 수납을 진행하시겠습니까? [RRN_PAYMENT_INTENT]")
- 정치적, 종교적 또는 논란의 여지가 있는 주제에 대해서는 중립적인 입장을 취하거나 답변을 정중히 거절합니다. ("죄송하지만, 해당 질문에 대해서는 답변드리기 어렵습니다.")

**이미지 입력 처리 (해당되는 경우):**
- 사용자가 이미지를 제공하면, 이미지의 내용을 이해하고 관련된 질문에 답변할 수 있습니다. (예: "이것은 무슨 약인가요?" 또는 "이 증상에 대해 알려주세요.")
- 이미지에 있는 글자를 읽고 해석할 수 있습니다.
- 이미지에 대한 분석이 불가능하거나 부적절한 경우, 정중하게 추가 정보를 요청하거나 답변할 수 없음을 알립니다.

이제 방문객의 질문에 답변해주세요."""

def process_rrn_reception(user_message, ai_response_text):
    """
    Processes the AI response to check for RRN reception intent and handles reservation lookup.
    """
    if "[RRN_RECEPTION_INTENT]" in ai_response_text:
        name = None
        rrn = None

        # Attempt to parse Name and RRN from AI response
        name_match_ai = re.search(r"(?:이름|성함)[\s:]*([가-힣]{2,10})", ai_response_text)  # Allow '성함' and optional colon
        rrn_match_ai = re.search(r"주민번호[\s:]*(\d{6}-\d{7})", ai_response_text)

        if name_match_ai and rrn_match_ai:
            name = name_match_ai.group(1)
            rrn = rrn_match_ai.group(1)
        else:
            # Fallback: Attempt to parse Name and RRN from user message
            name_match_user = re.search(r"([가-힣]{2,10})", user_message) # Adjusted length for name
            rrn_match_user = re.search(r"(\d{6}-\d{7})", user_message)

            if name_match_user:
                name_candidates = re.findall(r"([가-힣]{2,10})", user_message)
                if name_match_ai: name = name_match_ai.group(1)
                elif name_candidates: name = name_candidates[0] # Fallback to first found in user message

                if rrn_match_user:
                    rrn = rrn_match_user.group(1)
                elif rrn_match_ai:
                    rrn = rrn_match_ai.group(1)

            # Consolidate if one was found by AI and the other by user
            if not name and name_match_ai: name = name_match_ai.group(1)
            if not rrn and rrn_match_ai: rrn = rrn_match_ai.group(1)
            if not name and name_match_user: name = name_match_user.group(1) # Ensure user match is used if AI fails
            if not rrn and rrn_match_user: rrn = rrn_match_user.group(1) # Ensure user match is used if AI fails


        if name and rrn:
            try:
                # Assuming lookup_reservation is imported and works as expected
                # It might need the full path to CSV if not handled within lookup_reservation itself
                details = lookup_reservation(name, rrn) # Imported from app.routes.reception
                if details:
                    # Set session variables as if reception was done via web UI
                    session['reception_complete'] = True
                    session['payment_complete'] = False # Reset payment status
                    session['patient_name'] = name
                    session['patient_rrn'] = rrn
                    session['department'] = details.get('department')
                    update_reservation_status(rrn, "Registered")
                    # session['time'] = details.get('time') # Optional: Store if needed later
                    # session['location'] = details.get('location') # Optional: Store if needed later
                    # session['doctor'] = details.get('doctor') # Optional: Store if needed later

                    return f"성함 {name} 님, 예약이 확인되었습니다. 진료과: {details['department']}, 예약시간: {details['time']}, 위치: {details['location']}, 담당 의사: {details['doctor']} 입니다."
                else:
                    # No reservation found - do not set reception_complete.
                    return f"성함 {name}, 주민등록번호 {rrn} 님, 확인된 예약 내역이 없습니다. 증상으로 접수하시겠습니까?"
            except Exception as e:
                # Log the error for server-side review: print(f"Error in lookup_reservation: {e}")
                # Potentially, the CSV file might not be found or there's a format issue.
                # Provide a generic message to the user or indicate a system issue.
                return "예약 정보를 조회하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        else:
            # Tag was present, but name or RRN couldn't be parsed.
            # The AI should have asked for the information.
            # Return None to use the AI's original response (which might be asking for the info).
            return None # AI might be asking for clarification
    return None

def get_prescription_details_for_payment(department):
    if not os.path.exists(TREATMENT_FEES_CSV_PATH):
        print(f"Error: {TREATMENT_FEES_CSV_PATH} not found.") # Or log
        return None

    prescriptions_for_dept = []
    try:
        with open(TREATMENT_FEES_CSV_PATH, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Department"].strip().lower() == department.strip().lower(): # Case-insensitive department match
                    prescriptions_for_dept.append({"Prescription": row["Prescription"], "Fee": float(row["Fee"])})
    except Exception as e:
        print(f"Error reading/processing {TREATMENT_FEES_CSV_PATH}: {e}") # Or log
        return None

    if not prescriptions_for_dept:
        return {"prescriptions": [], "total_fee": 0.0, "error": f"진료과 '{department}'에 대한 처방 정보가 없습니다."}

    num_to_select = random.randint(2, 3)
    if len(prescriptions_for_dept) < num_to_select:
        selected_prescriptions = prescriptions_for_dept
    else:
        selected_prescriptions = random.sample(prescriptions_for_dept, num_to_select)

    total_fee = sum(p["Fee"] for p in selected_prescriptions)

    formatted_prescriptions = [{"name": p["Prescription"], "fee": p["Fee"]} for p in selected_prescriptions]

    return {"prescriptions": formatted_prescriptions, "total_fee": total_fee}

def process_rrn_payment(user_message, ai_response_text):
    if "[RRN_PAYMENT_INTENT]" not in ai_response_text:
        return None

    # Explicitly check if reception is complete
    if not session.get('reception_complete'):
        return "접수를 먼저 완료해주세요. 접수 완료 후 수납을 진행할 수 있습니다."

    name_match_ai = re.search(r"(?:이름|성함)[\s:]*([가-힣]{2,10})", ai_response_text)
    rrn_match_ai = re.search(r"주민번호[\s:]*(\d{6}-\d{7})", ai_response_text)

    name = name_match_ai.group(1) if name_match_ai else None
    rrn = rrn_match_ai.group(1) if rrn_match_ai else None

    if not name or not rrn:  # Fallback to user message
        name_match_user = re.search(r"([가-힣]{2,10})", user_message)
        rrn_match_user = re.search(r"(\d{6}-\d{7})", user_message)
        if not name and name_match_user:
            name = name_match_user.group(1)
        if not rrn and rrn_match_user:
            rrn = rrn_match_user.group(1)

    # Final fallback to session data if previous attempts failed
    if not name:
        name = session.get('patient_name')
    if not rrn:
        rrn = session.get('patient_rrn')

    if not name or not rrn:
        # AI indicated intent, but couldn't extract. AI should ask for info.
        return None

    reservation_details = lookup_reservation(name, rrn)
    if not reservation_details or not reservation_details.get("department"):
        return f"성함 {name}(주민번호 {rrn}) 님, 예약 정보를 찾을 수 없어 수납 처리를 진행할 수 없습니다. 먼저 접수를 완료해주세요."

    department = reservation_details["department"]
    payment_info = get_prescription_details_for_payment(department)

    if not payment_info:
        return f"성함 {name} 님 ({department}), 현재 해당 진료과에 대한 수납 정보를 불러올 수 없습니다. 직원에게 문의해주세요."

    if payment_info.get("error"):
         return f"성함 {name} 님 ({department}), 수납 정보 조회 중 오류: {payment_info['error']} 직원에게 문의해주세요."

    if not payment_info["prescriptions"]: # Handles empty list if no error key
        return f"성함 {name} 님 ({department}), 현재 해당 진료과에 대한 예상 처방내역이 없습니다. 직원에게 문의해주세요."

    presc_texts = []
    for p in payment_info["prescriptions"]:
        presc_texts.append(f"{p['name']} ({p['fee']:,.0f}원)") # Format fee with comma, no decimal for won
    prescriptions_string = ", ".join(presc_texts)
    total_fee_string = f"{payment_info['total_fee']:,.0f}"

    # Mark that the chatbot is waiting for the user to confirm the payment
    # This flag is checked in handle_chatbot_request before invoking Gemini.
    session['awaiting_payment_confirmation'] = True

    return f"성함 {name} 님 ({department} 진료), 예상 수납 정보입니다. 처방내역: {prescriptions_string}. 총 예상 금액은 {total_fee_string}원 입니다. 결제를 진행하시겠습니까?"


def process_prescription_certificate_request(user_message, ai_response_text):
    if "[PRESCRIPTION_CERTIFICATE_INTENT]" in ai_response_text:
        if not session.get('reception_complete'):
            return "접수를 먼저 완료해주세요. 접수 완료 후 처방전 발급을 요청해주세요."
        if not session.get('payment_complete'):
            return "수납을 먼저 완료해주세요. 수납 완료 후 처방전 발급을 요청해주세요."

        patient_name = session.get('patient_name')
        patient_rrn = session.get('patient_rrn')
        department = session.get('department')

        if not all([patient_name, patient_rrn, department]):
            return "환자 정보(성명, 주민번호, 진료과)가 세션에 없어 처방전을 발급할 수 없습니다. 접수부터 다시 진행해주세요."

        pdf_url = url_for('certificate.generate_prescription_pdf', _external=True)
        return {"reply": "처방전이 발급되었습니다.", "pdf_download_url": pdf_url, "audio_confirmation_url": "/static/audio/prescription_issued.mp3"}
    return None

def process_medical_confirmation_request(user_message, ai_response_text):
    if "[MEDICAL_CONFIRMATION_CERTIFICATE_INTENT]" in ai_response_text:
        if not session.get('reception_complete'):
            return "접수를 먼저 완료해주세요. 접수 완료 후 진료확인서 발급을 요청해주세요."
        if not session.get('payment_complete'):
            return "수납을 먼저 완료해주세요. 수납 완료 후 진료확인서 발급을 요청해주세요."

        patient_name = session.get('patient_name')
        patient_rrn = session.get('patient_rrn')
        department = session.get('department') # Used as disease_name

        if not all([patient_name, patient_rrn, department]):
            return "환자 정보(성명, 주민번호, 진료과)가 세션에 없어 진료확인서를 발급할 수 없습니다. 접수부터 다시 진행해주세요."

        pdf_url = url_for('certificate.generate_medical_confirmation_pdf', _external=True)
        return {"reply": "진료확인서가 발급되었습니다.", "pdf_download_url": pdf_url, "audio_confirmation_url": "/static/audio/medical_certificate_issued.mp3"}
    return None

def process_kiosk_status_check(user_message, ai_response_text):
    if "[CHECK_KIOSK_STATUS_INTENT]" in ai_response_text:
        reception_complete = session.get('reception_complete', False)
        payment_complete = session.get('payment_complete', False)

        if not reception_complete:
            return "현재 접수 단계입니다. 성함과 주민등록번호를 말씀해주시면 예약 확인 또는 신규 접수를 도와드리겠습니다. 또는 주요 증상을 말씀해주셔도 됩니다."
        elif not payment_complete:
            return "접수가 완료되었습니다. 다음은 수납 단계입니다. 처방 내역과 예상 비용을 안내받으시고 결제를 진행하시려면 '수납' 또는 '결제'라고 말씀해주세요."
        else:
            # Reception and payment are done.
            return "접수와 수납이 모두 완료되었습니다. 이제 증명서를 발급받으실 수 있습니다. 원하시는 증명서 종류를 말씀해주세요 (예: '처방전 발급' 또는 '진료확인서 발급')."
    return None

def update_reservation_status(rrn, status):
    """Update the payment_status column for a reservation identified by rrn."""
    if not rrn:
        return False

    expected_fieldnames = [
        'name', 'rrn', 'time', 'department', 'location', 'doctor', 'payment_status'
    ]

    try:
        rows = []
        current_fieldnames = []

        if not os.path.exists(RESERVATIONS_CSV_PATH):
            with open(RESERVATIONS_CSV_PATH, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=expected_fieldnames)
                writer.writeheader()
            return False

        with open(RESERVATIONS_CSV_PATH, 'r', newline='', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            current_fieldnames = reader.fieldnames or list(expected_fieldnames)
            rows = list(reader)

        if 'payment_status' not in current_fieldnames:
            current_fieldnames.append('payment_status')

        updated = False
        for row in rows:
            if 'payment_status' not in row:
                row['payment_status'] = 'Pending'
            if row.get('rrn') == rrn:
                if row.get('payment_status') != status:
                    row['payment_status'] = status
                updated = True

        if updated:
            with open(RESERVATIONS_CSV_PATH, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=current_fieldnames)
                writer.writeheader()
                writer.writerows(rows)

        return updated
    except Exception:
        return False

def update_payment_status_in_csv(patient_rrn):
    """Mark the given patient's reservation as Paid."""
    return update_reservation_status(patient_rrn, "Paid")

def process_user_confirmed_payment(user_message, ai_response_text):
    if "[USER_CONFIRMED_PAYMENT_INTENT]" in ai_response_text:
        if not session.get('reception_complete'):
            return "접수를 먼저 완료해주세요. 접수 완료 후 수납을 진행할 수 있습니다."

        if session.get('payment_complete'):
            return "이미 수납이 완료되었습니다. 증명서 발급 등 다음 서비스를 이용해주세요."

        patient_rrn = session.get('patient_rrn')
        if not patient_rrn:
            return "환자 정보(주민등록번호)가 없어 수납 처리를 완료할 수 없습니다. 접수를 다시 진행해주세요."

        if update_payment_status_in_csv(patient_rrn):
            session['payment_complete'] = True
            return None # Success, use AI's response ("수납이 완료되었습니다.")
        else:
            # Check if it failed because already paid vs actual error
            # For now, a general error if update_payment_status_in_csv didn't result in a positive update confirmation
            # or if the patient was not found.
            # If update_payment_status_in_csv returns True only when it actively changed status to "Paid"
            # or confirmed it is "Paid", this logic is okay.
            # The refined update_payment_status_in_csv returns True if target patient is now "Paid".
            return "수납 처리 중 오류가 발생했거나, 사용자 정보를 찾을 수 없어 완료하지 못했습니다. 직원에게 문의해주세요."
    return None # No intent match

@chatbot_bp.route('/chatbot', methods=['POST'])
def handle_chatbot_request():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON request"}), 400

    user_question = data.get('message')
    base64_image_data = data.get('base64_image_data')  # Optional

    if not user_question:
        return jsonify({"error": "No message (user_question) provided"}), 400

    # Handle simple payment confirmations without calling Gemini
    if session.get('awaiting_payment_confirmation'):
        confirmation_terms = ["네", "예", "수납해줘", "결제해줘"]
        clean_msg = user_question.strip()
        if any(term in clean_msg for term in confirmation_terms):
            patient_rrn = session.get('patient_rrn')
            if update_payment_status_in_csv(patient_rrn):
                session['payment_complete'] = True
            session.pop('awaiting_payment_confirmation', None)
            return jsonify({"reply": "수납이 완료되었습니다.", "audio_confirmation_url": "/static/audio/payment_completed.mp3"})

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "API key not configured"}), 500

    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        # This could catch issues with the API key format or other genai config errors
        return jsonify({"error": f"Failed to configure Generative AI: {str(e)}"}), 500

    model_name = "gemini-1.5-flash-latest"  # Or whichever model Kiosk2 used / is preferred
    model = genai.GenerativeModel(model_name)

    current_status = None
    name = session.get('patient_name')
    rrn = session.get('patient_rrn')
    if name and rrn:
        details = lookup_reservation(name, rrn)
        if details:
            current_status = details.get('status')

    prompt_parts = [SYSTEM_INSTRUCTION_PROMPT]

    if base64_image_data:
        try:
            # Remove potential data URI prefix (e.g., "data:image/jpeg;base64,")
            if ',' in base64_image_data:
                header, base64_image_data = base64_image_data.split(',', 1)
                # Infer mime_type from header if possible, otherwise default or require it
                mime_type = header.split(';')[0].split(':')[1] if header.startswith('data:') else "image/jpeg"
            else:
                # Assume it's raw base64 data, default mime_type
                mime_type = "image/jpeg" # Or require client to send mime_type

            image_bytes = base64.b64decode(base64_image_data)

            # Optional: Validate image using Pillow (robustness)
            # try:
            #     img = Image.open(BytesIO(image_bytes))
            #     img.verify() # Verify it's a valid image
            #     mime_type = Image.MIME.get(img.format) # Get accurate mime_type
            # except Exception as img_e:
            #     return jsonify({"error": f"Invalid image data: {str(img_e)}"}), 400

            image_blob = {"mime_type": mime_type, "data": image_bytes}
            prompt_parts.append(image_blob) # Append image if present
        except Exception as e:
            return jsonify({"error": f"Error processing image data: {str(e)}"}), 400

    state_tuple = (
        f"접수완료:{session.get('reception_complete')}, ",
        f"수납완료:{session.get('payment_complete')}, ",
        f"이름:{name}, ",
        f"주민번호:{rrn}, ",
        f"진료과:{session.get('department')}, ",
        f"상태:{current_status}"
    )
    for state_item in state_tuple:
        prompt_parts.append(state_item)

    prompt_parts.append("\n\n사용자 질문:\n")
    prompt_parts.append(user_question)

    try:
        # Generation config can be added here if needed (temperature, top_k, etc.)
        # generation_config = genai.types.GenerationConfig(temperature=0.7)
        response = model.generate_content(prompt_parts) #, generation_config=generation_config)

        # Check for safety ratings and blockages as in Kiosk2
        if not response.candidates:
            # This case might occur if the prompt itself was blocked even before generation attempt,
            # or if no candidates were generated for other reasons.
            # Check response.prompt_feedback if available and has block reason
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason = response.prompt_feedback.block_reason.name
                error_message = f"요청이 안전 설정에 의해 차단되었습니다. 이유: {block_reason}. 다른 질문을 시도해주세요."
                return jsonify({"error": "Blocked by safety settings", "details": error_message, "reply": error_message}), 400
            return jsonify({"error": "No response generated", "reply": "죄송합니다. 현재 답변을 생성할 수 없습니다. 잠시 후 다시 시도해주세요."}), 500


        # Ensure response.candidates[0].content.parts is safe to access
        if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                # ... (handle prompt blocked) ...
                error_message = f"요청이 안전 설정에 의해 차단되었습니다. 이유: {response.prompt_feedback.block_reason.name}."
                return jsonify({"error": "Blocked by safety settings", "details": error_message, "reply": error_message}), 400
            # This check should be more specific. If candidates exist but parts don't, it implies a non-STOP finish reason.
            if response.candidates and response.candidates[0].finish_reason != genai.types.Candidate.FinishReason.STOP:
                # ... (handle non-STOP finish reasons like SAFETY, RECITATION etc.) ...
                error_message = f"답변 생성 중 예상치 못한 이유({response.candidates[0].finish_reason.name})로 중단되었습니다."
                return jsonify({"error": "Response generation stopped", "reply": error_message}), 500
            # Default fallback if no parts for other reasons
            return jsonify({"reply": "죄송합니다. 질문에 대한 답변을 찾지 못했습니다."})

        bot_response_text = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, "text"))

        # Check for payment confirmation intent first
        if "[USER_CONFIRMED_PAYMENT_INTENT]" in bot_response_text:
            action_message = process_user_confirmed_payment(user_question, bot_response_text)
            if action_message:
                return jsonify({"reply": action_message})
            # If action_message is None, backend processing was successful.
            # bot_response_text (which should be "수납이 완료되었습니다.") will be used.
            # So, we fall through to the end of the function to return jsonify({"reply": bot_response_text})

        # Attempt to process for RRN reception
        reception_response = process_rrn_reception(user_question, bot_response_text)
        if reception_response:
            return jsonify({"reply": reception_response})

        # Attempt to process for RRN payment (this is the initial query for payment details)
        payment_query_response = process_rrn_payment(user_question, bot_response_text)
        if payment_query_response:
            return jsonify({"reply": payment_query_response})

        # Attempt to process for certificate intents
        prescription_cert_response = process_prescription_certificate_request(user_question, bot_response_text)
        if prescription_cert_response:
            if isinstance(prescription_cert_response, dict):
                return jsonify(prescription_cert_response)
            return jsonify({"reply": prescription_cert_response})

        medical_cert_response = process_medical_confirmation_request(user_question, bot_response_text)
        if medical_cert_response:
            if isinstance(medical_cert_response, dict):
                return jsonify(medical_cert_response)
            return jsonify({"reply": medical_cert_response})

        # Attempt to process for Kiosk Status Check
        status_check_response = process_kiosk_status_check(user_question, bot_response_text)
        if status_check_response:
            return jsonify({"reply": status_check_response})

        # If no special intent was processed, continue with original bot_response_text
        if not bot_response_text.strip():
            bot_response_text = "죄송합니다. 현재 적절한 답변을 드리기 어렵습니다. 다른 방식으로 질문해주시겠어요?"
        return jsonify({"reply": bot_response_text})

    except genai.types.BlockedPromptException as bpe:
        # This exception is specifically for when the prompt is blocked.
        # The general check above for response.prompt_feedback might catch this too.
        block_reason = str(bpe) # The exception itself might contain the reason
        error_message = f"요청이 안전 설정에 의해 차단되었습니다: {block_reason}. 다른 질문을 시도해주세요."
        return jsonify({"error": "Blocked by safety settings", "details": error_message, "reply": error_message}), 400
    except Exception as e:
        # General error handling for API calls or other unexpected issues
        # Log the error for server-side review: print(f"Error generating content: {e}")
        return jsonify({"error": "Error communicating with AI service", "reply": f"AI 서비스 오류: {str(e)}"}), 500

# Example of how to register this blueprint in app/__init__.py:
# from .routes.chatbot import chatbot_bp
# app.register_blueprint(chatbot_bp)

@chatbot_bp.route('/interface')
def chatbot_interface():
    """Renders the chatbot interface page."""
    return render_template("chatbot_interface.html")
