"""
TN Automotive Taxonomy - Stub implementation.
"""
from typing import Any, Dict, List


class TNAutomotiveSkillExtractor:
    def batch_analyze(self, profiles: List) -> Dict:
        return {"status": "not_implemented", "profiles_received": len(profiles)}

    def list_roles(self) -> List[str]:
        return ["Automotive Engineer", "EV Specialist", "BMS Engineer", "PLC Programmer"]

    def extract_skills(self, text: str) -> List[str]:
        keywords = ["bms", "can bus", "plc", "cnc", "scada", "iatf", "solidworks",
                    "autocad", "catia", "embedded c", "microcontroller", "arduino",
                    "stm32", "iot", "hydraulics", "pneumatics"]
        text_lower = text.lower()
        return [kw for kw in keywords if kw in text_lower]

    def get_skill_gaps_for_role(self, skills: List[str], role_name: str) -> Dict:
        return {
            "role": role_name,
            "current_skills": skills,
            "gaps": [],
            "message": "Full taxonomy analysis not yet implemented.",
        }


tn_extractor = TNAutomotiveSkillExtractor()
