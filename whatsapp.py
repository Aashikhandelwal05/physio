"""
WhatsApp report text generators for assessments and reassessments.
Uses WhatsApp-friendly formatting (*bold*, _italic_).
"""


def _section(title: str, lines: list[tuple[str, str]]) -> str:
    """Build a section block. Skips empty values."""
    filtered = [(label, val) for label, val in lines if val]
    if not filtered:
        return ""
    rows = "\n".join(f"  • {label}: {val}" for label, val in filtered)
    return f"\n*{title}*\n{rows}\n"


def _fmt_csv(csv_str: str) -> str:
    """Convert comma-separated DB values to readable text."""
    if not csv_str:
        return ""
    items = [v.strip().replace("_", " ").title() for v in csv_str.split(",") if v.strip()]
    return ", ".join(items)


def _fmt_radio(value: str) -> str:
    """Format radio/enum values for display."""
    if not value:
        return ""
    return value.replace("_", " ").title()


def generate_assessment_report(patient, assessment) -> str:
    """Generate a clean WhatsApp-formatted assessment report."""
    a = assessment
    date_str = a.assessment_date.strftime("%d %b %Y, %I:%M %p")

    header = (
        f"📋 *PHYSIOTHERAPY ASSESSMENT REPORT*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*Patient:* {patient.name}\n"
    )
    if patient.age:
        header += f"*Age:* {patient.age}\n"
    if patient.gender:
        header += f"*Gender:* {patient.gender}\n"
    header += f"*Date:* {date_str}\n"

    parts = [header]

    # ① Referral
    parts.append(_section("① Referral Information", [
        ("Referring Doctor", a.referring_doctor),
        ("History", a.history),
        ("Referral Reasons", _fmt_csv(a.referral_reasons)),
        ("Other Reason", a.referral_other),
        ("Chief Complaint", a.chief_complaint),
    ]))

    # ② Pain
    pain_intensity = f"{a.pain_intensity}/10" if a.pain_intensity is not None else ""
    parts.append(_section("② Pain Assessment", [
        ("Location", a.pain_location),
        ("Intensity", pain_intensity),
        ("Quality", a.pain_quality),
        ("Aggravating Factors", a.pain_aggravating),
        ("Relieving Factors", a.pain_relieving),
        ("Duration & Frequency", a.pain_duration),
        ("Previous Treatments", a.previous_treatments),
    ]))

    # ③ Medical History
    parts.append(_section("③ Medical History", [
        ("Conditions", _fmt_csv(a.medical_conditions)),
        ("Previous Surgeries", a.previous_surgeries),
        ("Medications", a.medications),
        ("Other", a.other_medical_history),
    ]))

    # ④ Functional Status
    parts.append(_section("④ Functional Status", [
        ("Mobility", _fmt_radio(a.mobility)),
        ("ADLs", _fmt_radio(a.adls)),
        ("Work/Leisure", _fmt_radio(a.work_leisure)),
        ("Physical Activity", _fmt_radio(a.physical_activity)),
    ]))

    # ⑤ Physical Examination
    exam_lines = [
        ("Posture & Gait", _fmt_radio(a.posture_gait)),
        ("Posture Details", a.posture_gait_details),
    ]
    # ROM
    for joint, val in [("Cervical", a.rom_cervical), ("Lumbar", a.rom_lumbar),
                       ("Shoulder", a.rom_shoulder), ("Hip", a.rom_hip),
                       ("Knee", a.rom_knee), ("Ankle", a.rom_ankle)]:
        if val:
            exam_lines.append((f"ROM {joint}", val))
    exam_lines += [
        ("Strength Upper Limb", a.strength_upper),
        ("Strength Lower Limb", a.strength_lower),
        ("Sensory", _fmt_radio(a.neuro_sensory)),
        ("Sensory Details", a.neuro_sensory_details),
        ("Reflexes", _fmt_radio(a.neuro_reflexes)),
        ("Reflexes Details", a.neuro_reflexes_details),
        ("Coordination", _fmt_radio(a.neuro_coordination)),
        ("Coordination Details", a.neuro_coordination_details),
        ("Respiratory", _fmt_radio(a.respiratory)),
        ("Respiratory Details", a.respiratory_details),
        ("Swelling", _fmt_radio(a.swelling)),
        ("Swelling Location", a.swelling_location),
        ("Special Tests", a.special_tests),
    ]
    parts.append(_section("⑤ Physical Examination", exam_lines))

    # ⑥ Assessment Summary
    parts.append(_section("⑥ Assessment Summary & Goals", [
        ("Diagnosis", a.diagnosis),
        ("Problem List", a.problem_list),
        ("Impairments", a.impairments),
        ("Short-term Goals", a.goals_short_term),
        ("Long-term Goals", a.goals_long_term),
    ]))

    # ⑦ Treatment Plan
    parts.append(_section("⑦ Treatment Plan", [
        ("Modalities", _fmt_csv(a.treatment_modalities)),
        ("Other Modality", a.treatment_other),
        ("Frequency", _fmt_radio(a.session_frequency)),
        ("Frequency Details", a.session_frequency_other),
        ("Duration", _fmt_radio(a.treatment_duration)),
        ("Duration Details", a.treatment_duration_other),
        ("Education Provided", _fmt_radio(a.patient_education)),
        ("Education Details", a.education_details),
    ]))

    if a.physiotherapist_name:
        parts.append(f"\n*Physiotherapist:* {a.physiotherapist_name}\n")

    parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n_Sent from Balaji Neurophysiotherapy Clinic_")

    return "".join(parts)


