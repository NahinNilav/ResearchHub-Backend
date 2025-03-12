from typing import List, Dict, Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas, crud
from datetime import date
from .database import get_db
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend link 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DepartmentFunding(BaseModel):
    department: str
    funding: float

class AveragePublications(BaseModel):
    average: float

class InactiveProfessor(BaseModel):
    professor_id: int
    first_name: str
    last_name: str
    email: str
    title: Optional[str] = None
    department: Optional[str] = None
    research_areas: List[str] = []

class DepartmentCount(BaseModel):
    department: str
    professor_count: int

class EmailEntry(BaseModel):
    name: str
    email: str

class UnassignedStudent(BaseModel):
    student_id: int
    first_name: str
    last_name: str
    email: str
    enrollment_date: date
    type: str
    department: Optional[str] = None
    research_areas: List[str] = []

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    enrollment_date: Optional[date] = None
    type: Optional[str] = None
    image_url: Optional[str] = None
    advisor_id: Optional[int] = None
    department_id: Optional[int] = None

class YearlyTrends(BaseModel):
    projects: Dict[int, int]
    publications: Dict[int, int]

class DepartmentPublications(BaseModel):
    department: str
    publication_count: int

class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    enrollment_date: date
    type: str  # Change to 'PhD' or 'Masters' ENUM 
    image_url: Optional[str] = None
    advisor_id: Optional[int] = None
    department_id: Optional[int] = None
    research_areas: Optional[List[int]] = []  # List of ra IDs

class ProfessorCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    title: Optional[str] = None
    office: Optional[str] = None
    image_url: Optional[str] = None
    department_id: Optional[int] = None
    research_areas: List[int] = []

class ProfessorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    office: Optional[str] = None
    image_url: Optional[str] = None
    department_id: Optional[int] = None

class ProjectCreate(BaseModel):
    title: str
    start_date: date
    end_date: Optional[date] = None
    status: str
    funding_amount: Optional[float] = None
    funding_source: str
    description: Optional[str] = None
    lead_professor_id: int
    department_id: int

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    funding_amount: Optional[float] = None
    funding_source: Optional[str] = None
    description: Optional[str] = None
    lead_professor_id: Optional[int] = None
    department_id: Optional[int] = None

class PublicationCreate(BaseModel):
    title: str
    journal_id: int
    year: int
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    citations: Optional[int] = 0
    abstract: Optional[str] = None

class PublicationUpdate(BaseModel):
    title: Optional[str] = None
    journal_id: Optional[int] = None
    year: Optional[int] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    citations: Optional[int] = None
    abstract: Optional[str] = None

class ProfessorPublicationCount(BaseModel):
    professor_id: int
    first_name: str
    last_name: str
    publication_count: int
    department: Optional[str] = None

class SystemStats(BaseModel):
    total_students: int
    total_professors: int
    total_citations: int
    total_active_projects: int

class ProfessorWithoutPublications(BaseModel):
    professor_id: int
    first_name: str
    last_name: str
    email: str
    title: Optional[str] = None
    department: Optional[str] = None
    research_areas: List[str] = []

class DepartmentTotalFunding(BaseModel):
    department: str
    total_funding: float


# Professors 
@app.get("/professors/", response_model=List[schemas.ProfessorResponse])
def read_professors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    professors = crud.get_all_professors(db, skip=skip, limit=limit)
    return [format_professor_response(p) for p in professors]

@app.get("/professors/{professor_id}", response_model=schemas.ProfessorResponse)
def read_professor(professor_id: int, db: Session = Depends(get_db)):
    db_professor = crud.get_professor(db, professor_id=professor_id)
    if not db_professor:
        raise HTTPException(status_code=404, detail="Professor not found")
    return format_professor_response(db_professor)

def format_professor_response(professor: models.Professor):
    return schemas.ProfessorResponse(
        **professor.__dict__,
        department=professor.department.name if professor.department else None,
        research_areas=[area.name for area in professor.research_areas]
    )

