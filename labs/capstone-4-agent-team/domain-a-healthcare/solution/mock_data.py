"""
Mock data for Healthcare Pre-Authorization Multi-Agent Pipeline (Solution).
Identical to the starter mock_data.py — shared across starter and solution.
"""

# Re-export everything from the starter mock_data
# In a real project you'd share the file; here we duplicate for self-containment.

from __future__ import annotations

# ---------------------------------------------------------------------------
# Pre-Authorization Requests (16 records with edge cases)
# ---------------------------------------------------------------------------
PREAUTH_REQUESTS = {
    "PA-2024-001": {
        "request_id": "PA-2024-001",
        "patient_name": "Maria Gonzalez",
        "patient_dob": "1958-03-14",
        "patient_id": "PT-90001",
        "plan_id": "PLAN-PPO-GOLD",
        "provider_npi": "NPI-1234567890",
        "facility_id": "FAC-001",
        "cpt_code": "27447",
        "diagnosis_codes": ["M17.11"],
        "clinical_notes": (
            "68-year-old female with 2-year history of progressive right knee pain. "
            "Kellgren-Lawrence grade 3 on recent X-ray. WOMAC score 52. Failed 6 months "
            "of conservative management including PT (12 sessions), naproxen 500mg BID, "
            "and two corticosteroid injections. BMI 32.1."
        ),
        "urgency": "routine",
        "submitted_date": "2024-11-15",
    },
    "PA-2024-002": {
        "request_id": "PA-2024-002",
        "patient_name": "David Park",
        "patient_dob": "1985-11-22",
        "patient_id": "PT-90002",
        "plan_id": "PLAN-HMO-BASIC",
        "provider_npi": "NPI-9876543210",
        "facility_id": "FAC-005",
        "cpt_code": "27447",
        "diagnosis_codes": ["M17.11"],
        "clinical_notes": (
            "35-year-old male with right knee OA secondary to prior ACL reconstruction. "
            "Requesting TKA with out-of-network surgeon Dr. Morton at Summit Specialty Hospital. "
            "WOMAC score 44. KL grade 2. Only 6 weeks of PT attempted."
        ),
        "urgency": "routine",
        "submitted_date": "2024-11-16",
    },
    "PA-2024-003": {
        "request_id": "PA-2024-003",
        "patient_name": "Linda Chen",
        "patient_dob": "1972-07-09",
        "patient_id": "PT-90003",
        "plan_id": "PLAN-PPO-SILVER",
        "provider_npi": "NPI-1234567890",
        "facility_id": "FAC-001",
        "cpt_code": "99999",
        "diagnosis_codes": ["M17.12"],
        "clinical_notes": (
            "Patient requesting experimental regenerative cartilage implant for left knee OA. "
            "Enrolled in clinical trial NCT-0042889 at Valley Medical Center."
        ),
        "urgency": "routine",
        "submitted_date": "2024-11-17",
    },
    "PA-2024-004": {
        "request_id": "PA-2024-004",
        "patient_name": "Robert Williams",
        "patient_dob": "1960-01-30",
        "patient_id": "PT-90004",
        "plan_id": "PLAN-PPO-GOLD",
        "provider_npi": "NPI-5551234567",
        "facility_id": "FAC-002",
        "cpt_code": "43239",
        "diagnosis_codes": ["K21.0"],
        "clinical_notes": (
            "64-year-old male with persistent GERD symptoms despite 12 weeks of omeprazole "
            "40mg daily. New-onset dysphagia over past 4 weeks. 8lb weight loss. "
            "Requesting EGD with biopsy."
        ),
        "urgency": "urgent",
        "submitted_date": "2024-11-18",
    },
    "PA-2024-005": {
        "request_id": "PA-2024-005",
        "patient_name": "Sarah Thompson",
        "patient_dob": "1990-05-20",
        "patient_id": "PT-90005",
        "plan_id": "PLAN-PPO-GOLD",
        "provider_npi": "NPI-1112223334",
        "facility_id": "FAC-001",
        "cpt_code": "70553",
        "diagnosis_codes": ["G43.909"],
        "clinical_notes": (
            "34-year-old female with chronic migraines, well-controlled on sumatriptan. "
            "Routine follow-up MRI requested. No new neurological deficits. "
            "Last MRI 14 months ago was normal."
        ),
        "urgency": "routine",
        "submitted_date": "2024-11-19",
    },
    "PA-2024-006": {
        "request_id": "PA-2024-006",
        "patient_name": "James Rivera",
        "patient_dob": "1975-08-12",
        "patient_id": "PT-90006",
        "plan_id": "PLAN-PPO-SILVER",
        "provider_npi": "NPI-7778889990",
        "facility_id": "FAC-002",
        "cpt_code": "64483",
        "diagnosis_codes": ["M51.16"],
        "clinical_notes": (
            "49-year-old male with L4-L5 disc herniation with left-sided radiculopathy. "
            "Positive straight leg raise. Failed 8 weeks of PT and gabapentin. "
            "MRI confirms disc herniation. This is the second injection request in 12 months."
        ),
        "urgency": "routine",
        "submitted_date": "2024-11-20",
    },
    "PA-2024-007": {
        "request_id": "PA-2024-007",
        "patient_name": "Emily Watson",
        "patient_dob": "1945-12-03",
        "patient_id": "PT-90007",
        "plan_id": "PLAN-HMO-BASIC",
        "provider_npi": "NPI-1234567890",
        "facility_id": "FAC-001",
        "cpt_code": "27447",
        "diagnosis_codes": ["M17.0"],
        "clinical_notes": (
            "79-year-old female with bilateral severe knee OA. KL grade 4 bilateral. "
            "WOMAC 68. BMI 41.2 — enrolled in hospital weight management programme. "
            "Failed 9 months conservative treatment including PT, NSAIDs, 3 steroid injections."
        ),
        "urgency": "routine",
        "submitted_date": "2024-11-21",
    },
    "PA-2024-008": {
        "request_id": "PA-2024-008",
        "patient_name": "Michael Brown",
        "patient_dob": "1988-04-15",
        "patient_id": "PT-90008",
        "plan_id": "PLAN-PPO-GOLD",
        "provider_npi": "NPI-1234567890",
        "facility_id": "FAC-003",
        "cpt_code": "29881",
        "diagnosis_codes": ["S83.21"],
        "clinical_notes": (
            "36-year-old male. Acute bucket-handle tear of medial meniscus from basketball "
            "injury 5 days ago. Locked knee, unable to fully extend. MRI confirms tear. "
            "Requesting urgent arthroscopic meniscectomy."
        ),
        "urgency": "urgent",
        "submitted_date": "2024-11-22",
    },
    "PA-2024-009": {
        "request_id": "PA-2024-009",
        "patient_name": "Nancy Liu",
        "patient_dob": "1970-09-25",
        "patient_id": "PT-90009",
        "plan_id": "PLAN-PPO-GOLD",
        "provider_npi": "NPI-5551234567",
        "facility_id": "FAC-001",
        "cpt_code": "INVALID",
        "diagnosis_codes": ["K21.0"],
        "clinical_notes": "Requesting procedure with invalid CPT code.",
        "urgency": "routine",
        "submitted_date": "2024-11-23",
    },
    "PA-2024-010": {
        "request_id": "PA-2024-010",
        "patient_name": "Thomas Garcia",
        "patient_dob": "1965-06-18",
        "patient_id": "PT-90010",
        "plan_id": "PLAN-PPO-SILVER",
        "provider_npi": "NPI-1234567890",
        "facility_id": "FAC-001",
        "cpt_code": "27447",
        "diagnosis_codes": [],
        "clinical_notes": "Request submitted without diagnosis codes.",
        "urgency": "routine",
        "submitted_date": "2024-11-24",
    },
    "PA-2024-011": {
        "request_id": "PA-2024-011",
        "patient_name": "Jennifer Adams",
        "patient_dob": "1982-02-14",
        "patient_id": "PT-90011",
        "plan_id": "PLAN-PPO-GOLD",
        "provider_npi": "NPI-1234567890",
        "facility_id": "FAC-001",
        "cpt_code": "27447",
        "diagnosis_codes": ["Z96.651"],
        "clinical_notes": (
            "Patient has presence of right artificial knee joint. Requesting TKA revision. "
            "Diagnosis code Z96.651 does not match standard TKA criteria."
        ),
        "urgency": "routine",
        "submitted_date": "2024-11-25",
    },
    "PA-2024-012": {
        "request_id": "PA-2024-012",
        "patient_name": "Richard Kim",
        "patient_dob": "1955-10-08",
        "patient_id": "PT-90012",
        "plan_id": "PLAN-PPO-GOLD",
        "provider_npi": "NPI-1234567890",
        "facility_id": "FAC-001",
        "cpt_code": "27447",
        "diagnosis_codes": ["M17.9"],
        "clinical_notes": (
            "69-year-old male. KL grade 3. WOMAC score 38 — just below threshold of 39. "
            "6 months conservative treatment. PT x 10 sessions, NSAIDs, 1 injection."
        ),
        "urgency": "routine",
        "submitted_date": "2024-11-26",
    },
    "PA-2024-013": {
        "request_id": "PA-2024-013",
        "patient_name": "Patricia Nguyen",
        "patient_dob": "1978-03-30",
        "patient_id": "PT-90013",
        "plan_id": "PLAN-PPO-GOLD",
        "provider_npi": "NPI-0000000000",
        "facility_id": "FAC-001",
        "cpt_code": "27447",
        "diagnosis_codes": ["M17.11"],
        "clinical_notes": "Submitted with unknown provider NPI.",
        "urgency": "routine",
        "submitted_date": "2024-11-27",
    },
    "PA-2024-014": {
        "request_id": "PA-2024-014",
        "patient_name": "George Martinez",
        "patient_dob": "1962-07-22",
        "patient_id": "PT-90014",
        "plan_id": "PLAN-PPO-GOLD",
        "provider_npi": "NPI-1234567890",
        "facility_id": "FAC-001",
        "cpt_code": "27447",
        "diagnosis_codes": ["M17.11"],
        "clinical_notes": (
            "62-year-old male. BMI 43.5 with no weight management programme enrollment. "
            "KL grade 4. WOMAC 61. 4 months PT, NSAIDs, 2 injections."
        ),
        "urgency": "routine",
        "submitted_date": "2024-11-28",
    },
    "PA-2024-015": {
        "request_id": "PA-2024-015",
        "patient_name": "Maria Gonzalez",
        "patient_dob": "1958-03-14",
        "patient_id": "PT-90001",
        "plan_id": "PLAN-PPO-GOLD",
        "provider_npi": "NPI-1234567890",
        "facility_id": "FAC-001",
        "cpt_code": "27447",
        "diagnosis_codes": ["M17.11"],
        "clinical_notes": "Duplicate of PA-2024-001 — same patient, same procedure.",
        "urgency": "routine",
        "submitted_date": "2024-11-29",
    },
    "PA-2024-016": {
        "request_id": "PA-2024-016",
        "patient_name": "Angela Foster",
        "patient_dob": "1993-01-11",
        "patient_id": "PT-90016",
        "plan_id": "PLAN-PPO-SILVER",
        "provider_npi": "NPI-1112223334",
        "facility_id": "FAC-001",
        "cpt_code": "70553",
        "diagnosis_codes": ["G40.909"],
        "clinical_notes": (
            "31-year-old female with first-time seizure 3 days ago. No prior neurological "
            "workup. Emergency department evaluation showed no acute findings on CT. "
            "Requesting MRI brain with contrast for further evaluation."
        ),
        "urgency": "urgent",
        "submitted_date": "2024-11-30",
    },
}

