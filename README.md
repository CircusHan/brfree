# Barrier-Free Kiosk Software

This project provides a sample web kiosk application targeted at public health centers.
It focuses on accessibility so that visitors of all ages can easily check in,
make payments, print certificates and interact with an AI assistant.

## Features

- **Reception** – scan or manually enter resident registration information and
  receive a ticket number.
- **Payment** – simple payment form that loads recommended prescriptions from
  `data/treatment_fees.csv` and records payment details.
- **Certificate Issuance** – generates PDF prescriptions and medical
  confirmations. Korean text in the PDFs requires the NanumSquareNeo font.
- **AI Chatbot** – powered by Google Gemini to answer common questions.
- **Adjustable Font Size** and basic language support (Korean/English).

## Installation

1. **Prerequisites**
   - Python 3.8 or newer.
   - A terminal or command prompt.
   - A TrueType font file `NanumSquareNeo-bRg.ttf` placed in
     `app/static/fonts/NanumSquareNeo/NanumSquareNeo/TTF/` so PDF output shows Korean correctly.
     The font is included in this repository under that directory.

2. **Clone the repository**
   ```bash
   git clone https://github.com/example/brfree.git
   cd brfree
   ```
   *(If not cloning, make sure the current directory is the project root.)*

3. **Create and activate a virtual environment** (recommended)
   ```bash
   python -m venv venv
   ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   The AI chatbot uses the Google Gemini API. Set your API key before running:
   - On Windows (Command Prompt)
     ```bash
     set GEMINI_API_KEY=YOUR_API_KEY
     ```
   - On Windows (PowerShell)
     ```bash
     $env:GEMINI_API_KEY="YOUR_API_KEY"
     ```
   - On macOS/Linux
     ```bash
     export GEMINI_API_KEY=YOUR_API_KEY
     ```
   Replace `YOUR_API_KEY` with the key you obtained from Google.

## Running the Application

After installing dependencies and setting the environment variable, start the
Flask development server:

```bash
python run.py
```

The kiosk will be available at <http://127.0.0.1:5001/>.

When generating PDFs, if `NanumSquareNeo-bRg.ttf` is missing you will see a warning in
the PDF and Korean characters may not render correctly. Ensure the font file is
present in `app/static/fonts/NanumSquareNeo/NanumSquareNeo/TTF/`.
