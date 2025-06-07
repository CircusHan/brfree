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

