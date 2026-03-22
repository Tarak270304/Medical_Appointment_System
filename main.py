from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
import math

app = FastAPI(
    title="MediCare Clinic API",
    description="Medical Appointment System — FastAPI Internship Final Project",
    version="1.0.0"
)

# ===========================================================================
# DATA — Doctors list & Appointments store
# ===========================================================================

doctors = [
    {"id": 1, "name": "Dr. Aisha Sharma",   "specialization": "Cardiologist",    "fee": 800,  "experience_years": 12, "is_available": True},
    {"id": 2, "name": "Dr. Rohan Mehta",    "specialization": "Dermatologist",   "fee": 500,  "experience_years": 7,  "is_available": True},
    {"id": 3, "name": "Dr. Priya Nair",     "specialization": "Pediatrician",    "fee": 400,  "experience_years": 9,  "is_available": False},
    {"id": 4, "name": "Dr. Suresh Patel",   "specialization": "General",         "fee": 300,  "experience_years": 15, "is_available": True},
    {"id": 5, "name": "Dr. Kavya Reddy",    "specialization": "Dermatologist",   "fee": 600,  "experience_years": 5,  "is_available": True},
    {"id": 6, "name": "Dr. Arjun Bose",     "specialization": "Cardiologist",    "fee": 900,  "experience_years": 20, "is_available": True},
]

doctor_counter = 7          # next doctor id

appointments = []
appt_counter = 1            # next appointment id

# ===========================================================================
# PYDANTIC MODELS
# ===========================================================================

class AppointmentRequest(BaseModel):
    patient_name:     str  = Field(..., min_length=2,  description="Patient full name")
    doctor_id:        int  = Field(..., gt=0,           description="Valid doctor ID")
    date:             str  = Field(..., min_length=8,   description="Appointment date e.g. 2026-04-01")
    reason:           str  = Field(..., min_length=5,   description="Reason for visit")
    appointment_type: str  = Field(default="in-person", description="in-person | video | emergency")
    senior_citizen:   bool = Field(default=False,       description="Senior citizen discount (15% off)")


class NewDoctor(BaseModel):
    name:             str  = Field(..., min_length=2, description="Doctor full name")
    specialization:   str  = Field(..., min_length=2, description="e.g. Cardiologist")
    fee:              int  = Field(..., gt=0,          description="Consultation fee in INR")
    experience_years: int  = Field(..., gt=0,          description="Years of experience")
    is_available:     bool = Field(default=True,       description="Available for appointments")


# ===========================================================================
# HELPER FUNCTIONS  (Day 3 — plain Python, no @app decorator)
# ===========================================================================

def find_doctor(doctor_id: int):
    """Return doctor dict or None."""
    for doc in doctors:
        if doc["id"] == doctor_id:
            return doc
    return None


def calculate_fee(base_fee: int, appointment_type: str, senior_citizen: bool = False) -> dict:
    """
    Fee rules:
      video      → 80 % of base fee
      in-person  → 100 % of base fee
      emergency  → 150 % of base fee
    Senior citizen gets an extra 15 % discount after the above.
    Returns dict with original_fee and final_fee.
    """
    appointment_type = appointment_type.lower()
    if appointment_type == "video":
        calculated = base_fee * 0.80
    elif appointment_type == "emergency":
        calculated = base_fee * 1.50
    else:                               # in-person (default)
        calculated = float(base_fee)

    original_fee = round(calculated, 2)

    if senior_citizen:
        final_fee = round(calculated * 0.85, 2)
    else:
        final_fee = original_fee

    return {"original_fee": original_fee, "final_fee": final_fee}


def filter_doctors_logic(
    specialization: Optional[str],
    max_fee: Optional[int],
    min_experience: Optional[int],
    is_available: Optional[bool]
) -> list:
    """Filter doctors list based on optional parameters."""
    result = doctors[:]

    if specialization is not None:
        result = [d for d in result if d["specialization"].lower() == specialization.lower()]

    if max_fee is not None:
        result = [d for d in result if d["fee"] <= max_fee]

    if min_experience is not None:
        result = [d for d in result if d["experience_years"] >= min_experience]

    if is_available is not None:
        result = [d for d in result if d["is_available"] == is_available]

    return result


