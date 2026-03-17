# backend/services/tn_automotive_taxonomy.py
"""
Tamil Nadu Automotive & EV Skill Taxonomy
Maps skills to NSQF levels, job roles, and training institutions.
Aligned with TN AUTO Skills Development Centers and Naan Mudhalvan curriculum.
"""

from typing import Dict, List, Optional
import re

# ─── NSQF Level Descriptors ───────────────────────────────────────────────────
NSQF_LEVELS = {
    1: {"label": "NSQF Level 1", "description": "Basic awareness, no prior skill needed", "equivalent": "Below Class 8"},
    2: {"label": "NSQF Level 2", "description": "Semi-skilled worker, supervised tasks", "equivalent": "Class 8–10"},
    3: {"label": "NSQF Level 3", "description": "Skilled worker, independent tasks", "equivalent": "Class 10 / ITI 1st year"},
    4: {"label": "NSQF Level 4", "description": "Supervisory / technician level", "equivalent": "ITI Pass / Diploma 1st year"},
    5: {"label": "NSQF Level 5", "description": "Technician / foreman", "equivalent": "Diploma / B.Voc"},
    6: {"label": "NSQF Level 6", "description": "Junior Engineer / Analyst", "equivalent": "B.E. / B.Tech"},
    7: {"label": "NSQF Level 7", "description": "Senior Engineer / Specialist", "equivalent": "M.E. / M.Tech / MBA"},
}

