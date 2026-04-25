"""
Mock data for Healthcare Pre-Authorization Decision Support Agent.

This module contains realistic (but fictional) clinical criteria,
provider network data, and patient benefit plans used by the agent's tools.
"""

# ---------------------------------------------------------------------------
# Clinical Criteria Database
# Each entry maps a CPT code to the clinical criteria required for approval.
# ---------------------------------------------------------------------------
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
            "Conservative treatments must include physical therapy, NSAIDs, and at least one corticosteroid injection",
            "Radiographic evidence of moderate to severe joint space narrowing (Kellgren-Lawrence grade 3 or 4)",
            "Functional impairment documented by validated outcome measure (e.g., WOMAC score >= 39)",
            "BMI < 40 or documentation of weight management programme enrollment",
        ],
        "required_documentation": [
            "Office visit notes from the past 6 months",
            "Imaging reports (X-ray or MRI within 12 months)",
            "Physical therapy progress notes",
            "Conservative treatment log",
        ],
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
            "Mechanical symptoms present (locking, catching, giving way)",
            "Failure of 4-6 weeks of conservative treatment unless acute traumatic tear",
            "Patient age < 65 or documentation of mechanical symptoms refractory to conservative care",
        ],
        "required_documentation": [
            "MRI report within 6 months",
            "Physical examination notes documenting mechanical symptoms",
            "Conservative treatment log (if non-acute)",
        ],
        "approval_validity_days": 60,
        "peer_review_threshold": "auto_approve_if_all_criteria_met",
    },
    "43239": {
        "cpt_code": "43239",
        "procedure_name": "Upper GI Endoscopy (EGD) with Biopsy",
        "category": "Gastroenterology",
        "required_diagnoses": ["K21.0", "K25.9", "K29.70", "K44.9", "R10.13"],
        "diagnosis_descriptions": {
            "K21.0": "Gastro-esophageal reflux disease with esophagitis",
            "K25.9": "Gastric ulcer, unspecified",
            "K29.70": "Gastritis, unspecified, without bleeding",
            "K44.9": "Diaphragmatic hernia without obstruction or gangrene",
            "R10.13": "Epigastric pain",
        },
        "criteria": [
            "Symptoms persisting despite 8 weeks of PPI therapy",
            "Alarm symptoms present (dysphagia, weight loss > 5%, GI bleeding, anemia) OR age > 55 with new-onset symptoms",
            "No EGD in the past 3 years for the same indication",
        ],
        "required_documentation": [
            "Medication history showing PPI trial",
            "Symptom documentation",
            "Lab results if anemia is cited",
        ],
        "approval_validity_days": 45,
        "peer_review_threshold": "auto_approve_if_all_criteria_met",
    },
    "70553": {
        "cpt_code": "70553",
        "procedure_name": "MRI Brain with and without Contrast",
        "category": "Diagnostic Imaging",
        "required_diagnoses": ["G43.909", "R51.9", "G40.909", "R55", "G93.40"],
        "diagnosis_descriptions": {
            "G43.909": "Migraine, unspecified, not intractable",
            "R51.9": "Headache, unspecified",
            "G40.909": "Epilepsy, unspecified, not intractable",
            "R55": "Syncope and collapse",
            "G93.40": "Encephalopathy, unspecified",
        },
        "criteria": [
            "New-onset severe headache with neurological deficit",
            "Seizure in adult without prior workup",
            "Progressive neurological symptoms",
            "Not a routine follow-up for known benign condition (requires peer review if so)",
        ],
        "required_documentation": [
            "Neurological examination findings",
            "Symptom onset and progression notes",
            "Prior imaging results (if any)",
        ],
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
            "M51.16": "Intervertebral disc disorder with radiculopathy, lumbar region",
            "M51.17": "Intervertebral disc disorder with radiculopathy, lumbosacral region",
            "G55": "Nerve root and plexus compressions in diseases classified elsewhere",
            "M54.16": "Radiculopathy, lumbar region",
        },
        "criteria": [
            "Radicular pain documented by physical examination (positive straight leg raise or femoral stretch test)",
            "Failure of at least 4 weeks of conservative treatment (physical therapy, oral medications)",
            "MRI or CT confirming disc herniation or spinal stenosis at a level consistent with symptoms",
            "No more than 3 injections per region per 12-month period",
        ],
        "required_documentation": [
            "Advanced imaging (MRI or CT) within 12 months",
            "Physical examination with neurological findings",
            "Conservative treatment log",
            "History of prior injections (dates, levels, outcomes)",
        ],
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
            "Requires medical director review and explicit plan exception",
            "FDA investigational device exemption (IDE) number must be provided",
            "Patient must be enrolled in an approved clinical trial",
        ],
        "required_documentation": [
            "Clinical trial enrollment confirmation",
            "IDE number",
            "Informed consent documentation",
            "Investigator qualifications",
        ],
        "approval_validity_days": 0,
        "peer_review_threshold": "medical_director_review_required",
    },
}