CLINICAL_CRITERIA = {
    "27447": {
        "cpt_code": "27447",
        "procedure_name": "Total Knee Arthroplasty (TKA)",
        "category": "Orthopedic Surgery",
        "required_diagnoses": ["M17.0", "M17.11", "M17.12", "M17.9"],
        "diagnosis_descriptions": {
            "M17.0": "Bilateral primary osteoarthritis of knee",
            "M17.11": "Primary osteoarthritis, right knee",
            "M17.12": "Primary osteoarthritis, left knee",
            "M17.9": "Osteoarthritis of knee, unspecified",
        },
        "criteria": [
            "Documented failure of at least 3 months of conservative treatment",
            "Conservative treatments must include PT, NSAIDs, and at least one corticosteroid injection",
            "Radiographic evidence of KL grade 3 or 4",
            "WOMAC score >= 39",
            "BMI < 40 or enrolled in weight management programme",
        ],
        "medical_necessity_weights": {
            "conservative_treatment": 25,
            "imaging_grade": 25,
            "functional_score": 25,
            "bmi_compliance": 15,
            "diagnosis_match": 10,
        },
        "approval_validity_days": 90,
        "peer_review_threshold": "auto_approve_if_all_criteria_met",
    },
    "29881": {
        "cpt_code": "29881",
        "procedure_name": "Knee Arthroscopy with Meniscectomy",
        "category": "Orthopedic Surgery",
        "required_diagnoses": ["M23.21", "M23.22", "M23.31", "M23.32", "S83.21"],
        "diagnosis_descriptions": {
            "M23.21": "Derangement of anterior horn of medial meniscus, right knee",
            "M23.22": "Derangement of anterior horn of medial meniscus, left knee",
            "M23.31": "Other meniscus derangements, right knee",
            "M23.32": "Other meniscus derangements, left knee",
            "S83.21": "Bucket-handle tear of medial meniscus, current injury",
        },
        "criteria": [
            "MRI-confirmed meniscal tear",
            "Mechanical symptoms (locking, catching, giving way)",
            "Failure of 4-6 weeks conservative treatment unless acute traumatic tear",
            "Age < 65 or refractory mechanical symptoms",
        ],
        "medical_necessity_weights": {
            "imaging_confirmation": 30,
            "mechanical_symptoms": 30,
            "conservative_treatment_or_acute": 25,
            "diagnosis_match": 15,
        },
        "approval_validity_days": 60,
        "peer_review_threshold": "auto_approve_if_all_criteria_met",
    },
    "43239": {
        "cpt_code": "43239",
        "procedure_name": "Upper GI Endoscopy (EGD) with Biopsy",
        "category": "Gastroenterology",
        "required_diagnoses": ["K21.0", "K25.9", "K29.70", "K44.9", "R10.13"],
        "diagnosis_descriptions": {
            "K21.0": "GERD with esophagitis",
            "K25.9": "Gastric ulcer, unspecified",
            "K29.70": "Gastritis, unspecified",
            "K44.9": "Diaphragmatic hernia",
            "R10.13": "Epigastric pain",
        },
        "criteria": [
            "Symptoms persisting despite 8 weeks of PPI therapy",
            "Alarm symptoms (dysphagia, weight loss > 5%, GI bleeding, anemia) OR age > 55 with new-onset",
            "No EGD in past 3 years for same indication",
        ],
        "medical_necessity_weights": {
            "ppi_failure": 35,
            "alarm_symptoms": 35,
            "prior_egd_check": 15,
            "diagnosis_match": 15,
        },
        "approval_validity_days": 45,
        "peer_review_threshold": "auto_approve_if_all_criteria_met",
    },
    "70553": {
        "cpt_code": "70553",
        "procedure_name": "MRI Brain with and without Contrast",
        "category": "Diagnostic Imaging",
        "required_diagnoses": ["G43.909", "R51.9", "G40.909", "R55", "G93.40"],
        "diagnosis_descriptions": {
            "G43.909": "Migraine, unspecified",
            "R51.9": "Headache, unspecified",
            "G40.909": "Epilepsy, unspecified",
            "R55": "Syncope and collapse",
            "G93.40": "Encephalopathy, unspecified",
        },
        "criteria": [
            "New-onset severe headache with neurological deficit",
            "Seizure in adult without prior workup",
            "Progressive neurological symptoms",
            "Not a routine follow-up for known benign condition",
        ],
        "medical_necessity_weights": {
            "neurological_deficit": 35,
            "new_onset_or_seizure": 30,
            "not_routine_followup": 20,
            "diagnosis_match": 15,
        },
        "approval_validity_days": 30,
        "peer_review_threshold": "peer_review_if_routine_followup",
    },
    "64483": {
        "cpt_code": "64483",
        "procedure_name": "Transforaminal Epidural Steroid Injection (Lumbar)",
        "category": "Pain Management",
        "required_diagnoses": ["M54.5", "M51.16", "M51.17", "G55", "M54.16"],
        "diagnosis_descriptions": {
            "M54.5": "Low back pain",
            "M51.16": "Disc disorder with radiculopathy, lumbar",
            "M51.17": "Disc disorder with radiculopathy, lumbosacral",
            "G55": "Nerve root compression",
            "M54.16": "Radiculopathy, lumbar region",
        },
        "criteria": [
            "Radicular pain with positive straight leg raise or femoral stretch test",
            "Failure of at least 4 weeks conservative treatment",
            "MRI/CT confirming herniation or stenosis",
            "No more than 3 injections per region per 12-month period",
        ],
        "medical_necessity_weights": {
            "physical_exam_findings": 30,
            "conservative_treatment": 25,
            "imaging_confirmation": 25,
            "injection_frequency": 20,
        },
        "approval_validity_days": 45,
        "peer_review_threshold": "auto_approve_if_all_criteria_met",
    },
    "99999": {
        "cpt_code": "99999",
        "procedure_name": "Experimental Regenerative Cartilage Implant",
        "category": "Experimental / Investigational",
        "required_diagnoses": ["M17.11", "M17.12"],
        "diagnosis_descriptions": {
            "M17.11": "Primary osteoarthritis, right knee",
            "M17.12": "Primary osteoarthritis, left knee",
        },
        "criteria": [
            "EXPERIMENTAL — Not covered under standard benefit plans",
            "Requires medical director review",
            "FDA IDE number required",
            "Patient must be in approved clinical trial",
        ],
        "medical_necessity_weights": {
            "clinical_trial": 50,
            "ide_documentation": 30,
            "diagnosis_match": 20,
        },
        "approval_validity_days": 0,
        "peer_review_threshold": "medical_director_review_required",
    },
}

