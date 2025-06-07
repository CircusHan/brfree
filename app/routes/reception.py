# app/blueprints/reception.py
import csv, os, random
from datetime import datetime
from flask import Blueprint, render_template, request, session

reception_bp = Blueprint('reception', __name__, template_folder='../../templates')

# CSV 경로 --------------------------------------------------------------------
BASE_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
RESV_CSV  = os.path.join(BASE_DIR, "data", "reservations.csv")

# 주민등록증 스캔 더미 ---------------------------------------------------------
def fake_scan_rrn():
    """OCR 테스트용 – 실제 리더기로 바꾸세요"""
    return "홍길동", "900101-1234567"

# CSV 예약 조회 ---------------------------------------------------------------
def lookup_reservation(name: str, rrn: str):
    """
    reservations.csv 에서 (이름, 주민번호) 완전 일치 행을 찾아 dict 반환.
    못 찾으면 None.
    """
    if not os.path.exists(RESV_CSV):
        return None

    with open(RESV_CSV, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row["name"].strip() == name and row["rrn"].strip() == rrn:
                return {
                    "department": row["department"],
                    "time":       row["time"],
                    "location":   row["location"],
                    "doctor":     row["doctor"],
                    "status":     row.get("payment_status", "Pending")
                }
    return None

# 증상 → 진료과 매핑 ----------------------------------------------------------
SYMPTOMS = [
    ("fever",   "발열‧오한"), ("cough",  "기침‧가래"), ("soreth",  "인후통"),
    ("stomach", "복통‧소화불량"), ("diarr", "설사"),  ("headache", "두통"),
    ("dizzy",   "어지럼증"),    ("skin",  "피부발진"), ("injury",  "타박상‧상처"),
    ("etc",     "기타")
]
SYM_TO_DEPT = {
    "fever": "내과",        "cough": "호흡기내과", "soreth": "이비인후과",
    "stomach": "소화기내과","diarr": "감염내과",   "headache": "신경과",
    "dizzy": "신경과",      "skin": "피부과",      "injury": "외과",
    "etc": "가정의학과"
}

def new_ticket():
    return f"{datetime.now():%H%M}-{random.randint(100,999)}"

# 라우트 ----------------------------------------------------------------------
@reception_bp.route("/reception", methods=["GET", "POST"])
def reception():
    if request.method == "GET" and request.args.get("step", "method") == "method":
        session.pop('reception_complete', None)
        session.pop('payment_complete', None)
        session.pop('patient_name', None)
        session.pop('patient_rrn', None)
        session.pop('department', None)
        session.pop('ticket', None)

    if request.method == "POST":
        action = request.form.get("action")

        # 1) 주민등록증 인식 ---------------------------------------------------
        if action == "scan":
            name, rrn = fake_scan_rrn()
            session['patient_name'] = name
            session['patient_rrn'] = rrn
            resv = lookup_reservation(name, rrn)
            if resv:   # 예약 O → 안내
                session['reception_complete'] = True
                session['payment_complete'] = False
                return render_template("reception.html", step="reserved",
                                       name=name, **resv)
            # 예약 X → 증상 선택
            return render_template("reception.html", step="symptom",
                                   name=name, rrn=rrn, symptoms=SYMPTOMS)

        # 2) 개인정보 직접 입력 ------------------------------------------------
        if action == "manual":
            name = request.form.get("name", "").strip()
            rrn  = request.form.get("rrn",  "").strip()
            session['patient_name'] = name
            session['patient_rrn'] = rrn
            if not name or not rrn:
                return render_template("reception.html", step="input",
                                       err="이름과 주민번호를 모두 입력하세요.")
            resv = lookup_reservation(name, rrn)
            if resv:  # 예약 O
                session['reception_complete'] = True
                session['payment_complete'] = False
                return render_template("reception.html", step="reserved",
                                       name=name, **resv)
            # 예약 X
            return render_template("reception.html", step="symptom",
                                   name=name, rrn=rrn, symptoms=SYMPTOMS)

        # 3) 증상 선택 후 번호표 발급 ----------------------------------------
        if action == "choose_symptom":
            symptom    = request.form.get("symptom")
            department = SYM_TO_DEPT.get(symptom, "가정의학과")
            session["department"] = department
            ticket     = new_ticket()
            session["ticket"] = ticket
            session['reception_complete'] = True
            session['payment_complete'] = False
            return render_template("reception.html", step="ticket",
                                   department=department, ticket=ticket)

    # GET → 접수 방법 선택
    return render_template("reception.html", step="method")