# ---------------------------------------------------------------------------
# Provider Network Data
# ---------------------------------------------------------------------------
PROVIDER_NETWORK = {
    "NPI-1234567890": {
        "npi": "NPI-1234567890",
        "name": "Dr. Sarah Chen",
        "specialty": "Orthopedic Surgery",
        "practice": "Valley Orthopedics & Sports Medicine",
        "network_status": "in_network",
        "network_tier": "preferred",
        "accepting_new_patients": True,
        "facility_affiliations": ["FAC-001", "FAC-003"],
        "state_licenses": ["CA", "NV"],
        "board_certified": True,
        "quality_score": 4.7,
    },
    "NPI-9876543210": {
        "npi": "NPI-9876543210",
        "name": "Dr. James Morton",
        "specialty": "Orthopedic Surgery",
        "practice": "Premier Joint & Spine Institute",
        "network_status": "out_of_network",
        "network_tier": None,
        "accepting_new_patients": True,
        "facility_affiliations": ["FAC-005"],
        "state_licenses": ["CA"],
        "board_certified": True,
        "quality_score": 4.9,
    },
    "NPI-5551234567": {
        "npi": "NPI-5551234567",
        "name": "Dr. Anika Patel",
        "specialty": "Gastroenterology",
        "practice": "Digestive Health Associates",
        "network_status": "in_network",
        "network_tier": "standard",
        "accepting_new_patients": True,
        "facility_affiliations": ["FAC-001", "FAC-002"],
        "state_licenses": ["CA", "OR", "WA"],
        "board_certified": True,
        "quality_score": 4.5,
    },
    "NPI-7778889990": {
        "npi": "NPI-7778889990",
        "name": "Dr. Robert Kim",
        "specialty": "Pain Management",
        "practice": "Pacific Pain & Rehabilitation Center",
        "network_status": "in_network",
        "network_tier": "preferred",
        "accepting_new_patients": False,
        "facility_affiliations": ["FAC-002"],
        "state_licenses": ["CA"],
        "board_certified": True,
        "quality_score": 4.3,
    },
    "NPI-1112223334": {
        "npi": "NPI-1112223334",
        "name": "Dr. Emily Vasquez",
        "specialty": "Neurology",
        "practice": "NeuroCare Specialists",
        "network_status": "in_network",
        "network_tier": "standard",
        "accepting_new_patients": True,
        "facility_affiliations": ["FAC-001"],
        "state_licenses": ["CA", "AZ"],
        "board_certified": True,
        "quality_score": 4.6,
    },
}

FACILITIES = {
    "FAC-001": {
        "id": "FAC-001",
        "name": "Valley Medical Center",
        "network_status": "in_network",
        "type": "Hospital — Acute Care",
        "city": "San Jose",
        "state": "CA",
    },
    "FAC-002": {
        "id": "FAC-002",
        "name": "Bay Area Ambulatory Surgery Center",
        "network_status": "in_network",
        "type": "Ambulatory Surgery Center",
        "city": "Palo Alto",
        "state": "CA",
    },
    "FAC-003": {
        "id": "FAC-003",
        "name": "Coastal Community Hospital",
        "network_status": "in_network",
        "type": "Hospital — Acute Care",
        "city": "Santa Cruz",
        "state": "CA",
    },
    "FAC-005": {
        "id": "FAC-005",
        "name": "Summit Specialty Hospital",
        "network_status": "out_of_network",
        "type": "Specialty Hospital",
        "city": "Beverly Hills",
        "state": "CA",
    },
}