# ─── TN Automotive Skill Database ─────────────────────────────────────────────
# Each skill entry:
#   keywords     : regex-matchable terms found in resumes / job descriptions
#   nsqf_level   : minimum NSQF level the skill is associated with
#   category     : skill domain
#   sector       : "automotive" | "ev" | "manufacturing" | "common"
#   related_roles: TN job roles that require this skill
#   training_src : TN institutions / programs where this can be learned
TN_SKILL_DB: List[Dict] = [

    # ── EV-Specific Skills ─────────────────────────────────────────────────────
    {
        "skill": "Battery Management System (BMS)",
        "keywords": ["bms", "battery management", "battery management system", "cell balancing",
                     "soc estimation", "state of charge"],
        "nsqf_level": 5,
        "category": "EV Electronics",
        "sector": "ev",
        "related_roles": ["EV Technician", "Battery Pack Engineer", "BMS Engineer"],
        "training_src": ["Naan Mudhalvan – EV Module", "TNSDC EV Skill Centre", "ARAI Pune Online"],
    },
    {
        "skill": "Electric Motor & Drive Systems",
        "keywords": ["bldc motor", "pmsm", "induction motor", "motor controller", "motor drives",
                     "vfd", "variable frequency drive", "traction motor"],
        "nsqf_level": 5,
        "category": "EV Powertrain",
        "sector": "ev",
        "related_roles": ["EV Powertrain Technician", "Drive System Engineer"],
        "training_src": ["Naan Mudhalvan – EV Module", "CIPET Chennai", "TNSDC"],
    },
    {
        "skill": "CAN Bus / Automotive Communication Protocols",
        "keywords": ["can bus", "canbus", "lin bus", "autosar", "uds", "obd", "obd2",
                     "j1939", "automotive ethernet", "flexray"],
        "nsqf_level": 6,
        "category": "Embedded & Protocols",
        "sector": "ev",
        "related_roles": ["Embedded Systems Engineer", "Automotive Diagnostics Technician"],
        "training_src": ["Vector Academy Online", "KPIT Campus Connect", "NIT Trichy"],
    },
    {
        "skill": "EV Charging Infrastructure",
        "keywords": ["ev charging", "ev charger", "ac charging", "dc fast charging", "ocpp",
                     "ccs", "chademo", "type 2 charging", "charging station"],
        "nsqf_level": 4,
        "category": "EV Infrastructure",
        "sector": "ev",
        "related_roles": ["EV Charging Technician", "Infrastructure Engineer"],
        "training_src": ["Naan Mudhalvan – EV Module", "TNSDC EV Skill Centre"],
    },
    {
        "skill": "High Voltage Safety (HV Safety)",
        "keywords": ["high voltage safety", "hv safety", "ev safety", "electrical safety",
                     "arc flash", "ppe ev", "isolation testing"],
        "nsqf_level": 4,
        "category": "Safety",
        "sector": "ev",
        "related_roles": ["EV Technician", "Service Engineer", "HV Safety Officer"],
        "training_src": ["TNSDC EV Skill Centre", "BOSCH Training Centre Chennai"],
    },
    {
        "skill": "Thermal Management in EVs",
        "keywords": ["thermal management", "battery cooling", "heat exchanger ev",
                     "thermal runaway", "battery thermal"],
        "nsqf_level": 6,
        "category": "EV Electronics",
        "sector": "ev",
        "related_roles": ["Battery Systems Engineer", "NVH Engineer"],
        "training_src": ["IIT Madras Online", "ARAI Pune Online"],
    },

    # ── Automotive Manufacturing Skills ───────────────────────────────────────
    {
        "skill": "CNC Machine Operation",
        "keywords": ["cnc", "cnc machine", "cnc operator", "cnc programming", "g-code",
                     "m-code", "fanuc", "siemens cnc", "lathe cnc", "milling cnc"],
        "nsqf_level": 4,
        "category": "Machining",
        "sector": "automotive",
        "related_roles": ["CNC Operator", "Machinist", "Tool Room Technician"],
        "training_src": ["Government ITI Chennai", "Government ITI Coimbatore", "NTTF Hosur"],
    },
    {
        "skill": "PLC Programming",
        "keywords": ["plc", "plc programming", "siemens s7", "allen bradley", "ladder logic",
                     "scada", "hmi", "automation plc", "programmable logic"],
        "nsqf_level": 5,
        "category": "Automation",
        "sector": "automotive",
        "related_roles": ["PLC Technician", "Automation Engineer", "Maintenance Engineer"],
        "training_src": ["Government Polytechnic Chennai", "SIEMENS Skill Centre TN", "Naan Mudhalvan – Automation"],
    },
    {
        "skill": "Welding (MIG/TIG/Spot)",
        "keywords": ["welding", "mig welding", "tig welding", "spot welding", "arc welding",
                     "gmaw", "gtaw", "resistance welding", "robotic welding"],
        "nsqf_level": 3,
        "category": "Fabrication",
        "sector": "automotive",
        "related_roles": ["Welder", "Fabrication Technician", "Body Shop Technician"],
        "training_src": ["Government ITI", "ESAB Welding Academy Chennai", "TNSDC"],
    },
    {
        "skill": "Quality Control & Inspection (IATF 16949)",
        "keywords": ["quality control", "qc", "iatf", "iatf 16949", "iso/ts 16949",
                     "quality inspection", "ppap", "fmea", "control plan", "8d report",
                     "spc", "statistical process control", "cmm", "gauge r&r"],
        "nsqf_level": 5,
        "category": "Quality",
        "sector": "automotive",
        "related_roles": ["Quality Inspector", "QC Engineer", "Quality Analyst"],
        "training_src": ["CII Quality Centre", "TUV SUD India", "Naan Mudhalvan – Quality"],
    },
    {
        "skill": "CAD / AutoCAD / SolidWorks",
        "keywords": ["autocad", "solidworks", "catia", "nx cad", "pro-e", "creo",
                     "cad design", "3d modelling", "2d drafting", "mechanical design"],
        "nsqf_level": 5,
        "category": "Design",
        "sector": "automotive",
        "related_roles": ["CAD Designer", "Design Engineer", "Tooling Engineer"],
        "training_src": ["Government Polytechnic", "CADD Centre Chennai", "Naan Mudhalvan – CAD/CAM"],
    },
    {
        "skill": "Lean Manufacturing / 5S",
        "keywords": ["lean", "lean manufacturing", "5s", "kaizen", "six sigma",
                     "value stream mapping", "vsm", "tpm", "oee", "jit", "just in time",
                     "poka yoke", "kanban manufacturing"],
        "nsqf_level": 4,
        "category": "Production Management",
        "sector": "automotive",
        "related_roles": ["Production Supervisor", "Lean Coach", "Process Engineer"],
        "training_src": ["CII Institute of Quality", "ACMA Skill Development", "Naan Mudhalvan"],
    },
    {
        "skill": "Robotics & Industrial Automation",
        "keywords": ["robotics", "industrial robot", "kuka", "fanuc robot", "abb robot",
                     "robot programming", "cobots", "robotic arm", "pick and place robot"],
        "nsqf_level": 5,
        "category": "Automation",
        "sector": "automotive",
        "related_roles": ["Robotics Technician", "Automation Engineer"],
        "training_src": ["KUKA College Chennai", "Naan Mudhalvan – Robotics", "SIEMENS Skill Centre"],
    },
    {
        "skill": "Hydraulics & Pneumatics",
        "keywords": ["hydraulics", "pneumatics", "hydraulic system", "pneumatic system",
                     "fluid power", "actuator", "solenoid valve"],
        "nsqf_level": 4,
        "category": "Mechanical Systems",
        "sector": "automotive",
        "related_roles": ["Maintenance Technician", "Hydraulics Technician"],
        "training_src": ["Government ITI", "FESTO Training Centre", "Government Polytechnic"],
    },
    {
        "skill": "Sheet Metal & Press Shop",
        "keywords": ["sheet metal", "press shop", "stamping", "deep drawing", "blanking",
                     "punching press", "die design", "progressive die"],
        "nsqf_level": 3,
        "category": "Fabrication",
        "sector": "automotive",
        "related_roles": ["Press Shop Operator", "Sheet Metal Technician"],
        "training_src": ["Government ITI", "TNSDC", "ACMA Skill Development"],
    },

    # ── Common / Cross-Sector Skills ──────────────────────────────────────────
    {
        "skill": "Embedded C / Microcontroller Programming",
        "keywords": ["embedded c", "microcontroller", "arduino", "stm32", "pic", "avr",
                     "arm cortex", "rtos", "real-time os", "firmware"],
        "nsqf_level": 6,
        "category": "Embedded Systems",
        "sector": "common",
        "related_roles": ["Embedded Engineer", "Firmware Developer", "ECU Developer"],
        "training_src": ["NIT Trichy", "Anna University", "Naan Mudhalvan – IoT & Embedded"],
    },
    {
        "skill": "IoT & Industry 4.0",
        "keywords": ["iot", "industry 4.0", "industrial iot", "iiot", "mqtt", "opc-ua",
                     "digital twin", "predictive maintenance", "condition monitoring"],
        "nsqf_level": 6,
        "category": "Digital Manufacturing",
        "sector": "common",
        "related_roles": ["IoT Engineer", "Industry 4.0 Specialist", "Smart Manufacturing Engineer"],
        "training_src": ["Naan Mudhalvan – IoT", "SIEMENS Skill Centre", "IIT Madras Online"],
    },
    {
        "skill": "Data Analysis & Python",
        "keywords": ["python", "data analysis", "pandas", "numpy", "matplotlib",
                     "data visualization", "excel analytics", "power bi", "tableau"],
        "nsqf_level": 6,
        "category": "Data & Analytics",
        "sector": "common",
        "related_roles": ["Data Analyst", "Production Analytics Engineer"],
        "training_src": ["Naan Mudhalvan – Data Science", "GUVI Chennai", "NSDC Online"],
    },
    {
        "skill": "ERP / SAP Manufacturing",
        "keywords": ["erp", "sap", "sap mm", "sap pp", "sap qm", "oracle erp",
                     "mes", "manufacturing execution system"],
        "nsqf_level": 5,
        "category": "Enterprise Systems",
        "sector": "common",
        "related_roles": ["SAP Consultant", "Production Planner", "Supply Chain Analyst"],
        "training_src": ["SAP Training Centre Chennai", "NIIT TN", "Naan Mudhalvan – ERP"],
    },
    {
        "skill": "English Communication & Soft Skills",
        "keywords": ["communication", "english communication", "presentation skills",
                     "team work", "leadership", "problem solving"],
        "nsqf_level": 3,
        "category": "Soft Skills",
        "sector": "common",
        "related_roles": ["All roles"],
        "training_src": ["Naan Mudhalvan – Soft Skills", "TNSDC", "Government ITI"],
    },
]

