"""
진료비 수납 (Blueprint)
  • GET  /payment/       → 결제 폼
  • POST /payment/       → 결제 처리 → /payment/done
  • GET  /payment/done   → 결제 완료 화면
"""
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
import random
import csv
import os

# ──────────────────────────────────────────────────────────
#  Blueprint 인스턴트를 'payment_bp'라는 이름으로 노출
# ──────────────────────────────────────────────────────────
payment_bp = Blueprint("payment", __name__, url_prefix="/payment")

# CSV 경로 --------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
TREATMENT_FEES_CSV = os.path.join(BASE_DIR, "data", "treatment_fees.csv")
RESERVATIONS_CSV = os.path.join(BASE_DIR, "data", "reservations.csv")

# 인-메모리 결제 내역(데모용)
payments: list[dict] = []


@payment_bp.route("/", methods=["GET", "POST"])
def payment():
    """
    결제 폼 & 처리
    """
    department = session.get("department")
    if not department:
        # If reception is not done, redirect. This also implies payment can't be complete.
        session['payment_complete'] = False # Explicitly set here
        return redirect(url_for("reception.reception"))

    if request.method == "GET":
        # When first loading the payment page for a valid user
        session['payment_complete'] = False # Reset if they are just landing here
        return render_template("payment.html", step="initial_payment", department=department)

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
    return render_template("payment.html", step="initial_payment", department=department)


@payment_bp.route("/load_prescriptions", methods=["GET"])
def load_prescriptions():
    department = session.get("department")
    if not department:
        return jsonify({"error": "Department not selected"}), 400

    if not os.path.exists(TREATMENT_FEES_CSV):
        return jsonify({"error": "Treatment fees data not found"}), 500

    prescriptions_for_dept = []
    try:
        with open(TREATMENT_FEES_CSV, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Department"].strip() == department:
                    prescriptions_for_dept.append({"Prescription": row["Prescription"], "Fee": float(row["Fee"])})
    except Exception as e:
        # Log the error e
        return jsonify({"error": "Error processing treatment fees data"}), 500

    if not prescriptions_for_dept:
        return jsonify({"prescriptions": [], "total_fee": 0.0})

    num_to_select = random.randint(2, 3)
    if len(prescriptions_for_dept) < num_to_select:
        selected_prescriptions = prescriptions_for_dept
    else:
        selected_prescriptions = random.sample(prescriptions_for_dept, num_to_select)

    total_fee = sum(p["Fee"] for p in selected_prescriptions)

    # Save the generated prescriptions and total fee for later use
    session["last_prescriptions"] = [
        {"name": p["Prescription"], "fee": float(p["Fee"])}
        for p in selected_prescriptions
    ]
    session["last_total_fee"] = total_fee

    return jsonify({"prescriptions": selected_prescriptions, "total_fee": total_fee})


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

    session['payment_complete'] = True

    # Update payment status in reservations.csv
    patient_rrn = session.get("patient_rrn")
    if patient_rrn:
        try:
            with open(RESERVATIONS_CSV, 'r', newline='', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                rows = list(reader)
                fieldnames = reader.fieldnames
                if not fieldnames: # Handle empty or malformed CSV
                    fieldnames = ['name', 'rrn', 'time', 'department', 'location', 'doctor', 'payment_status']


            updated = False
            for row in rows:
                if row.get("rrn") == patient_rrn:
                    row["payment_status"] = "Paid"
                    updated = True
                    break

            if updated:
                # Ensure 'payment_status' is in fieldnames if it wasn't (e.g., new file)
                # However, the previous step should have added it.
                # For robustness, especially if the file could be manually reverted or is new:
                if "payment_status" not in fieldnames:
                    # This situation implies the CSV was not pre-processed by step 1,
                    # or fieldnames were not captured correctly from an empty file.
                    # We'll add it, but this might indicate an issue if rows don't expect it.
                    # Given the problem description, 'payment_status' should exist.
                    # If `rows` came from DictReader, they are dicts. If fieldnames were empty
                    # and we defaulted them, this part is crucial.
                    # A truly robust solution for new/empty CSVs might need more logic
                    # or rely on `payment_status` definitely being there from step 1.
                    # For now, assume `fieldnames` from `DictReader` is correct if file not empty.
                    # If file was empty and `fieldnames` was empty, we manually set them.
                    # Let's assume 'payment_status' is expected.
                    pass # fieldnames should include it from DictReader or our default

                with open(RESERVATIONS_CSV, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
            elif not rows and fieldnames: # CSV was empty, write header if patient_rrn was somehow processed
                # This case is unlikely if patient_rrn implies an existing reservation.
                # But if we wanted to create a new entry, this might be relevant.
                # For now, we only update, so 'updated' being false on empty 'rows' is fine.
                with open(RESERVATIONS_CSV, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader() # Write header to empty file

        except FileNotFoundError:
            # Log this error: app.logger.error(f"Reservations file not found: {RESERVATIONS_CSV}")
            print(f"Error: Reservations file not found at {RESERVATIONS_CSV}")
            # Create the file with headers if it's missing
            try:
                with open(RESERVATIONS_CSV, 'w', newline='', encoding='utf-8') as file:
                    # Define default headers if file is created anew
                    default_fieldnames = ['name', 'rrn', 'time', 'department', 'location', 'doctor', 'payment_status']
                    writer = csv.DictWriter(file, fieldnames=default_fieldnames)
                    writer.writeheader()
                print(f"Created empty reservations file with headers at {RESERVATIONS_CSV}")
            except Exception as e_create:
                # Log this error: app.logger.error(f"Error creating reservations file: {e_create}")
                print(f"Error creating reservations file: {e_create}")
        except Exception as e:
            # Log this error: app.logger.error(f"Error updating payment status: {e}")
            print(f"Error updating payment status in CSV: {e}")
            # Depending on policy, may or may not want to pass silently
            pass

    return render_template(
        "payment.html",
        step="done",
        pay_id=record["id"],
        amount=record["amount"],
        method=record["method"],
    )
