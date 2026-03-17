# Physio Prescription Manager

A simple web application for managing physiotherapy patients and their prescriptions.

## Features

- **Patient Management**: Create and search patients by name or phone
- **Prescription Management**: Add, edit, and delete prescriptions for each patient
- **Visit History**: Track all visits and prescriptions for each patient
- **Simple Interface**: Clean, easy-to-use web interface

## Quick Start

### Option 1: Windows (Easy)
1. Double-click `start.bat`
2. Open your browser and go to http://127.0.0.1:8000

### Option 2: Manual Setup
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python run.py
   ```

3. Open your browser and go to http://127.0.0.1:8000

## Usage

1. **Search for a Patient**: Enter name or phone number on the home page
2. **Create New Patient**: If patient not found, click "Create New Patient"
3. **Add Prescription**: From patient detail page, click "Add New Prescription"
4. **Edit/Delete**: Use the buttons on each prescription to modify or remove

## Database

The application uses SQLite database (`physio.db`) which will be created automatically in the project folder.

## Files Structure

- `app.py` - Main FastAPI application
- `models.py` - Database models (Patient, Prescription)
- `database.py` - Database configuration
- `templates/` - HTML templates
- `requirements.txt` - Python dependencies
- `run.py` - Application startup script
- `start.bat` - Windows batch file for easy startup