# PHYSIO

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org)

A professional management system for physiotherapy clinics to track patient assessments, treatments, and progress.

---

## ✨ Key Features

- **👤 Patient Management**: Comprehensive profiles with quick search and history.
- **📝 Clinical Assessments**: Detailed initial assessments covering history, pain, physical exam, and goals.
- **🔄 Reassessments**: Dedicated progress tracking to monitor patient recovery over time.
- **📱 WhatsApp Integration**: Generate and share professional assessment reports directly via WhatsApp.
- **🛡️ Production Ready**: Configured for secure deployment on platforms like Railway or Render.

---

## 🚀 Quick Start

### For Windows Users
1. **Launch**: Double-click `start.bat`.
2. **Access**: Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

### Manual Setup (Developers)
1. **Clone & Enter**:
   ```bash
   git clone https://github.com/Aashikhandelwal05/physio.git
   cd physio
   ```
2. **Install**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run**:
   ```bash
   python run.py
   ```

---

## 📂 Project Structure

- `app.py`: Core FastAPI logic & web routes.
- `models.py`: Database schema (Patients, Assessments, Reassessments).
- `whatsapp.py`: Report generation for WhatsApp sharing.
- `database.py`: Database connection management.
- `templates/`: Modern, responsive HTML templates.

---

## ☁️ Deployment

This project is optimized for **Railway** (using SQLite with Persistent Volumes) or **Render** (using external Postgres).

- **Database**: Supports `DATABASE_URL` environment variable.
- **Security**: Requires `SECRET_KEY` in production environments.

---

## 🛠️ Built With

- **Backend**: FastAPI
- **Database**: SQLAlchemy (SQLite for local)
- **Templates**: Jinja2 & Vanilla CSS
- **Server**: Uvicorn / Gunicorn