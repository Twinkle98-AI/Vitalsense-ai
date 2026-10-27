# VitalSense AI 🩺

**An AI-powered health record management application built with Python, Flask, SQLite, and NVIDIA NIM.**

VitalSense AI is an academic project that allows users to manage patient records, store blood test results, and generate AI-assisted remarks based on entered health data. The application combines a simple web interface with persistent database storage, input validation, and an external AI API integration.

> **Disclaimer:** VitalSense AI is an educational demonstration project. AI-generated remarks are informational only and must not be used for medical diagnosis, treatment, or clinical decision-making.

---

## ✨ Features

### Patient Record Management
- Add new patient records.
- View patient details and blood test results.
- Edit existing patient information.
- Delete patient records.
- Search patient records by name or email.
- Store patient information persistently using SQLite.

### Blood Test Information
The application records the following information:

- Full name
- Date of birth
- Email address
- Glucose level (mg/dL)
- Haemoglobin level (g/dL)
- Cholesterol level (mg/dL)
- AI-generated remarks

### AI Integration
- Connects to NVIDIA NIM through an external API.
- Generates AI-assisted remarks based on the available patient information.
- Uses environment variables to configure the API key, endpoint, and model.
- Keeps API credentials outside the application source code.

**Note:** AI availability and supported models depend on the NVIDIA NIM service and the model configured in the local environment.

### Input Validation
- Validates patient names and email addresses.
- Checks date-of-birth formatting and validity.
- Rejects future dates of birth.
- Checks laboratory values against configured input ranges.
- Handles invalid or missing patient records.

The configured laboratory value ranges are application-level validation rules, not medical diagnostic thresholds.

### Testing
- Automated tests for application routes.
- Tests for patient record database operations.
- Tests for input validation.
- Isolated test databases to help protect application data during database tests.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application programming language |
| Flask | Web application framework |
| SQLite | Persistent database |
| HTML5 | Page structure |
| CSS3 | User interface styling |
| JavaScript | Client-side interactions |
| NVIDIA NIM API | AI-assisted remarks |
| pytest | Automated testing |
| python-dotenv | Environment variable configuration |
| Git and GitHub | Version control and project hosting |

---

## 📁 Project Structure

```text
vitalsense-ai/
│
├── app.py
├── database.py
├── validators.py
├── ai_service.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── patient_detail.html
│   ├── patient_form.html
│   └── ...
│
├── static/
│   ├── css/
│   ├── js/
│   └── ...
│
├── tests/
│   ├── __init__.py
│   ├── test_app.py
│   ├── test_validators.py
│   └── test_database.py
│
├── instance/
│   └── vitalsense.db
│
└── .venv/
```

*The structure above illustrates the expected organization. Keep only filenames and folders that actually exist in your project. The virtual environment, local database, and `.env` file should not be committed to GitHub.*

---

## ⚙️ Prerequisites

Before running the application, install:

- Python 3.10 or a compatible version supported by your dependencies.
- Git, if you want to clone or manage the repository.
- An NVIDIA NIM API key for AI features.

Check your Python installation:

```bash
python --version
```

Check Git:

```bash
git --version
```

---

## 🚀 Installation and Setup

### 1. Clone the repository

Replace `YOUR-USERNAME` with your GitHub username.

```bash
git clone https://github.com/Twinkle98-AI/vitalsense-ai.git
cd vitalsense-ai
```

Alternatively, if you already have the project locally, open a terminal in the project directory.

### 2. Create a virtual environment

**Windows:**

```bash
python -m venv .venv
```

Activate it in Command Prompt:

```bat
.venv\Scripts\activate
```

Or in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If `requirements.txt` does not yet contain all the dependencies used by your application, update it before sharing the repository.

### 4. Configure environment variables

Create your local `.env` file by copying `.env.example`.

In Windows Command Prompt:

```bat
copy .env.example .env
```

In PowerShell:

```powershell
Copy-Item .env.example .env
```

Open `.env` and enter your own NVIDIA NIM configuration.

Example:

```dotenv
NVIDIA_API_KEY=your_actual_api_key
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=your_supported_model_id
SECRET_KEY=your_private_flask_secret
FLASK_DEBUG=False
```

**Important:**
- Replace the example values with valid local configuration.
- Use the exact environment variable names expected by your application code.
- Configure a model that is currently supported by your NVIDIA NIM account.
- Never commit `.env` or publish your API key.
- Do not copy real credentials into `.env.example`.

### 5. Initialize the database

The application should initialize its SQLite database when configured to do so by its startup code.

If initialization is not automatic, follow the initialization procedure implemented in `database.py` and `app.py`.

The local database is normally stored under the `instance/` directory.

**Warning:** Do not delete your existing database to troubleshoot setup unless you have backed up any records you need.

### 6. Run the application

From the project root, with the virtual environment activated:

```bash
python app.py
```

Open the local address printed in your terminal. For the development server, this is commonly:

```text
http://127.0.0.1:5000
```

Keep the terminal running while using the application.

To stop the server, press **Ctrl+C** in the terminal.

---

## 🧪 Running Automated Tests

Run the complete test suite from the project root:

```bash
python -m pytest -v
```

The test suite covers application routes, validation rules, and database operations when the corresponding test files are present.

To run a particular test file:

```bash
python -m pytest -v tests/test_app.py
```

```bash
python -m pytest -v tests/test_validators.py
```

```bash
python -m pytest -v tests/test_database.py
```

A successful test run should report that all collected tests passed.

---

## 📋 Typical Application Workflow

1. Open the VitalSense AI dashboard.
2. Navigate to the patient form.
3. Enter the patient's personal information and blood test results.
4. Submit the form and review any validation errors.
5. Save the valid patient record.
6. Open the patient's details to review stored information and AI-assisted remarks.
7. Edit a record to update its information.
8. Delete a record when required.
9. Run the automated tests to verify key application behavior.

The exact navigation and displayed information depend on the current implementation.

---

## 🔐 Security and Privacy

- API keys and private configuration belong in `.env`.
- `.env` should be excluded from version control.
- `.env.example` should contain placeholders only.
- Local database files should generally remain outside the public repository.
- Do not use real patient or personally identifiable health information in a public demonstration.
- Use synthetic records for screenshots, recordings, and testing.
- Do not expose secrets in terminal screenshots, demo videos, or repository commits.

---

## ⚠️ Limitations

- AI-generated remarks may be inaccurate, incomplete, or misleading.
- Availability depends on the external NVIDIA NIM service and configured model.
- Laboratory input validation does not establish whether a result is medically normal or abnormal.
- This project is not a validated medical device and is not intended to replace qualified healthcare professionals.

---

## 👩‍💻 Author

**Project:** VitalSense AI  
**Purpose:** Academic project demonstrating web development, database operations, input validation, automated testing, and external AI API integration.

**GitHub Repository:**  
`https://github.com/Twinkle98-AI/vitalsense-ai`

Replace the placeholder with your actual public repository link after publishing the project.

---

## 📄 License

No license has been specified yet. Add a `LICENSE` file if you decide to distribute the project under an open-source license.