# ===========================================================================
# Q1 — Home Route                                               (Day 1 — GET)
# ===========================================================================

@app.get("/", tags=["General"])
def home():
    """Q1 — Welcome message."""
    return {"message": "Welcome to MediCare Clinic"}


# ===========================================================================
# Q2 — GET all doctors                                          (Day 1 — GET)
# ===========================================================================

@app.get("/doctors", tags=["Doctors"])
def get_all_doctors():
    """Q2 — Return all doctors with total and available count."""
    available_count = sum(1 for d in doctors if d["is_available"])
    return {
        "total": len(doctors),
        "available_count": available_count,
        "doctors": doctors
    }


# ===========================================================================
# FIXED ROUTES — must appear before /doctors/{doctor_id}
# ===========================================================================

# Q5 — Summary                                                  (Day 1 — GET)
@app.get("/doctors/summary", tags=["Doctors"])
def doctors_summary():
    """Q5 — Return summary stats about doctors."""
    available_count = sum(1 for d in doctors if d["is_available"])

    most_experienced = max(doctors, key=lambda d: d["experience_years"])
    cheapest_fee     = min(doctors, key=lambda d: d["fee"])["fee"]

    specialization_count: dict = {}
    for d in doctors:
        spec = d["specialization"]
        specialization_count[spec] = specialization_count.get(spec, 0) + 1

    return {
        "total_doctors":         len(doctors),
        "available_count":       available_count,
        "most_experienced_doctor": most_experienced["name"],
        "cheapest_consultation_fee": cheapest_fee,
        "doctors_per_specialization": specialization_count
    }


# Q10 — Filter doctors                                  (Day 3 — Query Filter)
@app.get("/doctors/filter", tags=["Doctors"])
def filter_doctors(
    specialization: Optional[str]  = Query(default=None),
    max_fee:        Optional[int]  = Query(default=None),
    min_experience: Optional[int]  = Query(default=None),
    is_available:   Optional[bool] = Query(default=None)
):
    """Q10 — Filter doctors by specialization, fee, experience, availability."""
    result = filter_doctors_logic(specialization, max_fee, min_experience, is_available)
    return {"total": len(result), "doctors": result}


# Q16 — Search doctors                                      (Day 6 — Search)
@app.get("/doctors/search", tags=["Doctors"])
def search_doctors(keyword: str = Query(..., description="Search in name or specialization")):
    """Q16 — Case-insensitive search across name and specialization."""
    kw = keyword.lower()
    results = [
        d for d in doctors
        if kw in d["name"].lower() or kw in d["specialization"].lower()
    ]
    if not results:
        return {
            "total_found": 0,
            "message": f"No doctors found matching '{keyword}'. Try a different keyword.",
            "doctors": []
        }
    return {"total_found": len(results), "keyword": keyword, "doctors": results}


# Q17 — Sort doctors                                         (Day 6 — Sort)
@app.get("/doctors/sort", tags=["Doctors"])
def sort_doctors(
    sort_by: str = Query(default="fee",  description="fee | name | experience_years"),
    order:   str = Query(default="asc",  description="asc | desc")
):
    """Q17 — Sort doctors by fee, name, or experience_years."""
    valid_sort_fields = ["fee", "name", "experience_years"]
    valid_orders      = ["asc", "desc"]

    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {valid_sort_fields}")
    if order not in valid_orders:
        raise HTTPException(status_code=400, detail=f"order must be one of {valid_orders}")

    reverse = (order == "desc")
    sorted_doctors = sorted(doctors, key=lambda d: d[sort_by], reverse=reverse)

    return {
        "sort_by": sort_by,
        "order":   order,
        "total":   len(sorted_doctors),
        "doctors": sorted_doctors
    }


