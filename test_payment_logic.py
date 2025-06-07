import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.routes.chatbot import process_user_confirmed_payment, RESERVATIONS_CSV_PATH
# Removed unused imports: update_payment_status_in_csv, CHATBOT_BASE_DIR

class MockSession(dict):
    def get(self, key, default=None):
        # print(f"MockSession.get: key='{key}'") # Debug
        return super().get(key, default)

    def __setitem__(self, key, value):
        # print(f"MockSession.set: key='{key}', value='{value}'") # Debug
        super().__setitem__(key, value)
        if key == 'payment_complete' and value is True:
            print(f"MockSession: session['payment_complete'] was set to True by the tested function.")

def run_test():
    print(f"Using RESERVATIONS_CSV_PATH: {RESERVATIONS_CSV_PATH}")

    # Data for mock session
    initial_session_data = {
        'reception_complete': True,
        'payment_complete': False,
        'patient_rrn': "970405-1660660",
        'patient_name': "류열다",
        'department': "소화기내과"
    }

    import app.routes.chatbot
    original_session = app.routes.chatbot.session

    # Create the mock session instance that will be patched
    patched_session_instance = MockSession(initial_session_data)
    app.routes.chatbot.session = patched_session_instance

    print(f"Mock session (instance: {id(app.routes.chatbot.session)}) before call: {app.routes.chatbot.session}")

    user_message = "네"
    ai_response_text = "[USER_CONFIRMED_PAYMENT_INTENT] 수납이 완료되었습니다."

    print(f"Calling process_user_confirmed_payment with: user='{user_message}', ai_response='{ai_response_text}'")
    result = process_user_confirmed_payment(user_message, ai_response_text)
    print(f"Result from process_user_confirmed_payment: {result}")

    # IMPORTANT: Check the state of 'patched_session_instance' *before* restoring the original session
    payment_complete_in_mock = patched_session_instance.get('payment_complete')

    app.routes.chatbot.session = original_session # Restore original session

    if result is None:
        print("Test SUCCESS: process_user_confirmed_payment returned None (indicating success).")
    else:
        print(f"Test FAILURE: process_user_confirmed_payment returned '{result}' instead of None.")
        return False

    if payment_complete_in_mock is True:
        print("Test SUCCESS: 'payment_complete' was set to True in the mock session instance.")
    else:
        print(f"Test FAILURE: 'payment_complete' was '{payment_complete_in_mock}' in the mock session instance, expected True.")
        return False

    updated_csv_correctly = False
    try:
        with open(RESERVATIONS_CSV_PATH, 'r', newline='', encoding='utf-8-sig') as f:
            for line in f:
                if "970405-1660660" in line and "Paid" in line:
                    updated_csv_correctly = True
                    break
    except FileNotFoundError:
        print(f"Test FAILURE: CSV file {RESERVATIONS_CSV_PATH} not found during verification.")
        return False

    if updated_csv_correctly:
        print(f"Test SUCCESS: CSV file updated to 'Paid' for patient RRN 970405-1660660.")
    else:
        print(f"Test FAILURE: CSV file was NOT updated to 'Paid' for patient RRN 970405-1660660.")
        return False

    return True

if __name__ == "__main__":
    if run_test():
        print("All focused tests passed.")
        sys.exit(0)
    else:
        print("One or more focused tests failed.")
        sys.exit(1)
