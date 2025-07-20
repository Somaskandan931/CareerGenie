from pydantic import BaseModel
from typing import List

class ResumeForm(BaseModel):
    name: str
    email: str
    phone: str
    education: str
    experience: str
    skills: List[str]