# Q18 — Paginate doctors                                    (Day 6 — Pagination)
@app.get("/doctors/page", tags=["Doctors"])
def paginate_doctors(
    page:  int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=3, ge=1, description="Items per page")
):
    """Q18 — Paginate the doctors list."""
    total       = len(doctors)
    total_pages = math.ceil(total / limit)
    start       = (page - 1) * limit
    end         = start + limit
    page_data   = doctors[start:end]

    return {
        "page":        page,
        "limit":       limit,
        "total":       total,
        "total_pages": total_pages,
        "doctors":     page_data
    }


# Q20 — Browse (search + sort + paginate)     (Day 6 — Combined / Day 3 Filter)
@app.get("/doctors/browse", tags=["Doctors"])
def browse_doctors(
    keyword: Optional[str] = Query(default=None, description="Search in name or specialization"),
    sort_by: str           = Query(default="fee",  description="fee | name | experience_years"),
    order:   str           = Query(default="asc",  description="asc | desc"),
    page:    int           = Query(default=1, ge=1),
    limit:   int           = Query(default=4, ge=1)
):
    """Q20 — Combined: optional search → sort → paginate."""
    valid_sort_fields = ["fee", "name", "experience_years"]
    valid_orders      = ["asc", "desc"]

    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {valid_sort_fields}")
    if order not in valid_orders:
        raise HTTPException(status_code=400, detail=f"order must be one of {valid_orders}")

    # Step 1 — Filter
    if keyword:
        kw = keyword.lower()
        filtered = [d for d in doctors if kw in d["name"].lower() or kw in d["specialization"].lower()]
    else:
        filtered = doctors[:]

    # Step 2 — Sort
    reverse = (order == "desc")
    sorted_result = sorted(filtered, key=lambda d: d[sort_by], reverse=reverse)

    # Step 3 — Paginate
    total       = len(sorted_result)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start       = (page - 1) * limit
    page_data   = sorted_result[start:start + limit]

    return {
        "keyword":     keyword,
        "sort_by":     sort_by,
        "order":       order,
        "page":        page,
        "limit":       limit,
        "total":       total,
        "total_pages": total_pages,
        "doctors":     page_data
    }


# ===========================================================================
# Q3 — GET doctor by ID                                         (Day 1 — GET)
# ===========================================================================

@app.get("/doctors/{doctor_id}", tags=["Doctors"])
def get_doctor(doctor_id: int):
    """Q3 — Return a single doctor or 404."""
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail=f"Doctor with id {doctor_id} not found")
    return doctor


# ===========================================================================
# Q11 — POST /doctors (Add new doctor)                          (Day 4 — CRUD)
# ===========================================================================

@app.post("/doctors", status_code=201, tags=["Doctors"])
def add_doctor(new_doc: NewDoctor):
    """Q11 — Add a new doctor. Reject duplicate names."""
    global doctor_counter

    for d in doctors:
        if d["name"].lower() == new_doc.name.lower():
            raise HTTPException(status_code=400, detail=f"Doctor '{new_doc.name}' already exists")

    doctor = {
        "id":               doctor_counter,
        "name":             new_doc.name,
        "specialization":   new_doc.specialization,
        "fee":              new_doc.fee,
        "experience_years": new_doc.experience_years,
        "is_available":     new_doc.is_available
    }
    doctors.append(doctor)
    doctor_counter += 1

    return {"message": "Doctor added successfully", "doctor": doctor}


# ===========================================================================
# Q12 — PUT /doctors/{doctor_id}                                (Day 4 — CRUD)
# ===========================================================================

@app.put("/doctors/{doctor_id}", tags=["Doctors"])
def update_doctor(
    doctor_id:    int,
    fee:          Optional[int]  = Query(default=None, description="Update consultation fee"),
    is_available: Optional[bool] = Query(default=None, description="Update availability")
):
    """Q12 — Update doctor's fee and/or availability."""
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail=f"Doctor with id {doctor_id} not found")

    if fee is not None:
        doctor["fee"] = fee
    if is_available is not None:
        doctor["is_available"] = is_available

    return {"message": "Doctor updated successfully", "doctor": doctor}


