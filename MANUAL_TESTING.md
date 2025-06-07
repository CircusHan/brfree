# Manual Testing Procedure for Certificate Generation

This document outlines the manual testing steps for the certificate (prescription and medical confirmation) generation feature.

## Pre-requisites for Manual Testing

1.  **Application Running**: Ensure the Flask application is running. This is typically done by executing `python run.py` from the project's root directory. The application should be accessible at `http://127.0.0.1:5001/`.
2.  **Dependencies Installed**: Ensure all Python dependencies, including `fpdf2`, are installed. This can usually be done by running `pip install -r requirements.txt`.
3.  **Korean Font File**:
    *   A Korean TrueType font file (`NanumSquareNeo-bRg.ttf`) must be placed at `app/static/fonts/NanumSquareNeo/NanumSquareNeo/TTF/NanumSquareNeo-bRg.ttf`.
    *   If this font file is missing or not accessible, the PDF generation will attempt to use a fallback font (Arial). In this case, Korean characters will likely not render correctly, and a warning message should appear at the top of the generated PDF.

## Test Steps

**Important Note**: Clear browser session/cache or use an incognito window between test cases that require a clean session state (like Test Case 3) to avoid interference from previous session data.

---

**Test Case 1: Full successful flow for "처방전" (Prescription PDF)**

*Objective: Verify the successful generation of a prescription PDF with correct data after completing the full user journey through reception and payment.*

1.  **Navigate to Reception**: Open a web browser and go to `http://127.0.0.1:5001/reception`.
2.  **Input Patient Details**:
    *   Choose the "직접 입력" (manual input) option.
    *   Enter a test name (e.g., "김환자").
    *   Enter a test RRN (e.g., "920202-1234567").
    *   Click "다음" (Next).
3.  **Select Symptom**:
    *   Select a symptom that maps to a department with available prescriptions in `data/treatment_fees.csv`. For example, select "기침‧가래" (which should map to "호흡기내과" or similar).
    *   Click "다음" (Next). A temporary ticket will be issued; note the department.
4.  **Navigate to Payment**: Go to `http://127.0.0.1:5001/payment/`.
5.  **Load Prescriptions**:
    *   Click the "처방 불러오기" (Load Prescriptions) button.
    *   **Verify**: Prescriptions related to the selected department should appear on the page, along with a total fee.
6.  **Navigate to Certificate Menu**: Go to `http://127.0.0.1:5001/certificate/`.
7.  **Request Prescription PDF**: Click the "처방전 발급" (Issue Prescription) button.
8.  **Expected Outcome**:
    *   A PDF document should open in the browser or be downloaded.
    *   **Filename**: Check that the filename is in the format `prescription_{RRN_PREFIX}_{TIMESTAMP}.pdf` (e.g., `prescription_920202_20231027_103000.pdf`).
    *   **Content Verification**:
        *   **Institution Name**: "중앙대 보건소" should be displayed prominently.
        *   **Patient Information**: The name ("김환자") and RRN ("920202-1234567") should be correct.
        *   **Department**: The selected department (e.g., "호흡기내과") should be listed.
        *   **Prescriptions**: The same prescriptions and total fee loaded in step 5 should be itemized correctly.
        *   **Korean Text**: All Korean text (titles, labels, patient data, prescription names) should be rendered correctly (requires the NanumSquareNeo font).
        *   **Date**: The current date should be displayed as the issue date.

---

**Test Case 2: Full successful flow for "진료확인서" (Medical Confirmation PDF)**

*Objective: Verify the successful generation of a medical confirmation PDF with correct data.*