# ─── TN Automotive Job Role Profiles ─────────────────────────────────────────
# Pre-defined job role → required skills mappings for TN automotive clusters
TN_JOB_ROLES: Dict[str, Dict] = {
    "EV Technician": {
        "description": "Diagnoses, services, and repairs electric vehicles",
        "cluster": "Chennai / Hosur / Coimbatore",
        "nsqf_target": 4,
        "required_skills": [
            "Battery Management System (BMS)",
            "Electric Motor & Drive Systems",
            "High Voltage Safety (HV Safety)",
            "EV Charging Infrastructure",
        ],
        "preferred_skills": [
            "Embedded C / Microcontroller Programming",
            "CAN Bus / Automotive Communication Protocols",
        ],
        "typical_employer": ["Ola Electric", "TVS Motor", "Ashok Leyland EV", "TATA Motors"],
    },
    "CNC Operator": {
        "description": "Operates CNC machines in automotive component manufacturing",
        "cluster": "Hosur / Coimbatore / Chennai",
        "nsqf_target": 4,
        "required_skills": [
            "CNC Machine Operation",
            "Quality Control & Inspection (IATF 16949)",
        ],
        "preferred_skills": [
            "CAD / AutoCAD / SolidWorks",
            "Lean Manufacturing / 5S",
        ],
        "typical_employer": ["Sundaram Clayton", "Rane Group", "Lucas TVS", "Wheels India"],
    },
    "Automation / PLC Engineer": {
        "description": "Programs and maintains automated production lines",
        "cluster": "Chennai / Hosur",
        "nsqf_target": 5,
        "required_skills": [
            "PLC Programming",
            "Robotics & Industrial Automation",
            "Hydraulics & Pneumatics",
        ],
        "preferred_skills": [
            "IoT & Industry 4.0",
            "ERP / SAP Manufacturing",
        ],
        "typical_employer": ["Ford Chennai", "Hyundai India", "Saint-Gobain", "Ashok Leyland"],
    },
    "Quality Inspector (Automotive)": {
        "description": "Inspects parts and assemblies against IATF standards",
        "cluster": "Chennai / Hosur / Coimbatore",
        "nsqf_target": 4,
        "required_skills": [
            "Quality Control & Inspection (IATF 16949)",
            "CAD / AutoCAD / SolidWorks",
        ],
        "preferred_skills": [
            "Lean Manufacturing / 5S",
            "ERP / SAP Manufacturing",
        ],
        "typical_employer": ["Delphi TVS", "Minda Industries", "Sundaram Fasteners"],
    },
    "Battery Pack Assembler": {
        "description": "Assembles lithium-ion battery packs for EVs",
        "cluster": "Hosur / Chennai",
        "nsqf_target": 3,
        "required_skills": [
            "Battery Management System (BMS)",
            "High Voltage Safety (HV Safety)",
            "Welding (MIG/TIG/Spot)",
        ],
        "preferred_skills": [
            "Quality Control & Inspection (IATF 16949)",
            "Lean Manufacturing / 5S",
        ],
        "typical_employer": ["Ola Electric", "Amara Raja Energy", "Exide Industries"],
    },
    "Embedded Systems Engineer": {
        "description": "Develops firmware and embedded software for automotive ECUs",
        "cluster": "Chennai",
        "nsqf_target": 6,
        "required_skills": [
            "Embedded C / Microcontroller Programming",
            "CAN Bus / Automotive Communication Protocols",
        ],
        "preferred_skills": [
            "Battery Management System (BMS)",
            "IoT & Industry 4.0",
        ],
        "typical_employer": ["Kpit Technologies", "Tata Elxsi", "Robert Bosch India", "Continental"],
    },
    "Production / Maintenance Technician": {
        "description": "Maintains equipment and production processes in auto factories",
        "cluster": "Chennai / Hosur / Coimbatore",
        "nsqf_target": 4,
        "required_skills": [
            "Hydraulics & Pneumatics",
            "PLC Programming",
            "Lean Manufacturing / 5S",
        ],
        "preferred_skills": [
            "Robotics & Industrial Automation",
            "IoT & Industry 4.0",
        ],
        "typical_employer": ["Hyundai India", "Ford Chennai", "Royal Enfield", "TVS Motor"],
    },
}


