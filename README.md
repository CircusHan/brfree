# Barrier-Free Kiosk Software

This is a web-based kiosk application designed for accessibility in public health centers. It includes features such as reception check-in, payment processing, certificate issuance, and an AI-powered chatbot assistant.

## Installation

1.  **Prerequisites:**
    *   Python 3.8 or newer is recommended.
    *   Access to a terminal or command prompt.
    *   `NanumGothic.ttf` placed in `app/static/fonts/` for proper Korean text rendering in generated PDFs.

2.  **Clone the Repository (if applicable):**
    ```bash
    git clone https://github.com/example/brfree.git
    cd brfree
    ```
    *(If not cloning, ensure you are in the project's root directory. The project directory is named `brfree` in this example.)*

3.  **Create and Activate a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    ```
    *   On Windows:
        ```bash
        venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

4.  **Install Dependencies:**
    Make sure your virtual environment is activated. Then run:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Set Environment Variables:**
    This application uses the Google Gemini API for its AI Chatbot functionality. You need to set an API key for this service.
    *   **`GEMINI_API_KEY`**: Your API key for Google Gemini.

    You can set this variable in your terminal session before running the app:
    *   On Windows (Command Prompt):
        ```bash
        set GEMINI_API_KEY=YOUR_API_KEY_HERE
        ```
    *   On Windows (PowerShell):
        ```bash
        $env:GEMINI_API_KEY="YOUR_API_KEY_HERE"
        ```
    *   On macOS/Linux:
        ```bash
        export GEMINI_API_KEY=YOUR_API_KEY_HERE
        ```
    Replace `YOUR_API_KEY_HERE` with your actual Gemini API key. For persistent storage, consider using a `.env` file with a library like `python-dotenv` (though this is not implemented in the current project setup) or setting it in your system's environment variables.

6.  **Korean Font Setup:**
    Place the `NanumGothic.ttf` font file in `app/static/fonts/`. This font is required for Korean text to display correctly in generated PDFs.

## Running the Application

1.  **Ensure Environment Variables are Set:**
    Make sure you have set the `GEMINI_API_KEY` as described in the installation steps.

2.  **Activate Virtual Environment (if not already active):**
    *   On Windows:
        ```bash
        venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

3.  **Run the Flask Application:**
    From the project's root directory (where `run.py` is located):
    ```bash
    flask run
    ```
    Alternatively, you might run it using:
    ```bash
    python run.py
    ```
    The application will typically start on `http://127.0.0.1:5000/`.

4.  **Access in Browser:**
    Open your web browser and navigate to `http://127.0.0.1:5000/` to use the kiosk application.

## Key Features

*   **Reception (순번표):** Allows users to check in and get a queue number.
*   **Payment (수납):** Facilitates payment processing.
*   **Certificate Issuance (증명서 발급):** Enables users to request and receive various certificates.
*   **AI Chatbot Counseling (AI 챗봇 상담):**
    *   Provides an interactive AI assistant to answer questions and provide information about the health center.
    *   Utilizes webcam feed for potential visual queries (e.g., showing a document).
    *   Supports voice input (Korean) for hands-free interaction.
    *   Requires browser permissions for camera and microphone access.
*   **Accessibility Features:**
    *   Adjustable font sizes.
    *   Multilingual support (Korean and English).

## Browser and Permissions

*   **Recommended Browsers:** This application is best experienced on modern web browsers like Google Chrome, Mozilla Firefox, or Microsoft Edge.
*   **Permissions:** For the AI Chatbot to function fully (including webcam video and voice input), you will need to grant the website permission to access your camera and microphone when prompted by your browser.
