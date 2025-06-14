import os
import csv
import random
import io # Will be used for BytesIO for PDF generation
from datetime import datetime # For filename timestamp
from flask import (
    Blueprint, render_template, request, session, redirect, url_for, jsonify, Response
)
from app.utils.pdf_generator import (
    generate_prescription_pdf as create_prescription_pdf_bytes,
    generate_medical_confirmation_pdf as create_confirmation_pdf_bytes,
    MissingKoreanFontError,
)

certificate_bp = Blueprint(
    "certificate", __name__, url_prefix="/certificate", template_folder="../../templates"
)

# Data Paths
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
TREATMENT_FEES_CSV = os.path.join(BASE_DIR, "data", "treatment_fees.csv")
RESERVATIONS_CSV = os.path.join(BASE_DIR, "data", "reservations.csv")

# Helper function to load prescription data
def _load_prescription_data(department: str) -> dict | None:
    """
    Loads prescription data for a given department from TREATMENT_FEES_CSV.
    Selects 2-3 random prescriptions and calculates the total fee.
    Returns a dict with 'prescriptions' and 'total_fee', or None if error.
    """
    if not os.path.exists(TREATMENT_FEES_CSV):
        print(f"Error: {TREATMENT_FEES_CSV} not found.")
        return None

    department_prescriptions = []
    try:
        with open(TREATMENT_FEES_CSV, newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["Department"].strip() == department:
                    department_prescriptions.append(
                        {"name": row["Prescription"], "fee": int(row["Fee"])}
                    )
    except Exception as e:
        print(f"Error reading or parsing {TREATMENT_FEES_CSV}: {e}")
        return None

    if not department_prescriptions:
        print(f"No prescriptions found for department: {department}")
        return {"prescriptions": [], "total_fee": 0} # Return empty if no specific items

    num_to_select = random.randint(2, 3)
    if len(department_prescriptions) < num_to_select:
        selected_prescriptions = department_prescriptions
    else:
        selected_prescriptions = random.sample(department_prescriptions, num_to_select)

    total_fee = sum(item["fee"] for item in selected_prescriptions)

    return {"prescriptions": selected_prescriptions, "total_fee": total_fee}


@certificate_bp.route("/", methods=["GET"])
def certificate():
    """
    Renders the main certificate choice page.
    """
    return render_template("certificate.html")


@certificate_bp.route("/prescription/", methods=["GET"])
def generate_prescription_pdf():
    """
    Generates a prescription PDF (currently returns JSON).
    """
    patient_name = session.get("patient_name")
    patient_rrn = session.get("patient_rrn")
    department = session.get("department")

    if not patient_name or not patient_rrn:
        # If basic patient info is missing, redirect to reception
        return redirect(url_for("reception.reception", error="patient_info_missing"))

    if not department:
        # If department info is missing (needed for prescriptions), also redirect
        # Potentially pass an error message to reception or a general error page
        return redirect(url_for("reception.reception", error="department_info_missing"))

    # Payment verification logic
    payment_status_verified = False
    if patient_rrn: # Ensure RRN is available
        try:
            with open(RESERVATIONS_CSV, 'r', newline='', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row.get("rrn") == patient_rrn:
                        if row.get("payment_status") == "Paid":
                            payment_status_verified = True
                        break # Found patient's record
        except FileNotFoundError:
            # app.logger.error(f"Reservations CSV file not found: {RESERVATIONS_CSV}")
            return redirect(url_for("payment.payment", error="system_error_reservations_missing"))
        except Exception as e:
            # app.logger.error(f"Error reading reservations CSV: {e}")
            return redirect(url_for("payment.payment", error="system_error_csv_access"))

    if not payment_status_verified:
        session['payment_complete'] = False # Sync session state
        return redirect(url_for("payment.payment", error="payment_not_completed"))

    # Try to use prescription data stored during the payment step
    last_prescriptions = session.get("last_prescriptions")
    last_total_fee = session.get("last_total_fee")

    if last_prescriptions is not None and last_total_fee is not None:
        prescription_info = {
            "prescriptions": last_prescriptions,
            "total_fee": last_total_fee,
        }
        # Optionally clear the stored values after use
        session.pop("last_prescriptions", None)
        session.pop("last_total_fee", None)
    else:
        prescription_info = _load_prescription_data(department)

    if prescription_info is None or not prescription_info["prescriptions"]:
        # This could happen if CSV is missing, dept not found, or no items for dept.
        # Redirecting to payment, as per instruction, though this might be confusing.
        # A better UX might be to show an error on the certificate page itself
        # or guide the user more clearly.
        # For now, let's consider if there's a way to inform payment page.
        # Or, redirect back to reception if the issue is fundamental like unknown dept.
        # If department exists but has no items, that's a specific case.
        # Let's redirect to payment and it can handle "no items".
        return redirect(url_for("payment.payment", error="no_prescription_items"))


    # Generate PDF
    try:
        pdf_bytes = create_prescription_pdf_bytes(
            patient_name=patient_name,
            patient_rrn=patient_rrn,
            department=department,
            prescriptions=prescription_info["prescriptions"],
            total_fee=prescription_info["total_fee"],
        )
    except MissingKoreanFontError as e:
        return render_template("error.html", message=str(e)), 500

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"prescription_{patient_rrn.split('-')[0]}_{timestamp}.pdf"

    return Response(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment;filename={filename}'}
    )


@certificate_bp.route("/medical_confirmation/", methods=["GET"])
def generate_confirmation_pdf():
    """
    Generates a medical confirmation PDF (currently returns JSON).
    """
    patient_name = session.get("patient_name")
    patient_rrn = session.get("patient_rrn")
    department = session.get("department") # Used as "병명" (diagnosis/reason for visit)

    if not patient_name or not patient_rrn:
        return redirect(url_for("reception.reception", error="patient_info_missing"))

    if not department: # Department is essential for "병명"
        return redirect(url_for("reception.reception", error="department_info_missing_for_confirmation"))

    # Payment verification logic
    payment_status_verified = False
    if patient_rrn: # Ensure RRN is available
        try:
            with open(RESERVATIONS_CSV, 'r', newline='', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row.get("rrn") == patient_rrn:
                        if row.get("payment_status") == "Paid":
                            payment_status_verified = True
                        break # Found patient's record
        except FileNotFoundError:
            # app.logger.error(f"Reservations CSV file not found: {RESERVATIONS_CSV}")
            return redirect(url_for("payment.payment", error="system_error_reservations_missing"))
        except Exception as e:
            # app.logger.error(f"Error reading reservations CSV: {e}")
            return redirect(url_for("payment.payment", error="system_error_csv_access"))

    if not payment_status_verified:
        session['payment_complete'] = False # Sync session state
        return redirect(url_for("payment.payment", error="payment_not_completed"))

    # Generate PDF
    try:
        pdf_bytes = create_confirmation_pdf_bytes(
            patient_name=patient_name,
            patient_rrn=patient_rrn,
            disease_name=department,  # department is used as disease_name
        )
    except MissingKoreanFontError as e:
        return render_template("error.html", message=str(e)), 500

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"medical_confirmation_{patient_rrn.split('-')[0]}_{timestamp}.pdf"

    return Response(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment;filename={filename}'}
    )