PROVIDER_NETWORK = {
    "NPI-1234567890": {"npi": "NPI-1234567890", "name": "Dr. Sarah Chen", "specialty": "Orthopedic Surgery", "network_status": "in_network", "network_tier": "preferred", "board_certified": True, "quality_score": 4.7},
    "NPI-9876543210": {"npi": "NPI-9876543210", "name": "Dr. James Morton", "specialty": "Orthopedic Surgery", "network_status": "out_of_network", "network_tier": None, "board_certified": True, "quality_score": 4.9},
    "NPI-5551234567": {"npi": "NPI-5551234567", "name": "Dr. Anika Patel", "specialty": "Gastroenterology", "network_status": "in_network", "network_tier": "standard", "board_certified": True, "quality_score": 4.5},
    "NPI-7778889990": {"npi": "NPI-7778889990", "name": "Dr. Robert Kim", "specialty": "Pain Management", "network_status": "in_network", "network_tier": "preferred", "board_certified": True, "quality_score": 4.3},
    "NPI-1112223334": {"npi": "NPI-1112223334", "name": "Dr. Emily Vasquez", "specialty": "Neurology", "network_status": "in_network", "network_tier": "standard", "board_certified": True, "quality_score": 4.6},
}

BENEFIT_PLANS = {
    "PLAN-PPO-GOLD": {
        "plan_id": "PLAN-PPO-GOLD", "plan_name": "PPO Gold Plus", "plan_type": "PPO",
        "in_network_coinsurance": 0.10, "out_of_network_coinsurance": 0.40,
        "covered_categories": ["Orthopedic Surgery", "Gastroenterology", "Diagnostic Imaging", "Pain Management"],
        "excluded_categories": ["Experimental / Investigational", "Cosmetic Surgery"],
        "pre_auth_required": True,
    },
    "PLAN-HMO-BASIC": {
        "plan_id": "PLAN-HMO-BASIC", "plan_name": "HMO Basic", "plan_type": "HMO",
        "in_network_coinsurance": 0.20, "out_of_network_coinsurance": None,
        "covered_categories": ["Orthopedic Surgery", "Gastroenterology", "Diagnostic Imaging", "Pain Management"],
        "excluded_categories": ["Experimental / Investigational", "Cosmetic Surgery"],
        "pre_auth_required": True,
    },
    "PLAN-PPO-SILVER": {
        "plan_id": "PLAN-PPO-SILVER", "plan_name": "PPO Silver", "plan_type": "PPO",
        "in_network_coinsurance": 0.20, "out_of_network_coinsurance": 0.50,
        "covered_categories": ["Orthopedic Surgery", "Gastroenterology", "Diagnostic Imaging", "Pain Management"],
        "excluded_categories": ["Experimental / Investigational"],
        "pre_auth_required": True,
    },
}