# ---------------------------------------------------------------------------
# Patient Benefit Plans
# ---------------------------------------------------------------------------
BENEFIT_PLANS = {
    "PLAN-PPO-GOLD": {
        "plan_id": "PLAN-PPO-GOLD",
        "plan_name": "PPO Gold Plus",
        "plan_type": "PPO",
        "in_network_deductible": 500,
        "in_network_deductible_met": 500,
        "out_of_network_deductible": 2000,
        "out_of_network_deductible_met": 750,
        "in_network_coinsurance": 0.10,
        "out_of_network_coinsurance": 0.40,
        "in_network_oop_max": 4000,
        "out_of_network_oop_max": 12000,
        "current_oop_spent": 1200,
        "surgical_benefit": True,
        "pre_auth_required": True,
        "experimental_exclusion": True,
        "covered_categories": [
            "Orthopedic Surgery",
            "Gastroenterology",
            "Diagnostic Imaging",
            "Pain Management",
        ],
        "excluded_categories": ["Experimental / Investigational", "Cosmetic Surgery"],
        "annual_max": None,
        "notes": "Standard employer group plan with comprehensive surgical coverage.",
    },
    "PLAN-HMO-BASIC": {
        "plan_id": "PLAN-HMO-BASIC",
        "plan_name": "HMO Basic",
        "plan_type": "HMO",
        "in_network_deductible": 1500,
        "in_network_deductible_met": 400,
        "out_of_network_deductible": None,
        "out_of_network_deductible_met": None,
        "in_network_coinsurance": 0.20,
        "out_of_network_coinsurance": None,
        "in_network_oop_max": 7500,
        "out_of_network_oop_max": None,
        "current_oop_spent": 800,
        "surgical_benefit": True,
        "pre_auth_required": True,
        "experimental_exclusion": True,
        "covered_categories": [
            "Orthopedic Surgery",
            "Gastroenterology",
            "Diagnostic Imaging",
            "Pain Management",
        ],
        "excluded_categories": ["Experimental / Investigational", "Cosmetic Surgery"],
        "annual_max": 250000,
        "notes": "HMO plan — out-of-network services NOT covered except emergencies.",
    },
    "PLAN-PPO-SILVER": {
        "plan_id": "PLAN-PPO-SILVER",
        "plan_name": "PPO Silver",
        "plan_type": "PPO",
        "in_network_deductible": 1000,
        "in_network_deductible_met": 1000,
        "out_of_network_deductible": 3000,
        "out_of_network_deductible_met": 0,
        "in_network_coinsurance": 0.20,
        "out_of_network_coinsurance": 0.50,
        "in_network_oop_max": 6500,
        "out_of_network_oop_max": 15000,
        "current_oop_spent": 3200,
        "surgical_benefit": True,
        "pre_auth_required": True,
        "experimental_exclusion": True,
        "covered_categories": [
            "Orthopedic Surgery",
            "Gastroenterology",
            "Diagnostic Imaging",
            "Pain Management",
        ],
        "excluded_categories": ["Experimental / Investigational"],
        "annual_max": None,
        "notes": "Mid-tier PPO with deductible already met for in-network services.",
    },
}

# ---------------------------------------------------------------------------
# Sample Pre-Auth Requests (used for testing)
# ---------------------------------------------------------------------------
SAMPLE_REQUESTS = {
    "REQ-001": {
        "request_id": "REQ-001",
        "patient_name": "Maria Gonzalez",
        "patient_dob": "1958-03-14",
        "plan_id": "PLAN-PPO-GOLD",
        "provider_npi": "NPI-1234567890",
        "facility_id": "FAC-001",
        "cpt_code": "27447",
        "diagnosis_codes": ["M17.11"],
        "clinical_notes": (
            "Patient is a 68-year-old female with 2-year history of progressive right knee pain. "
            "Kellgren-Lawrence grade 3 on recent X-ray. WOMAC score 52. Failed 6 months of conservative "
            "management including PT (12 sessions), naproxen 500mg BID, and two corticosteroid injections "
            "(most recent 3 months ago with minimal relief). BMI 32.1. Requesting total knee arthroplasty."
        ),
    },
    "REQ-002": {
        "request_id": "REQ-002",
        "patient_name": "David Park",
        "patient_dob": "1985-11-22",
        "plan_id": "PLAN-HMO-BASIC",
        "provider_npi": "NPI-9876543210",
        "facility_id": "FAC-005",
        "cpt_code": "27447",
        "diagnosis_codes": ["M17.11"],
        "clinical_notes": (
            "35-year-old male with right knee OA secondary to prior ACL reconstruction. "
            "Requesting TKA with out-of-network surgeon Dr. Morton at Summit Specialty Hospital."
        ),
    },
    "REQ-003": {
        "request_id": "REQ-003",
        "patient_name": "Linda Chen",
        "patient_dob": "1972-07-09",
        "plan_id": "PLAN-PPO-SILVER",
        "provider_npi": "NPI-1234567890",
        "facility_id": "FAC-001",
        "cpt_code": "99999",
        "diagnosis_codes": ["M17.12"],
        "clinical_notes": (
            "Patient requesting experimental regenerative cartilage implant for left knee OA. "
            "Patient has been evaluated for clinical trial NCT-0042889 at Valley Medical Center."
        ),
    },
}