def generate_reassessment_report(patient, assessment, reassessment) -> str:
    """Generate a clean WhatsApp-formatted reassessment report."""
    r = reassessment
    date_str = r.reassessment_date.strftime("%d %b %Y, %I:%M %p")

    header = (
        f"🔄 *PHYSIOTHERAPY REASSESSMENT REPORT*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*Patient:* {patient.name}\n"
    )
    if patient.age:
        header += f"*Age:* {patient.age}\n"
    if patient.gender:
        header += f"*Gender:* {patient.gender}\n"
    header += (
        f"*Reassessment Date:* {date_str}\n"
        f"*Original Assessment:* {assessment.assessment_date.strftime('%d %b %Y')}\n"
    )
    if assessment.diagnosis:
        header += f"*Diagnosis:* {assessment.diagnosis}\n"

    parts = [header]

    # Progress
    parts.append(_section("Progress Towards Goals", [
        ("Short-term Achieved", _fmt_radio(r.short_term_achieved)),
        ("Details", r.short_term_explain),
        ("Long-term Progress", _fmt_radio(r.long_term_progress)),
        ("Details", r.long_term_explain),
    ]))

    # Feedback
    pain_current = f"{r.pain_current}/10" if r.pain_current is not None else ""
    parts.append(_section("Patient Feedback", [
        ("Current Pain", pain_current),
        ("Functionality", _fmt_radio(r.functionality)),
        ("Details", r.functionality_details),
    ]))

    # Physical Exam
    pain_intensity = f"{r.pain_intensity}/10" if r.pain_intensity is not None else ""
    parts.append(_section("Re-evaluated Physical Examination", [
        ("Posture / Gait", _fmt_radio(r.posture_gait)),
        ("ROM Upper Limb", r.rom_upper),
        ("ROM Lower Limb", r.rom_lower),
        ("Strength Upper Limb", r.strength_upper),
        ("Strength Lower Limb", r.strength_lower),
        ("Neurological Status", _fmt_radio(r.neuro_status)),
        ("Sensory", r.neuro_sensory),
        ("Reflexes", r.neuro_reflexes),
        ("Coordination", r.neuro_coordination),
        ("Pain Location", r.pain_location),
        ("Pain Intensity", pain_intensity),
        ("Other Findings", r.other_findings),
    ]))

    # Revised Plan
    parts.append(_section("Revised Treatment Plan", [
        ("Continue Current Plan", _fmt_radio(r.continue_plan)),
        ("Modify Treatment", _fmt_radio(r.modify_treatment)),
        ("Frequency Changes", r.frequency_changes),
        ("Modality Changes", r.modality_changes),
        ("Education Revisited", _fmt_radio(r.education_revisited)),
    ]))

    # Next Follow-up
    parts.append(_section("Next Follow-up", [
        ("Next Visit", r.next_visit),
        ("Additional Assessments", r.additional_assessments),
    ]))

    if r.physiotherapist_name:
        parts.append(f"\n*Physiotherapist:* {r.physiotherapist_name}\n")

    parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n_Sent from Balaji Neurophysiotherapy Clinic_")

    return "".join(parts)
