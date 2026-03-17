from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False, unique=True, index=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    doctor_assessment = Column(Text, nullable=True)  # Private — not sent to patient via WhatsApp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship: one patient can have many assessments
    assessments = relationship("Assessment", back_populates="patient", cascade="all, delete-orphan")


class Assessment(Base):
    """Full physiotherapy assessment form."""
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    assessment_date = Column(DateTime, default=datetime.utcnow)

    # --- Referral Information ---
    referring_doctor = Column(String(100), nullable=True)
    history = Column(Text, nullable=True)
    referral_reasons = Column(Text, nullable=True)      # comma-separated: pain,loss_of_function,...
    referral_other = Column(Text, nullable=True)

    # --- Chief Complaint ---
    chief_complaint = Column(Text, nullable=True)

    # --- Pain Assessment ---
    pain_location = Column(Text, nullable=True)
    pain_intensity = Column(Integer, nullable=True)       # 0-10
    pain_quality = Column(String(100), nullable=True)     # sharp, dull, throbbing
    pain_aggravating = Column(Text, nullable=True)
    pain_relieving = Column(Text, nullable=True)
    pain_duration = Column(Text, nullable=True)
    previous_treatments = Column(Text, nullable=True)

    # --- Medical History ---
    medical_conditions = Column(Text, nullable=True)      # comma-separated checkboxes
    previous_surgeries = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    other_medical_history = Column(Text, nullable=True)

    # --- Functional Status ---
    mobility = Column(String(30), nullable=True)          # independent / with_assistance / dependent
    adls = Column(String(30), nullable=True)              # independent / some_assistance / dependent
    work_leisure = Column(String(30), nullable=True)      # sedentary / active / highly_active
    physical_activity = Column(String(30), nullable=True) # low / moderate / high

    # --- Physical Examination ---
    posture_gait = Column(String(20), nullable=True)      # normal / abnormal
    posture_gait_details = Column(Text, nullable=True)

    # Range of Motion
    rom_cervical = Column(String(50), nullable=True)
    rom_lumbar = Column(String(50), nullable=True)
    rom_shoulder = Column(String(50), nullable=True)
    rom_hip = Column(String(50), nullable=True)
    rom_knee = Column(String(50), nullable=True)
    rom_ankle = Column(String(50), nullable=True)

    # Muscle Strength (0-5)
    strength_upper = Column(String(50), nullable=True)
    strength_lower = Column(String(50), nullable=True)

    # Neurological Assessment
    neuro_sensory = Column(String(20), nullable=True)     # normal / abnormal
    neuro_sensory_details = Column(Text, nullable=True)
    neuro_reflexes = Column(String(20), nullable=True)
    neuro_reflexes_details = Column(Text, nullable=True)
    neuro_coordination = Column(String(20), nullable=True)
    neuro_coordination_details = Column(Text, nullable=True)

    # Respiratory
    respiratory = Column(String(20), nullable=True)       # normal / abnormal
    respiratory_details = Column(Text, nullable=True)

    # Swelling
    swelling = Column(String(20), nullable=True)          # present / not_present
    swelling_location = Column(Text, nullable=True)

    # Special Tests
    special_tests = Column(Text, nullable=True)

    # --- Assessment Summary ---
    diagnosis = Column(Text, nullable=True)
    problem_list = Column(Text, nullable=True)
    impairments = Column(Text, nullable=True)
    goals_short_term = Column(Text, nullable=True)
    goals_long_term = Column(Text, nullable=True)

    # --- Treatment Plan ---
    treatment_modalities = Column(Text, nullable=True)    # comma-separated checkboxes
    treatment_other = Column(Text, nullable=True)
    session_frequency = Column(String(50), nullable=True)
    session_frequency_other = Column(String(50), nullable=True)
    treatment_duration = Column(String(50), nullable=True)
    treatment_duration_other = Column(String(50), nullable=True)
    patient_education = Column(String(10), nullable=True) # yes / no
    education_details = Column(Text, nullable=True)

    # --- Physiotherapist ---
    physiotherapist_name = Column(String(100), nullable=True)

    # --- Doctor Assessment (PRIVATE — not sent to patient via WhatsApp) ---
    doctor_assessment = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="assessments")
    reassessments = relationship("Reassessment", back_populates="assessment", cascade="all, delete-orphan")


class Reassessment(Base):
    """Follow-up reassessment linked to an initial assessment."""
    __tablename__ = "reassessments"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    reassessment_date = Column(DateTime, default=datetime.utcnow)

    # --- Progress Towards Goals ---
    short_term_achieved = Column(String(10), nullable=True)   # yes / no
    short_term_explain = Column(Text, nullable=True)
    long_term_progress = Column(String(10), nullable=True)    # yes / no
    long_term_explain = Column(Text, nullable=True)

    # --- Patient Feedback ---
    pain_current = Column(Integer, nullable=True)              # 0-10
    functionality = Column(String(20), nullable=True)          # improved / no_change / worsened
    functionality_details = Column(Text, nullable=True)

    # --- Re-evaluated Physical Exam ---
    posture_gait = Column(String(20), nullable=True)
    rom_upper = Column(String(50), nullable=True)
    rom_lower = Column(String(50), nullable=True)
    strength_upper = Column(String(50), nullable=True)
    strength_lower = Column(String(50), nullable=True)
    neuro_status = Column(String(20), nullable=True)           # improved / no_change / worsened
    neuro_sensory = Column(Text, nullable=True)
    neuro_reflexes = Column(Text, nullable=True)
    neuro_coordination = Column(Text, nullable=True)
    pain_location = Column(Text, nullable=True)
    pain_intensity = Column(Integer, nullable=True)
    other_findings = Column(Text, nullable=True)

    # --- Revised Treatment Plan ---
    continue_plan = Column(String(10), nullable=True)          # yes / no
    modify_treatment = Column(String(10), nullable=True)       # yes / no
    frequency_changes = Column(Text, nullable=True)
    modality_changes = Column(Text, nullable=True)
    education_revisited = Column(String(10), nullable=True)    # yes / no

    # --- Next Follow-up ---
    next_visit = Column(Text, nullable=True)
    additional_assessments = Column(Text, nullable=True)

    # --- Physiotherapist ---
    physiotherapist_name = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    assessment = relationship("Assessment", back_populates="reassessments")