ELIGIBILITY = {
    "PT-90001": {"patient_id": "PT-90001", "eligible": True, "plan_id": "PLAN-PPO-GOLD", "effective_date": "2024-01-01", "term_date": None},
    "PT-90002": {"patient_id": "PT-90002", "eligible": True, "plan_id": "PLAN-HMO-BASIC", "effective_date": "2024-01-01", "term_date": None},
    "PT-90003": {"patient_id": "PT-90003", "eligible": True, "plan_id": "PLAN-PPO-SILVER", "effective_date": "2024-01-01", "term_date": None},
    "PT-90004": {"patient_id": "PT-90004", "eligible": True, "plan_id": "PLAN-PPO-GOLD", "effective_date": "2024-01-01", "term_date": None},
    "PT-90005": {"patient_id": "PT-90005", "eligible": True, "plan_id": "PLAN-PPO-GOLD", "effective_date": "2024-01-01", "term_date": None},
    "PT-90006": {"patient_id": "PT-90006", "eligible": True, "plan_id": "PLAN-PPO-SILVER", "effective_date": "2024-01-01", "term_date": None},
    "PT-90007": {"patient_id": "PT-90007", "eligible": True, "plan_id": "PLAN-HMO-BASIC", "effective_date": "2024-01-01", "term_date": None},
    "PT-90008": {"patient_id": "PT-90008", "eligible": True, "plan_id": "PLAN-PPO-GOLD", "effective_date": "2024-01-01", "term_date": None},
    "PT-90009": {"patient_id": "PT-90009", "eligible": True, "plan_id": "PLAN-PPO-GOLD", "effective_date": "2024-01-01", "term_date": None},
    "PT-90010": {"patient_id": "PT-90010", "eligible": True, "plan_id": "PLAN-PPO-SILVER", "effective_date": "2024-01-01", "term_date": None},
    "PT-90011": {"patient_id": "PT-90011", "eligible": True, "plan_id": "PLAN-PPO-GOLD", "effective_date": "2024-01-01", "term_date": None},
    "PT-90012": {"patient_id": "PT-90012", "eligible": True, "plan_id": "PLAN-PPO-GOLD", "effective_date": "2024-01-01", "term_date": None},
    "PT-90013": {"patient_id": "PT-90013", "eligible": True, "plan_id": "PLAN-PPO-GOLD", "effective_date": "2024-01-01", "term_date": None},
    "PT-90014": {"patient_id": "PT-90014", "eligible": True, "plan_id": "PLAN-PPO-GOLD", "effective_date": "2024-01-01", "term_date": None},
    "PT-90016": {"patient_id": "PT-90016", "eligible": True, "plan_id": "PLAN-PPO-SILVER", "effective_date": "2024-01-01", "term_date": None},
}

LETTER_TEMPLATES = {
    "approval": (
        "Dear {patient_name},\n\n"
        "Your pre-authorization request ({request_id}) for {procedure_name} has been APPROVED.\n\n"
        "Provider: {provider_name}\nFacility: {facility_name}\n"
        "Authorization valid for {validity_days} days from {decision_date}.\n\n"
        "Conditions:\n{conditions}\n\n"
        "If you have questions, contact Member Services at 1-800-555-PLAN.\n\nSincerely,\nPre-Authorization Department"
    ),
    "denial": (
        "Dear {patient_name},\n\n"
        "Your pre-authorization request ({request_id}) for {procedure_name} has been DENIED.\n\n"
        "Reason: {reason}\n\nYou have the right to appeal this decision within 60 days.\n"
        "To file an appeal, contact Member Services at 1-800-555-PLAN.\n\nSincerely,\nPre-Authorization Department"
    ),
    "pended": (
        "Dear {patient_name},\n\n"
        "Your pre-authorization request ({request_id}) for {procedure_name} "
        "has been PENDED for additional review.\n\nReason: {reason}\n\n"
        "A clinical reviewer will contact your provider within 5 business days.\n\nSincerely,\nPre-Authorization Department"
    ),
}
