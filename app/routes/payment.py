"""
진료비 수납 (Blueprint)
  • GET  /payment/       → 결제 폼
  • POST /payment/       → 결제 처리 → /payment/done
  • GET  /payment/done   → 결제 완료 화면
"""
import uuid
from flask import Blueprint, render_template, request, redirect, url_for

# ──────────────────────────────────────────────────────────
#  Blueprint 인스턴트를 'payment_bp'라는 이름으로 노출
# ──────────────────────────────────────────────────────────
payment_bp = Blueprint("payment", __name__, url_prefix="/payment")

# 인-메모리 결제 내역(데모용)
payments: list[dict] = []


@payment_bp.route("/", methods=["GET", "POST"])
def payment():
    """
    결제 폼 & 처리
    """
    if request.method == "POST":
        patient_id = request.form.get("patient_id", "").strip()

        # 천 단위 콤마가 들어와도 안전하게 float 변환
        amount_raw = request.form.get("amount", "0").replace(",", "")
        try:
            amount = float(amount_raw)
        except ValueError:
            amount = 0.0

        method = request.form.get("method", "card")  # cash | card | qr

        pay_id = uuid.uuid4().hex[:8].upper()
        payments.append(
            {"id": pay_id, "patient": patient_id, "amount": amount, "method": method}
        )

        # 완료 페이지로 리다이렉트
        return redirect(url_for("payment.done", pay_id=pay_id))

    # GET → 결제 입력 폼
    return render_template("payment.html", step="form")


@payment_bp.route("/done")
def done():
    """
    결제 완료 화면
    """
    pay_id = request.args.get("pay_id", "")
    record = next((p for p in payments if p["id"] == pay_id), None)

    # 잘못된 접근이면 다시 결제 폼으로
    if record is None:
        return redirect(url_for("payment.payment"))

    return render_template(
        "payment.html",
        step="done",
        pay_id=record["id"],
        amount=record["amount"],
        method=record["method"],
    )
