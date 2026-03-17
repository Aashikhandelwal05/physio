import os
import re
import json
import urllib.parse
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from models import Patient, Assessment, Reassessment
from database import engine, Base, get_db
from whatsapp import generate_assessment_report, generate_reassessment_report

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Balaji Neurophysiotherapy Clinic & Rehabilitation Center")

# Mount static folder for the logo
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add session middleware
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
if SECRET_KEY == "dev-secret-change-in-production":
    print("WARNING: Using default SECRET_KEY. Set SECRET_KEY environment variable in production!")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Setup templates
templates = Jinja2Templates(directory="templates")

# ── Helpers ──────────────────────────────────────────────────────────────

def validate_patient_fields(name: str, phone: str, age: int = None):
    """Validate patient form fields. Returns error message or None."""
    name = name.strip()
    phone = phone.strip()
    if not name or len(name) < 2:
        return "Name must be at least 2 characters"
    if len(name) > 100:
        return "Name must be 100 characters or less"
    if not phone:
        return "Phone number is required"
    phone_digits = re.sub(r'[\s\-]', '', phone)
    if not phone_digits.isdigit():
        return "Phone number must contain only digits"
    if len(phone_digits) != 10:
        return "Phone number must be exactly 10 digits"
    if age is not None and (age < 1 or age > 120):
        return "Age must be between 1 and 120"
    return None


def get_form_list(form_data: dict, key: str) -> str:
    """Get comma-separated string from checkbox group in form data."""
    values = form_data.getlist(key)
    return ",".join(values) if values else ""