@app.post("/professors/", response_model=schemas.ProfessorResponse)
def create_professor_endpoint(professor: ProfessorCreate, db: Session = Depends(get_db)):
    existing_professor = db.query(models.Professor).filter(
        models.Professor.email == professor.email
    ).first()
    if existing_professor:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if professor.department_id:
        department = db.query(models.Department).filter(
            models.Department.department_id == professor.department_id
        ).first()
        if not department:
            raise HTTPException(status_code=400, detail="Invalid department ID")

    try:
        professor_data = professor.dict(exclude={'research_areas'})
        db_professor = crud.create_professor(db, professor_data)
        
        if professor.research_areas:
            research_areas = (
                db.query(models.ResearchArea)
                .filter(models.ResearchArea.area_id.in_(professor.research_areas))
                .all()
            )
            db_professor.research_areas = research_areas
            db.commit()
            
        return format_professor_response(db_professor)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/professors/{professor_id}", response_model=schemas.ProfessorResponse)
def update_professor_endpoint(
    professor_id: int,
    professor: ProfessorUpdate,
    db: Session = Depends(get_db)
):
    db_professor = crud.get_professor(db, professor_id)
    if not db_professor:
        raise HTTPException(status_code=404, detail="Professor not found")
    
    updated_professor = crud.update_professor(db, professor_id, professor.dict(exclude_unset=True))
    return format_professor_response(updated_professor)

@app.delete("/professors/{professor_id}")
def delete_professor_endpoint(professor_id: int, db: Session = Depends(get_db)):
    if not crud.delete_professor(db, professor_id):
        raise HTTPException(status_code=404, detail="Professor not found")
    return {"message": "Professor deleted successfully"}


# Students 
@app.get("/students/", response_model=List[schemas.GradStudentResponse])
def read_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    students = crud.get_all_students(db, skip=skip, limit=limit)
    return [format_student_response(s) for s in students]