# ===========================================================================
# Q13 — DELETE /doctors/{doctor_id}                             (Day 4 — CRUD)
# ===========================================================================

@app.delete("/doctors/{doctor_id}", tags=["Doctors"])
def delete_doctor(doctor_id: int):
    """Q13 — Delete doctor. Block if they have active scheduled appointments."""
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail=f"Doctor with id {doctor_id} not found")

    active = [
        a for a in appointments
        if a["doctor_id"] == doctor_id and a["status"] == "scheduled"
    ]
    if active:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete Dr. {doctor['name']} — they have {len(active)} active scheduled appointment(s)"
        )

    doctors.remove(doctor)
    return {"message": f"Doctor '{doctor['name']}' deleted successfully"}


# ===========================================================================
# Q4 — GET /appointments                                        (Day 1 — GET)
# ===========================================================================

@app.get("/appointments", tags=["Appointments"])
def get_all_appointments():
    """Q4 — Return all appointments with total count."""
    return {"total": len(appointments), "appointments": appointments}


# ===========================================================================
# FIXED APPOINTMENT ROUTES — above /appointments/{appointment_id}
# ===========================================================================

# Q15 part-a — Active appointments
@app.get("/appointments/active", tags=["Appointments"])
def get_active_appointments():
    """Q15 — Return appointments with status 'scheduled' or 'confirmed'."""
    active = [a for a in appointments if a["status"] in ("scheduled", "confirmed")]
    return {"total": len(active), "appointments": active}


# Q19 — Search appointments
@app.get("/appointments/search", tags=["Appointments"])
def search_appointments(patient_name: str = Query(..., description="Search by patient name")):
    """Q19 — Case-insensitive search by patient_name."""
    kw      = patient_name.lower()
    results = [a for a in appointments if kw in a["patient_name"].lower()]
    if not results:
        return {
            "total_found": 0,
            "message":     f"No appointments found for patient '{patient_name}'.",
            "appointments": []
        }
    return {"total_found": len(results), "appointments": results}


# Q19 — Sort appointments
@app.get("/appointments/sort", tags=["Appointments"])
def sort_appointments(
    sort_by: str = Query(default="fee",  description="fee | date"),
    order:   str = Query(default="asc",  description="asc | desc")
):
    """Q19 — Sort appointments by fee or date."""
    valid_sort_fields = ["fee", "date"]
    valid_orders      = ["asc", "desc"]

    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {valid_sort_fields}")
    if order not in valid_orders:
        raise HTTPException(status_code=400, detail=f"order must be one of {valid_orders}")

    reverse = (order == "desc")
    sorted_appts = sorted(appointments, key=lambda a: a[sort_by], reverse=reverse)

    return {
        "sort_by": sort_by,
        "order":   order,
        "total":   len(sorted_appts),
        "appointments": sorted_appts
    }


# Q19 — Paginate appointments
@app.get("/appointments/page", tags=["Appointments"])
def paginate_appointments(
    page:  int = Query(default=1, ge=1),
    limit: int = Query(default=3, ge=1)
):
    """Q19 — Paginate appointments list."""
    total       = len(appointments)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start       = (page - 1) * limit
    page_data   = appointments[start:start + limit]

    return {
        "page":        page,
        "limit":       limit,
        "total":       total,
        "total_pages": total_pages,
        "appointments": page_data
    }


# Q15 part-b — Appointments by doctor
@app.get("/appointments/by-doctor/{doctor_id}", tags=["Appointments"])
def get_appointments_by_doctor(doctor_id: int):
    """Q15 — All appointments for a specific doctor."""
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail=f"Doctor with id {doctor_id} not found")

    doc_appts = [a for a in appointments if a["doctor_id"] == doctor_id]
    return {
        "doctor": doctor["name"],
        "total":  len(doc_appts),
        "appointments": doc_appts
    }