def split_csv(value: str) -> list:
    """Split comma-separated string into list for template rendering."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


# Make split_csv available in templates
templates.env.globals["split_csv"] = split_csv


# ── HOME PAGE ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, q: str = "", db: Session = Depends(get_db)):
    patients = []
    no_results = False
    search_query = q.strip()

    if search_query:
        patients = db.query(Patient).filter(
            (Patient.name.ilike(f"%{search_query}%")) |
            (Patient.phone.ilike(f"%{search_query}%"))
        ).order_by(Patient.name).all()
        if not patients:
            no_results = True
    else:
        # Show recent patients on home page
        patients = db.query(Patient).order_by(Patient.created_at.desc()).limit(10).all()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "patients": patients,
        "search_query": search_query,
        "no_results": no_results,
        "is_search": bool(search_query),
    })


@app.post("/search")
async def search_patient(
    request: Request,
    search_query: str = Form(...),
    db: Session = Depends(get_db)
):
    """POST fallback — redirects to GET search."""
    return RedirectResponse(url=f"/?q={search_query.strip()}", status_code=303)


@app.get("/api/search")
async def api_search(q: str = "", db: Session = Depends(get_db)):
    """JSON API for live search-as-you-type."""
    q = q.strip()
    if not q:
        return []
    patients = db.query(Patient).filter(
        (Patient.name.ilike(f"%{q}%")) |
        (Patient.phone.ilike(f"%{q}%"))
    ).order_by(Patient.name).limit(10).all()
    return [
        {"id": p.id, "name": p.name, "phone": p.phone, "age": p.age, "gender": p.gender or ""}
        for p in patients
    ]


# ── PATIENT CRUD ─────────────────────────────────────────────────────────

@app.get("/patient/new", response_class=HTMLResponse)
async def create_patient_form(request: Request, name: str = ""):
    return templates.TemplateResponse("create_patient.html", {
        "request": request, "prefill_name": name
    })


@app.post("/patient/new")
async def create_patient(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    age: int = Form(None),
    gender: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    name = name.strip()
    phone = re.sub(r'[\s\-]', '', phone.strip())
    notes = notes.strip()

    error = validate_patient_fields(name, phone, age)
    if error:
        return templates.TemplateResponse("create_patient.html", {
            "request": request, "error": error,
            "name": name, "phone": phone, "age": age, "gender": gender, "notes": notes
        })

    existing = db.query(Patient).filter(Patient.phone == phone).first()
    if existing:
        return templates.TemplateResponse("create_patient.html", {
            "request": request,
            "error": f"A patient with phone {phone} already exists ({existing.name})",
            "name": name, "phone": phone, "age": age, "gender": gender, "notes": notes
        })

    new_patient = Patient(name=name, phone=phone, age=age, gender=gender, notes=notes)
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return RedirectResponse(url=f"/patient/{new_patient.id}?created=1", status_code=303)


@app.get("/patient/{patient_id}/edit", response_class=HTMLResponse)
async def edit_patient_form(request: Request, patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return templates.TemplateResponse("edit_patient.html", {"request": request, "patient": patient})


@app.post("/patient/{patient_id}/edit")
async def edit_patient(
    request: Request, patient_id: int,
    name: str = Form(...), phone: str = Form(...),
    age: int = Form(None), gender: str = Form(""),
    notes: str = Form(""), db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    name = name.strip()
    phone = re.sub(r'[\s\-]', '', phone.strip())
    notes = notes.strip()

    error = validate_patient_fields(name, phone, age)
    if error:
        patient.name = name; patient.phone = phone; patient.age = age
        patient.gender = gender; patient.notes = notes
        return templates.TemplateResponse("edit_patient.html", {
            "request": request, "patient": patient, "error": error
        })

    existing = db.query(Patient).filter(Patient.phone == phone, Patient.id != patient_id).first()
    if existing:
        patient.name = name; patient.phone = phone; patient.age = age
        patient.gender = gender; patient.notes = notes
        return templates.TemplateResponse("edit_patient.html", {
            "request": request, "patient": patient,
            "error": f"Phone {phone} is already used by {existing.name}"
        })

    patient.name = name
    patient.phone = phone
    patient.age = age
    patient.gender = gender
    patient.notes = notes
    db.commit()
    return RedirectResponse(url=f"/patient/{patient_id}?patient_updated=1", status_code=303)


@app.post("/patient/{patient_id}/doctor-assessment")
async def save_doctor_assessment(
    request: Request, patient_id: int, db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    form = await request.form()
    patient.doctor_assessment = form.get("doctor_assessment", "")
    db.commit()
    return RedirectResponse(url=f"/patient/{patient_id}?doctor_updated=1", status_code=303)


@app.post("/patient/{patient_id}/delete")
async def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return RedirectResponse(url="/?deleted=1", status_code=303)


# ── PATIENT DETAIL ───────────────────────────────────────────────────────

@app.get("/patient/{patient_id}", response_class=HTMLResponse)
async def patient_detail(request: Request, patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    assessments = sorted(patient.assessments, key=lambda x: x.assessment_date, reverse=True)

    # Success message from query params
    msg_map = {
        "created": "Patient created successfully!",
        "patient_updated": "Patient details updated!",
        "doctor_updated": "Doctor assessment saved!",
        "assessment_added": "Assessment added successfully!",
        "assessment_updated": "Assessment updated!",
        "assessment_deleted": "Assessment deleted!",
        "reassessment_added": "Reassessment added!",
        "reassessment_deleted": "Reassessment deleted!",
    }
    message = None
    for key, msg in msg_map.items():
        if request.query_params.get(key):
            message = msg
            break

    return templates.TemplateResponse("patient_detail.html", {
        "request": request, "patient": patient,
        "assessments": assessments, "success_message": message
    })


# ── ASSESSMENT CRUD ──────────────────────────────────────────────────────

@app.get("/patient/{patient_id}/assessment/new", response_class=HTMLResponse)
async def add_assessment_form(request: Request, patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return templates.TemplateResponse("add_assessment.html", {"request": request, "patient": patient})


@app.post("/patient/{patient_id}/assessment/new")
async def add_assessment(request: Request, patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    form = await request.form()

    assessment = Assessment(
        patient_id=patient_id,
        # Referral
        referring_doctor=form.get("referring_doctor", ""),
        history=form.get("history", ""),
        referral_reasons=",".join(form.getlist("referral_reasons")),
        referral_other=form.get("referral_other", ""),
        # Chief Complaint
        chief_complaint=form.get("chief_complaint", ""),
        # Pain
        pain_location=form.get("pain_location", ""),
        pain_intensity=int(form.get("pain_intensity")) if form.get("pain_intensity") else None,
        pain_quality=form.get("pain_quality", ""),
        pain_aggravating=form.get("pain_aggravating", ""),
        pain_relieving=form.get("pain_relieving", ""),
        pain_duration=form.get("pain_duration", ""),
        previous_treatments=form.get("previous_treatments", ""),
        # Medical History
        medical_conditions=",".join(form.getlist("medical_conditions")),
        previous_surgeries=form.get("previous_surgeries", ""),
        medications=form.get("medications", ""),
        other_medical_history=form.get("other_medical_history", ""),
        # Functional Status
        mobility=form.get("mobility", ""),
        adls=form.get("adls", ""),
        work_leisure=form.get("work_leisure", ""),
        physical_activity=form.get("physical_activity", ""),
        # Physical Exam
        posture_gait=form.get("posture_gait", ""),
        posture_gait_details=form.get("posture_gait_details", ""),
        rom_cervical=form.get("rom_cervical", ""),
        rom_lumbar=form.get("rom_lumbar", ""),
        rom_shoulder=form.get("rom_shoulder", ""),
        rom_hip=form.get("rom_hip", ""),
        rom_knee=form.get("rom_knee", ""),
        rom_ankle=form.get("rom_ankle", ""),
        strength_upper=form.get("strength_upper", ""),
        strength_lower=form.get("strength_lower", ""),
        neuro_sensory=form.get("neuro_sensory", ""),
        neuro_sensory_details=form.get("neuro_sensory_details", ""),
        neuro_reflexes=form.get("neuro_reflexes", ""),
        neuro_reflexes_details=form.get("neuro_reflexes_details", ""),
        neuro_coordination=form.get("neuro_coordination", ""),
        neuro_coordination_details=form.get("neuro_coordination_details", ""),
        respiratory=form.get("respiratory", ""),
        respiratory_details=form.get("respiratory_details", ""),
        swelling=form.get("swelling", ""),
        swelling_location=form.get("swelling_location", ""),
        special_tests=form.get("special_tests", ""),
        # Assessment Summary
        diagnosis=form.get("diagnosis", ""),
        problem_list=form.get("problem_list", ""),
        impairments=form.get("impairments", ""),
        goals_short_term=form.get("goals_short_term", ""),
        goals_long_term=form.get("goals_long_term", ""),
        # Treatment Plan
        treatment_modalities=",".join(form.getlist("treatment_modalities")),
        treatment_other=form.get("treatment_other", ""),
        session_frequency=form.get("session_frequency", ""),
        session_frequency_other=form.get("session_frequency_other", ""),
        treatment_duration=form.get("treatment_duration", ""),
        treatment_duration_other=form.get("treatment_duration_other", ""),
        patient_education=form.get("patient_education", ""),
        education_details=form.get("education_details", ""),
        physiotherapist_name=form.get("physiotherapist_name", ""),
    )
    db.add(assessment)
    db.commit()
    return RedirectResponse(url=f"/patient/{patient_id}?assessment_added=1", status_code=303)


@app.get("/assessment/{assessment_id}", response_class=HTMLResponse)
async def view_assessment(request: Request, assessment_id: int, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    reassessments = sorted(assessment.reassessments, key=lambda x: x.reassessment_date, reverse=True)
    return templates.TemplateResponse("view_assessment.html", {
        "request": request, "a": assessment, "patient": assessment.patient,
        "reassessments": reassessments
    })


@app.get("/assessment/{assessment_id}/edit", response_class=HTMLResponse)
async def edit_assessment_form(request: Request, assessment_id: int, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return templates.TemplateResponse("edit_assessment.html", {
        "request": request, "a": assessment, "patient": assessment.patient
    })


@app.post("/assessment/{assessment_id}/edit")
async def edit_assessment(request: Request, assessment_id: int, db: Session = Depends(get_db)):
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")

    form = await request.form()

    # Update all fields
    a.referring_doctor = form.get("referring_doctor", "")
    a.history = form.get("history", "")
    a.referral_reasons = ",".join(form.getlist("referral_reasons"))
    a.referral_other = form.get("referral_other", "")
    a.chief_complaint = form.get("chief_complaint", "")
    a.pain_location = form.get("pain_location", "")
    a.pain_intensity = int(form.get("pain_intensity")) if form.get("pain_intensity") else None
    a.pain_quality = form.get("pain_quality", "")
    a.pain_aggravating = form.get("pain_aggravating", "")
    a.pain_relieving = form.get("pain_relieving", "")
    a.pain_duration = form.get("pain_duration", "")
    a.previous_treatments = form.get("previous_treatments", "")
    a.medical_conditions = ",".join(form.getlist("medical_conditions"))
    a.previous_surgeries = form.get("previous_surgeries", "")
    a.medications = form.get("medications", "")
    a.other_medical_history = form.get("other_medical_history", "")
    a.mobility = form.get("mobility", "")
    a.adls = form.get("adls", "")
    a.work_leisure = form.get("work_leisure", "")
    a.physical_activity = form.get("physical_activity", "")
    a.posture_gait = form.get("posture_gait", "")
    a.posture_gait_details = form.get("posture_gait_details", "")
    a.rom_cervical = form.get("rom_cervical", "")
    a.rom_lumbar = form.get("rom_lumbar", "")
    a.rom_shoulder = form.get("rom_shoulder", "")
    a.rom_hip = form.get("rom_hip", "")
    a.rom_knee = form.get("rom_knee", "")
    a.rom_ankle = form.get("rom_ankle", "")
    a.strength_upper = form.get("strength_upper", "")
    a.strength_lower = form.get("strength_lower", "")
    a.neuro_sensory = form.get("neuro_sensory", "")
    a.neuro_sensory_details = form.get("neuro_sensory_details", "")
    a.neuro_reflexes = form.get("neuro_reflexes", "")
    a.neuro_reflexes_details = form.get("neuro_reflexes_details", "")
    a.neuro_coordination = form.get("neuro_coordination", "")
    a.neuro_coordination_details = form.get("neuro_coordination_details", "")
    a.respiratory = form.get("respiratory", "")
    a.respiratory_details = form.get("respiratory_details", "")
    a.swelling = form.get("swelling", "")
    a.swelling_location = form.get("swelling_location", "")
    a.special_tests = form.get("special_tests", "")
    a.diagnosis = form.get("diagnosis", "")
    a.problem_list = form.get("problem_list", "")
    a.impairments = form.get("impairments", "")
    a.goals_short_term = form.get("goals_short_term", "")
    a.goals_long_term = form.get("goals_long_term", "")
    a.treatment_modalities = ",".join(form.getlist("treatment_modalities"))
    a.treatment_other = form.get("treatment_other", "")
    a.session_frequency = form.get("session_frequency", "")
    a.session_frequency_other = form.get("session_frequency_other", "")
    a.treatment_duration = form.get("treatment_duration", "")
    a.treatment_duration_other = form.get("treatment_duration_other", "")
    a.patient_education = form.get("patient_education", "")
    a.education_details = form.get("education_details", "")
    a.physiotherapist_name = form.get("physiotherapist_name", "")

    db.commit()
    return RedirectResponse(url=f"/patient/{a.patient_id}?assessment_updated=1", status_code=303)


@app.post("/assessment/{assessment_id}/delete")
async def delete_assessment(assessment_id: int, db: Session = Depends(get_db)):
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    patient_id = a.patient_id
    db.delete(a)
    db.commit()
    return RedirectResponse(url=f"/patient/{patient_id}?assessment_deleted=1", status_code=303)


# ── REASSESSMENT CRUD ────────────────────────────────────────────────────

@app.get("/assessment/{assessment_id}/reassessment/new", response_class=HTMLResponse)
async def add_reassessment_form(request: Request, assessment_id: int, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return templates.TemplateResponse("add_reassessment.html", {
        "request": request, "a": assessment, "patient": assessment.patient
    })


@app.post("/assessment/{assessment_id}/reassessment/new")
async def add_reassessment(request: Request, assessment_id: int, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    form = await request.form()

    reassessment = Reassessment(
        assessment_id=assessment_id,
        short_term_achieved=form.get("short_term_achieved", ""),
        short_term_explain=form.get("short_term_explain", ""),
        long_term_progress=form.get("long_term_progress", ""),
        long_term_explain=form.get("long_term_explain", ""),
        pain_current=int(form.get("pain_current")) if form.get("pain_current") else None,
        functionality=form.get("functionality", ""),
        functionality_details=form.get("functionality_details", ""),
        posture_gait=form.get("posture_gait", ""),
        rom_upper=form.get("rom_upper", ""),
        rom_lower=form.get("rom_lower", ""),
        strength_upper=form.get("strength_upper", ""),
        strength_lower=form.get("strength_lower", ""),
        neuro_status=form.get("neuro_status", ""),
        neuro_sensory=form.get("neuro_sensory", ""),
        neuro_reflexes=form.get("neuro_reflexes", ""),
        neuro_coordination=form.get("neuro_coordination", ""),
        pain_location=form.get("pain_location", ""),
        pain_intensity=int(form.get("pain_intensity")) if form.get("pain_intensity") else None,
        other_findings=form.get("other_findings", ""),
        continue_plan=form.get("continue_plan", ""),
        modify_treatment=form.get("modify_treatment", ""),
        frequency_changes=form.get("frequency_changes", ""),
        modality_changes=form.get("modality_changes", ""),
        education_revisited=form.get("education_revisited", ""),
        next_visit=form.get("next_visit", ""),
        additional_assessments=form.get("additional_assessments", ""),
        physiotherapist_name=form.get("physiotherapist_name", ""),
    )
    db.add(reassessment)
    db.commit()
    return RedirectResponse(
        url=f"/patient/{assessment.patient_id}?reassessment_added=1", status_code=303
    )


@app.get("/reassessment/{reassessment_id}", response_class=HTMLResponse)
async def view_reassessment(request: Request, reassessment_id: int, db: Session = Depends(get_db)):
    r = db.query(Reassessment).filter(Reassessment.id == reassessment_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reassessment not found")
    return templates.TemplateResponse("view_reassessment.html", {
        "request": request, "r": r, "a": r.assessment, "patient": r.assessment.patient
    })


@app.post("/reassessment/{reassessment_id}/delete")
async def delete_reassessment(reassessment_id: int, db: Session = Depends(get_db)):
    r = db.query(Reassessment).filter(Reassessment.id == reassessment_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reassessment not found")
    patient_id = r.assessment.patient_id
    db.delete(r)
    db.commit()
    return RedirectResponse(url=f"/patient/{patient_id}?reassessment_deleted=1", status_code=303)


# ── WHATSAPP SHARING ─────────────────────────────────────────────────────

@app.get("/assessment/{assessment_id}/whatsapp")
async def whatsapp_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """Redirect to WhatsApp with a pre-filled assessment report."""
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    patient = a.patient
    report = generate_assessment_report(patient, a)
    phone = f"91{patient.phone}"  # Indian country code
    wa_url = f"https://wa.me/{phone}?text={urllib.parse.quote(report)}"
    return RedirectResponse(url=wa_url, status_code=303)

@app.get("/reassessment/{reassessment_id}/whatsapp")
async def whatsapp_reassessment(reassessment_id: int, db: Session = Depends(get_db)):
    """Redirect to WhatsApp with a pre-filled reassessment report."""
    r = db.query(Reassessment).filter(Reassessment.id == reassessment_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reassessment not found")
    patient = r.assessment.patient
    report = generate_reassessment_report(patient, r.assessment, r)
    phone = f"91{patient.phone}"  # Indian country code
    wa_url = f"https://wa.me/{phone}?text={urllib.parse.quote(report)}"
    return RedirectResponse(url=wa_url, status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000)