@app.get("/students/{student_id}", response_model=schemas.GradStudentResponse)
def read_student(student_id: int, db: Session = Depends(get_db)):
    db_student = crud.get_student(db, student_id=student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    return format_student_response(db_student)

def format_student_response(student: models.GradStudent):
    return schemas.GradStudentResponse(
        **student.__dict__,
        advisor=f"{student.advisor.first_name} {student.advisor.last_name}" if student.advisor else None,
        department=student.department.name if student.department else None,
        research_areas=[area.name for area in student.research_areas]
    )

@app.put("/students/{student_id}", response_model=schemas.GradStudentResponse)
def update_student_details(
    student_id: int,
    student: StudentUpdate,
    db: Session = Depends(get_db)
):
    """Update student details"""
    db_student = crud.update_student(db, student_id, student.dict(exclude_unset=True))
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    return format_student_response(db_student)

@app.delete("/students/{student_id}")
def delete_student_record(student_id: int, db: Session = Depends(get_db)):
    success = crud.delete_student(db, student_id)
    if not success:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deleted successfully"}

@app.post("/students/", response_model=schemas.GradStudentResponse)
def create_student_endpoint(
    student: StudentCreate,
    db: Session = Depends(get_db)
):
    existing_student = (
        db.query(models.GradStudent)
        .filter(models.GradStudent.email == student.email)
        .first()
    )
    if existing_student:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    if student.advisor_id:
        advisor = db.query(models.Professor).filter(
            models.Professor.professor_id == student.advisor_id
        ).first()
        if not advisor:
            raise HTTPException(
                status_code=400,
                detail="Invalid advisor ID"
            )
    
    if student.department_id:
        department = db.query(models.Department).filter(
            models.Department.department_id == student.department_id
        ).first()
        if not department:
            raise HTTPException(
                status_code=400,
                detail="Invalid department ID"
            )

    try:
        student_data = student.dict(exclude={'research_areas'})
        db_student = crud.create_student(db, student_data)
        
        if student.research_areas:
            research_areas = (
                db.query(models.ResearchArea)
                .filter(models.ResearchArea.area_id.in_(student.research_areas))
                .all()
            )
            db_student.research_areas = research_areas
            db.commit()
            
        return format_student_response(db_student)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

# Projects 
@app.get("/projects/", response_model=List[schemas.ProjectResponse])
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    projects = crud.get_all_projects(db, skip=skip, limit=limit)
    return [format_project_response(p) for p in projects]

@app.get("/projects/{project_id}", response_model=schemas.ProjectResponse)
def read_project(project_id: int, db: Session = Depends(get_db)):
    db_project = crud.get_project(db, project_id=project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return format_project_response(db_project)

def format_project_response(project: models.Project):
    professors = [
        schemas.Participant(
            name=f"{assoc.professor.first_name} {assoc.professor.last_name}",
            role=assoc.role
        )
        for assoc in project.professor_associations
    ]
    students = [
        schemas.Participant(
            name=f"{assoc.student.first_name} {assoc.student.last_name}",
            role=assoc.role
        )
        for assoc in project.student_associations
    ]
    return schemas.ProjectResponse(
        **project.__dict__,
        lead_professor=f"{project.lead_professor.first_name} {project.lead_professor.last_name}" if project.lead_professor else None,
        department=project.department.name if project.department else None,
        professors=professors,
        students=students
    )

@app.post("/projects/", response_model=schemas.ProjectResponse)
def create_project_endpoint(project: ProjectCreate, db: Session = Depends(get_db)):
    lead_professor = db.query(models.Professor).filter(
        models.Professor.professor_id == project.lead_professor_id
    ).first()
    if not lead_professor:
        raise HTTPException(status_code=400, detail="Invalid lead professor ID")
    
    department = db.query(models.Department).filter(
        models.Department.department_id == project.department_id
    ).first()
    if not department:
        raise HTTPException(status_code=400, detail="Invalid department ID")

    try:
        db_project = crud.create_project(db, project.dict())
        return format_project_response(db_project)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/projects/{project_id}", response_model=schemas.ProjectResponse)
def update_project_endpoint(
    project_id: int,
    project: ProjectUpdate,
    db: Session = Depends(get_db)
):
    db_project = crud.get_project(db, project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    updated_project = crud.update_project(db, project_id, project.dict(exclude_unset=True))
    return format_project_response(updated_project)

@app.delete("/projects/{project_id}")
def delete_project_endpoint(project_id: int, db: Session = Depends(get_db)):
    if not crud.delete_project(db, project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted successfully"}


# Publications 
@app.get("/publications/", response_model=List[schemas.PublicationResponse])
def read_publications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    publications = crud.get_all_publications(db, skip=skip, limit=limit)
    return [format_publication_response(p) for p in publications]

@app.get("/publications/{publication_id}", response_model=schemas.PublicationResponse)
def read_publication(publication_id: int, db: Session = Depends(get_db)):
    db_publication = crud.get_publication(db, publication_id=publication_id)
    if not db_publication:
        raise HTTPException(status_code=404, detail="Publication not found")
    return format_publication_response(db_publication)

def format_publication_response(publication: models.Publication):
    authors = []
    for pa in publication.professor_authors:
        authors.append(schemas.Author(
            name=f"{pa.professor.first_name} {pa.professor.last_name}",
            type="professor",
            order=pa.author_order
        ))
    for sa in publication.student_authors:
        authors.append(schemas.Author(
            name=f"{sa.student.first_name} {sa.student.last_name}",
            type="student",
            order=sa.author_order
        ))
    authors_sorted = sorted(authors, key=lambda x: x.order)
    return schemas.PublicationResponse(
        **publication.__dict__,
        journal=publication.journal.name if publication.journal else None,
        authors=authors_sorted
    )

@app.delete("/publications/{publication_id}")
def delete_publication_endpoint(publication_id: int, db: Session = Depends(get_db)):
    if not crud.delete_publication(db, publication_id):
        raise HTTPException(status_code=404, detail="Publication not found")
    return {"message": "Publication deleted successfully"}

@app.post("/publications/", response_model=schemas.PublicationResponse)
def create_publication_endpoint(publication: PublicationCreate, db: Session = Depends(get_db)):
    journal = db.query(models.Journal).filter(
        models.Journal.journal_id == publication.journal_id
    ).first()
    if not journal:
        raise HTTPException(status_code=400, detail="Invalid journal ID")

    try:
        db_publication = crud.create_publication(db, publication.dict())
        return format_publication_response(db_publication)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/publications/{publication_id}", response_model=schemas.PublicationResponse)
def update_publication_endpoint(
    publication_id: int,
    publication: PublicationUpdate,
    db: Session = Depends(get_db)
):
    db_publication = crud.get_publication(db, publication_id)
    if not db_publication:
        raise HTTPException(status_code=404, detail="Publication not found")
    
    updated_publication = crud.update_publication(db, publication_id, publication.dict(exclude_unset=True))
    return format_publication_response(updated_publication)


# Mixed 
@app.get("/analytics/department-funding/", response_model=List[DepartmentFunding])
def get_department_funding(db: Session = Depends(get_db)):
    results = crud.get_department_avg_funding(db)
    return [
        DepartmentFunding(department=dept, funding=float(avg))
        for dept, avg in results
    ]

@app.get("/analytics/departments-above-average/", response_model=List[DepartmentFunding])
def get_departments_above_average(db: Session = Depends(get_db)):
    results = crud.get_departments_above_avg_funding(db)
    return [
        DepartmentFunding(department=dept, funding=float(total))
        for dept, total in results
    ]

@app.get("/analytics/average-publications/", response_model=AveragePublications)
def get_average_publications(db: Session = Depends(get_db)):
    avg = crud.get_avg_publications_per_professor(db)
    return AveragePublications(average=avg)

@app.get("/analytics/inactive-professors/", response_model=List[InactiveProfessor])
def get_inactive_professors_endpoint(db: Session = Depends(get_db)):
    results = crud.get_inactive_professors(db)
    return [
        InactiveProfessor(
            professor_id=prof.professor_id,
            first_name=prof.first_name,
            last_name=prof.last_name,
            email=prof.email,
            title=prof.title,
            department=prof.department.name if prof.department else None,
            research_areas=[area.name for area in prof.research_areas]
        )
        for prof in results
    ]

@app.get("/analytics/small-departments/", response_model=List[DepartmentCount])
def get_small_departments_endpoint(db: Session = Depends(get_db)):
    """Get departments with less than 3 professors"""
    results = crud.get_small_departments(db)
    return [
        DepartmentCount(department=dept, professor_count=count)
        for dept, count in results
    ]

@app.get("/directory/emails/", response_model=List[EmailEntry])
def get_all_emails_endpoint(db: Session = Depends(get_db)):
    results = crud.get_all_emails(db)
    return [
        EmailEntry(name=name, email=email)
        for name, email in results
    ]

@app.get("/analytics/unassigned-students/", response_model=List[UnassignedStudent])
def get_unassigned_students(db: Session = Depends(get_db)):
    results = crud.get_students_without_projects(db)
    return [
        UnassignedStudent(
            student_id=student.student_id,
            first_name=student.first_name,
            last_name=student.last_name,
            email=student.email,
            enrollment_date=student.enrollment_date,
            type=student.type,
            department=student.department.name if student.department else None,
            research_areas=[area.name for area in student.research_areas]
        )
        for student in results
    ]

@app.get("/analytics/yearly-trends/", response_model=YearlyTrends)
def get_yearly_trends(db: Session = Depends(get_db)):
    return crud.get_yearly_trends(db)

@app.get("/analytics/department-publications/", response_model=List[DepartmentPublications])
def get_department_publications(db: Session = Depends(get_db)):
    results = crud.get_department_publications(db)
    return [
        DepartmentPublications(department=dept, publication_count=count)
        for dept, count in results
    ]

@app.get("/analytics/system-stats/", response_model=SystemStats)
def get_system_stats(db: Session = Depends(get_db)):
    return crud.get_system_stats(db)

@app.get("/analytics/department-total-funding/", response_model=List[DepartmentTotalFunding])
def get_department_total_funding(db: Session = Depends(get_db)):
    results = crud.get_department_total_funding(db)
    return [
        DepartmentTotalFunding(department=dept, total_funding=float(total))
        for dept, total in results
    ]

@app.get("/analytics/professors-without-publications/", response_model=List[ProfessorWithoutPublications])
def get_professors_without_publications(db: Session = Depends(get_db)):
    results = crud.get_professors_without_publications(db)
    return [
        ProfessorWithoutPublications(
            professor_id=prof.professor_id,
            first_name=prof.first_name,
            last_name=prof.last_name,
            email=prof.email,
            title=prof.title,
            department=prof.department.name if prof.department else None,
            research_areas=[area.name for area in prof.research_areas]
        )
        for prof in results
    ]

@app.get("/analytics/professor-publication-counts/", response_model=List[ProfessorPublicationCount])
def get_professor_publication_counts(db: Session = Depends(get_db)):
    results = crud.get_professor_publication_counts(db)
    return [
        ProfessorPublicationCount(
            professor_id=prof_id,
            first_name=first,
            last_name=last,
            publication_count=count,
            department=crud.get_professor(db, prof_id).department.name 
                if crud.get_professor(db, prof_id).department 
                else None
        )
        for prof_id, first, last, count in results
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)