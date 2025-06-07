"""
증명서 발급 (Blueprint)
  • GET  /certificate/  → 입력 폼
  • POST /certificate/  → 발급 완료 화면
"""
import uuid
from flask import Blueprint, render_template, request

# ──────────────────────────────────────────────────────────
# Blueprint 인스턴스를 'certificate_bp'라는 이름으로 노출
# ──────────────────────────────────────────────────────────
certificate_bp = Blueprint("certificate", __name__, url_prefix="/certificate")

# 간단한 인-메모리 저장소 (데모 용도)
issued_certs: list[dict] = []


@certificate_bp.route("/", methods=["GET", "POST"])
def certificate():
    """
    증명서 발급 액션
    """
    if request.method == "POST":
        patient_id      = request.form["patient_id"]
        cert_type       = request.form["cert_type"]        # diagnosis | visit | vaccination
        payment_method  = request.form["payment_method"]   # cash | card | qr

        cert_no = uuid.uuid4().hex[:8].upper()
        issued_certs.append(
            {"no": cert_no, "patient": patient_id, "type": cert_type}
        )

        return render_template(
            "certificate.html",
            step="done",
            cert_no=cert_no,
            cert_type=cert_type,
            payment_method=payment_method,
        )

    # GET 요청 → 입력 폼 렌더링
    return render_template("certificate.html", step="form")