# ─── Extractor Class ──────────────────────────────────────────────────────────

class TNAutomotiveSkillExtractor:
    """
    Extracts TN automotive / EV skills from resume or profile text,
    maps them to NSQF levels, and compares against job role requirements.
    """

    def __init__(self):
        self.skill_db = TN_SKILL_DB
        self.job_roles = TN_JOB_ROLES
        self.nsqf_levels = NSQF_LEVELS

    def extract_skills(self, text: str) -> List[Dict]:
        """
        Extract TN automotive skills from text.
        Returns list of matched skill dicts with NSQF level and category.
        """
        text_lower = text.lower()
        found = []

        for entry in self.skill_db:
            for kw in entry["keywords"]:
                pattern = rf'\b{re.escape(kw)}\b'
                if re.search(pattern, text_lower):
                    found.append({
                        "skill": entry["skill"],
                        "category": entry["category"],
                        "sector": entry["sector"],
                        "nsqf_level": entry["nsqf_level"],
                        "nsqf_label": NSQF_LEVELS[entry["nsqf_level"]]["label"],
                        "training_src": entry["training_src"],
                    })
                    break  # matched — move to next skill entry

        return found

    def get_skill_gaps_for_role(self, extracted_skills: List[Dict], role_name: str) -> Dict:
        """
        Compare extracted skills against a TN job role profile.
        Returns matched, missing (gaps), and NSQF readiness.
        """
        role = self.job_roles.get(role_name)
        if not role:
            return {"error": f"Role '{role_name}' not found in TN taxonomy"}

        extracted_names = {s["skill"] for s in extracted_skills}
        required = role["required_skills"]
        preferred = role["preferred_skills"]

        matched_required = [s for s in required if s in extracted_names]
        missing_required = [s for s in required if s not in extracted_names]
        matched_preferred = [s for s in preferred if s in extracted_names]
        missing_preferred = [s for s in preferred if s not in extracted_names]

        # NSQF readiness: highest NSQF level among extracted skills
        extracted_nsqf = [s["nsqf_level"] for s in extracted_skills] or [1]
        current_nsqf = max(extracted_nsqf)
        target_nsqf = role["nsqf_target"]
        nsqf_gap = max(0, target_nsqf - current_nsqf)

        overall_match = (
            len(matched_required) / len(required) * 100 if required else 0
        )

        # Build gap details with training recommendations
        gap_details = []
        for skill_name in missing_required:
            skill_entry = next((s for s in self.skill_db if s["skill"] == skill_name), None)
            gap_details.append({
                "skill": skill_name,
                "gap_severity": "critical",
                "nsqf_level_needed": skill_entry["nsqf_level"] if skill_entry else target_nsqf,
                "training_recommendations": skill_entry["training_src"] if skill_entry else [],
            })
        for skill_name in missing_preferred:
            skill_entry = next((s for s in self.skill_db if s["skill"] == skill_name), None)
            gap_details.append({
                "skill": skill_name,
                "gap_severity": "moderate",
                "nsqf_level_needed": skill_entry["nsqf_level"] if skill_entry else target_nsqf,
                "training_recommendations": skill_entry["training_src"] if skill_entry else [],
            })

        return {
            "role": role_name,
            "overall_match_pct": round(overall_match, 1),
            "nsqf_current": current_nsqf,
            "nsqf_target": target_nsqf,
            "nsqf_gap": nsqf_gap,
            "nsqf_current_label": NSQF_LEVELS[current_nsqf]["label"],
            "nsqf_target_label": NSQF_LEVELS[target_nsqf]["label"],
            "matched_required": matched_required,
            "matched_preferred": matched_preferred,
            "skill_gaps": gap_details,
            "role_description": role["description"],
            "cluster": role["cluster"],
            "typical_employers": role["typical_employer"],
        }

    def batch_analyze(self, profiles: List[Dict]) -> Dict:
        """
        Analyze a batch of student/worker profiles.
        Each profile: {"name": str, "id": str, "text": str, "target_role": str (optional)}

        Returns cohort-level analytics + individual breakdowns.
        """
        results = []
        skill_frequency: Dict[str, int] = {}
        gap_frequency: Dict[str, int] = {}
        nsqf_distribution: Dict[int, int] = {i: 0 for i in range(1, 8)}
        role_readiness: Dict[str, List[float]] = {}

        for profile in profiles:
            text = profile.get("text", "")
            name = profile.get("name", "Unknown")
            pid = profile.get("id", name)
            target_role = profile.get("target_role", None)

            extracted = self.extract_skills(text)

            # Skill frequency
            for s in extracted:
                skill_frequency[s["skill"]] = skill_frequency.get(s["skill"], 0) + 1

            # NSQF distribution
            nsqf_vals = [s["nsqf_level"] for s in extracted]
            peak_nsqf = max(nsqf_vals) if nsqf_vals else 1
            nsqf_distribution[peak_nsqf] = nsqf_distribution.get(peak_nsqf, 0) + 1

            # Role analysis
            role_analysis = None
            if target_role and target_role in self.job_roles:
                role_analysis = self.get_skill_gaps_for_role(extracted, target_role)
                score = role_analysis["overall_match_pct"]
                if target_role not in role_readiness:
                    role_readiness[target_role] = []
                role_readiness[target_role].append(score)

                # Gap frequency
                for gap in role_analysis["skill_gaps"]:
                    gsk = gap["skill"]
                    gap_frequency[gsk] = gap_frequency.get(gsk, 0) + 1

            results.append({
                "id": pid,
                "name": name,
                "skills_found": len(extracted),
                "peak_nsqf": peak_nsqf,
                "peak_nsqf_label": NSQF_LEVELS[peak_nsqf]["label"],
                "extracted_skills": extracted,
                "role_analysis": role_analysis,
            })

        total = len(profiles)

        # Top skill gaps across cohort
        top_gaps = sorted(gap_frequency.items(), key=lambda x: x[1], reverse=True)[:10]

        # Top skills present
        top_skills = sorted(skill_frequency.items(), key=lambda x: x[1], reverse=True)[:10]

        # Avg role readiness per role
        avg_readiness = {
            role: round(sum(scores) / len(scores), 1)
            for role, scores in role_readiness.items()
        }

        return {
            "total_profiles": total,
            "cohort_summary": {
                "avg_skills_per_person": round(
                    sum(r["skills_found"] for r in results) / total, 1
                ) if total else 0,
                "nsqf_distribution": nsqf_distribution,
                "top_skill_gaps": [{"skill": k, "count": v, "pct": round(v / total * 100, 1)}
                                   for k, v in top_gaps],
                "top_skills_present": [{"skill": k, "count": v, "pct": round(v / total * 100, 1)}
                                       for k, v in top_skills],
                "avg_role_readiness": avg_readiness,
            },
            "individual_results": results,
        }

    def list_roles(self) -> List[str]:
        return list(self.job_roles.keys())

    def get_role_profile(self, role_name: str) -> Optional[Dict]:
        return self.job_roles.get(role_name)


# Singleton
tn_extractor = TNAutomotiveSkillExtractor()