1.  **Establish Session**: Ensure patient details (name, RRN) and department are in the session. This can be achieved by completing steps 1-3 of **Test Case 1**.
2.  **Navigate to Certificate Menu**: Go to `http://127.0.0.1:5001/certificate/`.
3.  **Request Confirmation PDF**: Click the "진료확인서 발급" (Issue Medical Confirmation) button.
4.  **Expected Outcome**:
    *   A PDF document should open in the browser or be downloaded.
    *   **Filename**: Check that the filename is in the format `medical_confirmation_{RRN_PREFIX}_{TIMESTAMP}.pdf` (e.g., `medical_confirmation_920202_20231027_103500.pdf`).
    *   **Content Verification**:
        *   **Institution Name**: "중앙대 보건소" should be displayed.
        *   **Patient Information**: The name ("김환자") and RRN ("920202-1234567") from the session should be correct.
        *   **Disease Name ("병명")**: This should be the department name stored in the session (e.g., "호흡기내과").
        *   **Confirmation Text**: Standard confirmation text should be present.
        *   **Korean Text**: All Korean text should be rendered correctly.
        *   **Date**: The current date should be displayed as the issue date.

---

**Test Case 3: Missing Patient Information (Direct Access to Certificate Routes)**

*Objective: Verify that users are redirected to reception if they try to access certificate generation without prior patient information in the session.*

1.  **Prepare Clean Session**: Use a new browser incognito window or clear session cookies for `127.0.0.1:5001`.
2.  **Navigate to Certificate Menu**: Go to `http://127.0.0.1:5001/certificate/`.
3.  **Attempt Prescription PDF**: Click "처방전 발급".
4.  **Expected Outcome**: The user should be redirected to the reception page (`http://127.0.0.1:5001/reception` or similar, possibly with an error query parameter like `?error=patient_info_missing`).
5.  **Attempt Confirmation PDF**: (Assuming still on certificate page, or navigate back if redirected) Click "진료확인서 발급".
6.  **Expected Outcome**: The user should be redirected to the reception page (`http://127.0.0.1:5001/reception` or similar, possibly with an error query parameter).

---

**Test Case 4: Missing Department/Prescription Data for "처방전" (Skipping Payment Load or Department without Items)**

*Objective: Verify redirection or appropriate handling if prescription data cannot be loaded for a "처방전". This specifically tests the logic in `app/routes/certificate.py`'s `generate_prescription_pdf` route when `_load_prescription_data` returns no items or an error.*

1.  **Establish Partial Session**: Complete steps 1-3 of **Test Case 1** to get patient name, RRN, and department into the session.
    *   *Alternative for testing no items*: If possible, temporarily modify `data/treatment_fees.csv` so the selected department has no listed items, or ensure a department is chosen for which no items exist.
2.  **Navigate Directly to Certificate Menu**: Go to `http://127.0.0.1:5001/certificate/` (crucially, *skip* the `/payment/` page and its "처방 불러오기" step).
3.  **Attempt Prescription PDF**: Click "처방전 발급".
4.  **Expected Outcome**:
    *   The user should be redirected to the payment page (`http://127.0.0.1:5001/payment/`, possibly with an error query parameter like `?error=no_prescription_items`). This is because the `prescription_info` in `certificate.py` would be empty or indicate an issue, triggering the redirect.

---

## General Checks for all Generated PDFs

For every PDF generated during the tests, perform the following checks:

*   **Korean Text Rendering**:
    *   If `NanumSquareNeo-bRg.ttf` is correctly installed: All Korean text (static labels, dynamic data) must be displayed clearly and correctly.
    *   If `NanumSquareNeo-bRg.ttf` is *not* installed: A warning message about the missing font should appear at the top of the PDF. Other text might render in Arial, and Korean characters will likely be broken/missing.
*   **Dynamic Data Accuracy**:
    *   Confirm that all pieces of dynamic information (patient name, RRN, selected department/disease name, prescription item names, individual fees, total fees, issue dates) are accurate as per the input or session data.
*   **Static Text Presence**:
    *   Confirm that static text elements like the institution name ("중앙대 보건소"), doctor's name ("김중앙"), and other standard phrases are present as expected.
*   **Layout and Formatting**:
    *   Check for any obvious layout issues, overlapping text, or formatting errors.

---

This concludes the manual testing procedure. Report any deviations from expected outcomes as bugs.
