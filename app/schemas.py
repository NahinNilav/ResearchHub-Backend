from typing import List, Optional
from pydantic import BaseModel
from datetime import date

class DepartmentBase(BaseModel):
    name: str

class ResearchAreaBase(BaseModel):
    name: str

class ProfessorBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    title: Optional[str] = None
    office: Optional[str] = None
    image_url: Optional[str] = None
    department_id: Optional[int] = None

class ProfessorResponse(ProfessorBase):
    professor_id: int
    department: Optional[str] = None
    research_areas: List[str] = []

    class Config:
        orm_mode = True

class GradStudentBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    enrollment_date: date
    type: str
    image_url: Optional[str] = None
    advisor_id: Optional[int] = None
    department_id: Optional[int] = None

class GradStudentResponse(GradStudentBase):
    student_id: int
    advisor: Optional[str] = None
    department: Optional[str] = None
    research_areas: List[str] = []

    class Config:
        orm_mode = True

class ProjectBase(BaseModel):
    title: str
    start_date: date
    end_date: Optional[date] = None
    status: str
    funding_amount: Optional[float] = None
    funding_source: str
    description: Optional[str] = None
    lead_professor_id: Optional[int] = None
    department_id: Optional[int] = None

class Participant(BaseModel):
    name: str
    role: Optional[str] = None

class ProjectResponse(ProjectBase):
    project_id: int
    lead_professor: Optional[str] = None
    department: Optional[str] = None
    professors: List[Participant] = []
    students: List[Participant] = []

    class Config:
        orm_mode = True

class PublicationBase(BaseModel):
    title: str
    journal_id: Optional[int] = None
    year: int
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    citations: Optional[int] = 0
    abstract: Optional[str] = None

class Author(BaseModel):
    name: str
    type: str
    order: int

class PublicationResponse(PublicationBase):
    publication_id: int
    journal: Optional[str] = None
    authors: List[Author] = []

    class Config:
        orm_mode = True