# ===========================================================================
# Q8 & Q9 — POST /appointments                     (Day 2 — POST / Day 3 Helpers)
# ===========================================================================

@app.post("/appointments", status_code=201, tags=["Appointments"])
def book_appointment(request: AppointmentRequest):
    """Q8 & Q9 — Book appointment using helper functions with senior citizen discount."""
    global appt_counter

    doctor = find_doctor(request.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail=f"Doctor with id {request.doctor_id} not found")

    if not doctor["is_available"]:
        raise HTTPException(
            status_code=400,
            detail=f"Dr. {doctor['name']} is currently not available for appointments"
        )

    fee_info = calculate_fee(doctor["fee"], request.appointment_type, request.senior_citizen)

    appointment = {
        "appointment_id":   appt_counter,
        "patient_name":     request.patient_name,
        "doctor_id":        doctor["id"],
        "doctor_name":      doctor["name"],
        "specialization":   doctor["specialization"],
        "date":             request.date,
        "reason":           request.reason,
        "appointment_type": request.appointment_type,
        "senior_citizen":   request.senior_citizen,
        "original_fee":     fee_info["original_fee"],
        "fee":              fee_info["final_fee"],
        "status":           "scheduled"
    }
    appointments.append(appointment)
    appt_counter += 1

    # Mark doctor unavailable after booking
    doctor["is_available"] = False

    return {
        "message":     "Appointment booked successfully",
        "appointment": appointment
    }


# ===========================================================================
# Q14 — Confirm / Cancel                                   (Day 5 — Workflow)
# Q15 — Complete                                           (Day 5 — Workflow)
# ===========================================================================

@app.post("/appointments/{appointment_id}/confirm", tags=["Appointments"])
def confirm_appointment(appointment_id: int):
    """Q14 — Confirm a scheduled appointment."""
    appt = next((a for a in appointments if a["appointment_id"] == appointment_id), None)
    if not appt:
        raise HTTPException(status_code=404, detail=f"Appointment {appointment_id} not found")
    if appt["status"] != "scheduled":
        raise HTTPException(
            status_code=400,
            detail=f"Only 'scheduled' appointments can be confirmed. Current status: '{appt['status']}'"
        )

    appt["status"] = "confirmed"
    return {"message": "Appointment confirmed successfully", "appointment": appt}


@app.post("/appointments/{appointment_id}/cancel", tags=["Appointments"])
def cancel_appointment(appointment_id: int):
    """Q14 — Cancel an appointment and free up the doctor."""
    appt = next((a for a in appointments if a["appointment_id"] == appointment_id), None)
    if not appt:
        raise HTTPException(status_code=404, detail=f"Appointment {appointment_id} not found")
    if appt["status"] == "cancelled":
        raise HTTPException(status_code=400, detail="Appointment is already cancelled")

    appt["status"] = "cancelled"

    # Free the doctor
    doctor = find_doctor(appt["doctor_id"])
    if doctor:
        doctor["is_available"] = True

    return {"message": "Appointment cancelled. Doctor is now available.", "appointment": appt}


@app.post("/appointments/{appointment_id}/complete", tags=["Appointments"])
def complete_appointment(appointment_id: int):
    """Q15 — Mark an appointment as completed."""
    appt = next((a for a in appointments if a["appointment_id"] == appointment_id), None)
    if not appt:
        raise HTTPException(status_code=404, detail=f"Appointment {appointment_id} not found")
    if appt["status"] not in ("scheduled", "confirmed"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot complete appointment with status '{appt['status']}'"
        )

    appt["status"] = "completed"

    # Free the doctor after completion
    doctor = find_doctor(appt["doctor_id"])
    if doctor:
        doctor["is_available"] = True

    return {"message": "Appointment marked as completed", "appointment": appt}
