# 📄 AI-Powered Resume Analyzer & ATS Optimization Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-1.5%20Flash-8E75C2?style=for-the-badge&logo=google&logoColor=white)](https://aistudio.google.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com)
[![Tests](https://img.shields.io/badge/Pytest-Passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org)

An enterprise-grade, production-ready AI Resume Analyzer and ATS Optimization web application designed for students, freshers, and experienced professionals. The platform extracts structured data from PDF/DOCX resumes using Python NLP engines, evaluates resumes against deterministic ATS scoring algorithms, performs gap analysis against job descriptions, enhances content using Google Gemini AI, and compiles downloadable ATS-compliant resumes and audit reports.

---

## 🚀 Key Features

### 1. 🔐 User Authentication & Account Management
- Secure user registration, authentication, and session handling via **Flask-Login**.
- Strong password hashing with **Werkzeug Security** (`pbkdf2:sha256`).
- Profile management with customizable target career roles and in-app password changes.
- Role-based authorization (`user` and `admin`).

### 2. 📂 Multi-Format Resume Upload & Parsing
- Drag-and-drop or file-picker upload for **PDF** (`PyMuPDF`) and **DOCX** (`python-docx`).
- Robust text extraction, contact info detection (emails, phones, LinkedIn, GitHub, portfolios), and section segmentation.
- Comprehensive security validation for file types and sizes.

### 3. 🎯 100% Deterministic ATS Scoring Engine
Never generates fake or randomized numbers. Transparent weighted scoring breakdown:
- **Completeness Score (25%)**: Contact information and core section presence.
- **Technical Skills Score (25%)**: Depth and multi-category representation (Languages, Frameworks, Databases, Cloud/DevOps, Tools).
- **Keyword & Action Verbs Score (20%)**: Executive action verbs and industry keywords.
- **Formatting Score (15%)**: Section clarity, word count bounds (300–1200 words), and parsing clean ratio.
- **Content Quality Score (15%)**: Quantified metric achievements (percentages, revenue, throughput improvements) and bullet points.

### 4. 🎯 Job Description Matching & Gap Analysis
- Paste target job postings to compare against any saved resume.
- Automated extraction of required skills and side-by-side gap analysis.
- Compatibility score percentage and actionable learning roadmaps.

### 5. 🤖 Google Gemini AI Content Polish & Rewriter
- Rewrite professional summaries, work experience bullet points, and project descriptions.
- Preserves all real facts without fabricating false experience or credentials.
- Automatic heuristic fallback for offline execution.

### 6. 📝 ATS Resume Builder & PDF Generation
- Build resumes from scratch across three ATS-optimized layouts:
  1. **Classic ATS**: Single-column, timeless typographic standard.
  2. **Modern Tech**: Indigo accent bars, structured skill blocks.
  3. **Minimalist Executive**: Streamlined slate aesthetic with refined hierarchy.
- Compiles directly to downloadable PDF documents using **ReportLab**.

### 7. 📊 Interactive Dashboard & PDF Audit Reports
- Dashboard metrics and interactive charts using **Chart.js**.
- Instant export of comprehensive ATS audit reports as downloadable PDFs.
- Historical score comparisons and report management.

### 8. 🛡️ Admin Management Console
- Platform-wide statistics (total users, resumes, analyses, average scores).
- User management table with one-click administrative role toggling and user account removal.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| **Backend** | Python 3, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF |
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js, Font Awesome 6 |
| **Database** | MySQL (with SQLite local fallback) |
| **Document Processing**| PyMuPDF (`fitz`), `python-docx`, ReportLab |
| **AI Integration** | Google Gemini API (`google-generativeai`) |
| **Testing** | Pytest |
| **Deployment** | Render (`render.yaml`), Gunicorn |

---

## 🗄️ Database Architecture

The application defines 7 relational tables in MySQL (`app/models.py`):

1. **`users`**: User identities, hashed passwords, target roles, and administrator flags.
2. **`resumes`**: Stored resumes, raw extracted text, parsed section metadata, and file paths.
3. **`resume_analyses`**: Multi-dimensional ATS scores, qualitative feedback, strengths, and recommendations.
4. **`job_descriptions`**: Target job postings, required skills, matching vs. missing skills, compatibility score.
5. **`skills`**: Master dictionary of technical skills and categories.
6. **`analysis_history`**: Audit logs, score trends, and links to generated PDF reports.
7. **`resume_templates`**: ATS resume layout definitions and descriptions.

---

## ⚙️ Installation & Local Setup

### 1. Clone or Open the Repository
```bash
cd AI_RESUME_ANALYZER
```

### 2. Create and Activate a Python Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to supply your settings:
```ini
SECRET_KEY=your_secure_random_key
FLASK_DEBUG=1

# MySQL Database Connection
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/resume_analyzer

# Google Gemini API Key (optional for heuristic fallback, recommended for live AI)
GEMINI_API_KEY=your_gemini_api_key_from_ai_studio
```

> **Note on MySQL**: Create the MySQL database before starting:
> ```sql
> CREATE DATABASE resume_analyzer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
> ```
> *If MySQL is not installed locally, the application automatically falls back to local SQLite (`resume_analyzer.db`) for immediate execution!*

### 5. Run the Application
```bash
python run.py
```
Open your browser at `http://127.0.0.1:5000`.

---

## 🧪 Running Automated Tests

The platform includes 22 comprehensive unit and integration tests covering authentication, parsing, scoring, job matching, resume builder PDF compilation, and routes:

```bash
python -m pytest tests -v
```

---

## 🚢 Production Deployment (Render)

This repository includes a ready-to-deploy `render.yaml` specification:

1. Push your repository to GitHub.
2. On [Render](https://render.com), select **New Blueprint** and connect this repository.
3. Add the `GEMINI_API_KEY` and `DATABASE_URL` (MySQL instance) environment variables in the Render dashboard.
4. Deploy! Render will install dependencies and start the app using `gunicorn run:app`.

---

## 📜 License
Released under the MIT License. Built for students, engineers, and professionals striving for career excellence.
