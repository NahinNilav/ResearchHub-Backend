from sqlalchemy.orm import Session
from sqlalchemy import func, select
from sqlalchemy.sql import text
from typing import List, Tuple
from . import models

def get_professor(db: Session, professor_id: int):
    return db.query(models.Professor).filter(models.Professor.professor_id == professor_id).first()

def get_all_professors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Professor).offset(skip).limit(limit).all()

def get_student(db: Session, student_id: int):
    return db.query(models.GradStudent).filter(models.GradStudent.student_id == student_id).first()

def get_all_students(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.GradStudent).offset(skip).limit(limit).all()

def get_project(db: Session, project_id: int):
    return db.query(models.Project).filter(models.Project.project_id == project_id).first()

def get_all_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).offset(skip).limit(limit).all()

def get_publication(db: Session, publication_id: int):
    return db.query(models.Publication).filter(models.Publication.publication_id == publication_id).first()

def get_all_publications(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Publication).offset(skip).limit(limit).all()

def get_department_avg_funding(db: Session) -> List[Tuple[str, float]]:
    query = (
        db.query(
            models.Department.name,
            func.round(func.avg(models.Project.funding_amount), 2).label('avg_funding')
        )
        .join(models.Project)
        .group_by(models.Department.department_id)
    )
    return query.all()

def get_departments_above_avg_funding(db: Session) -> List[Tuple[str, float]]:
    dept_funding = (
        select(
            models.Project.department_id,
            func.sum(models.Project.funding_amount).label('total_funding')
        )
        .group_by(models.Project.department_id)
        .cte('dept_funding')
    )
    
    avg_total_funding = (
        select(func.avg(dept_funding.c.total_funding))
        .scalar_subquery()
    )
    
    query = (
        db.query(
            models.Department.name,
            dept_funding.c.total_funding
        )
        .join(dept_funding, models.Department.department_id == dept_funding.c.department_id)
        .filter(dept_funding.c.total_funding > avg_total_funding)
    )
    return query.all()

def get_avg_publications_per_professor(db: Session) -> float:
    prof_pubs = (
        db.query(
            models.ProfessorAuthor.professor_id,
            func.count().label('pub_count')
        )
        .group_by(models.ProfessorAuthor.professor_id)
        .subquery()
    )
    
    result = db.query(
        func.round(func.avg(prof_pubs.c.pub_count), 2)
    ).scalar()
    
    return float(result) if result is not None else 0.0

def get_inactive_professors(db: Session) -> List[models.Professor]:
    subquery = (
        db.query(models.Professor.professor_id)
        .join(models.Project, models.Professor.professor_id == models.Project.lead_professor_id)
        .filter(models.Project.status == 'Active')
        .subquery()
    )
    
    query = (
        db.query(models.Professor)
        .filter(~models.Professor.professor_id.in_(subquery))
    )
    return query.all()

def get_small_departments(db: Session) -> List[Tuple[str, int]]:
    query = (
        db.query(
            models.Department.name,
            func.count(models.Professor.professor_id).label('num_professors')
        )
        .join(models.Professor)
        .group_by(models.Department.department_id)
        .having(func.count(models.Professor.professor_id) < 3)
    )
    return query.all()

def get_all_emails(db: Session) -> List[Tuple[str, str]]:

    professors = (
        db.query(
            (func.concat(
                models.Professor.first_name, 
                ' ', 
                models.Professor.last_name, 
                ' (Professor)'
            )).label('name'),
            models.Professor.email
        )
    )
    
    students = (
        db.query(
            (func.concat(
                models.GradStudent.first_name, 
                ' ', 
                models.GradStudent.last_name, 
                ' (Student)'
            )).label('name'),
            models.GradStudent.email
        )
    )
    
    query = professors.union(students)
    return query.all()

def get_students_without_projects(db: Session) -> List[models.GradStudent]:
    subquery = (
        db.query(models.StudentProject.student_id)
        .distinct()
        .subquery()
    )
    
    query = (
        db.query(models.GradStudent)
        .filter(
            ~models.GradStudent.student_id.in_(subquery),
            models.GradStudent.advisor_id.is_(None)
        )
    )
    return query.all()

def update_student(db: Session, student_id: int, student_data: dict):
    db_student = db.query(models.GradStudent).filter(
        models.GradStudent.student_id == student_id
    ).first()
    
    if db_student:
        for key, value in student_data.items():
            setattr(db_student, key, value)
        db.commit()
        db.refresh(db_student)
    return db_student

def delete_student(db: Session, student_id: int) -> bool:
    db_student = db.query(models.GradStudent).filter(
        models.GradStudent.student_id == student_id
    ).first()
    if db_student:
        db.delete(db_student)
        db.commit()
        return True
    return False

def get_publications_by_citations(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Publication)
        .order_by(models.Publication.citations.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_yearly_trends(db: Session) -> dict:
    project_trends = (
        db.query(
            func.extract('year', models.Project.end_date).label('year'),
            func.count().label('count')
        )
        .filter(models.Project.status == 'Completed')
        .group_by(func.extract('year', models.Project.end_date))
        .all()
    )
    
    publication_trends = (
        db.query(
            models.Publication.year,
            func.count().label('count')
        )
        .group_by(models.Publication.year)
        .all()
    )
    
    return {
        'projects': {year: count for year, count in project_trends},
        'publications': {year: count for year, count in publication_trends}
    }

def get_department_publications(db: Session) -> List[Tuple[str, int]]:
    prof_pubs = (
        db.query(
            models.Department.name,
            func.count(models.Publication.publication_id).label('pub_count')
        )
        .join(models.Professor, models.Professor.department_id == models.Department.department_id)
        .join(models.ProfessorAuthor, models.ProfessorAuthor.professor_id == models.Professor.professor_id)
        .join(models.Publication, models.Publication.publication_id == models.ProfessorAuthor.publication_id)
        .group_by(models.Department.department_id, models.Department.name)
    )
    
    return prof_pubs.all()

def create_student(db: Session, student_data: dict) -> models.GradStudent:
    db_student = models.GradStudent(**student_data)
    db.add(db_student)
    try:
        db.commit()
        db.refresh(db_student)
        return db_student
    except Exception as e:
        db.rollback()
        raise e

def get_system_stats(db: Session) -> dict:
    total_students = db.query(func.count(models.GradStudent.student_id)).scalar()
    
    total_professors = db.query(func.count(models.Professor.professor_id)).scalar()
    
    total_citations = db.query(func.sum(models.Publication.citations)).scalar() or 0
    
    total_active_projects = (
        db.query(func.count(models.Project.project_id))
        .filter(models.Project.status == 'Active')
        .scalar()
    )
    
    return {
        "total_students": total_students,
        "total_professors": total_professors,
        "total_citations": total_citations,
        "total_active_projects": total_active_projects
    }

def get_department_total_funding(db: Session) -> List[Tuple[str, float]]:
    query = (
        db.query(
            models.Department.name,
            func.round(func.sum(models.Project.funding_amount), 2).label('total_funding')
        )
        .join(models.Project)
        .group_by(models.Department.department_id, models.Department.name)
        .order_by(func.sum(models.Project.funding_amount).desc())
    )
    return query.all()

def get_professors_without_publications(db: Session) -> List[models.Professor]:
    subquery = (
        db.query(models.ProfessorAuthor.professor_id)
        .distinct()
        .subquery()
    )
    
    query = (
        db.query(models.Professor)
        .filter(~models.Professor.professor_id.in_(subquery))
    )
    return query.all()

def get_professor_publication_counts(db: Session) -> List[Tuple[int, str, str, int]]:
    subquery = (
        db.query(
            models.ProfessorAuthor.professor_id,
            func.count().label('pub_count')
        )
        .group_by(models.ProfessorAuthor.professor_id)
        .subquery()
    )
    
    query = (
        db.query(
            models.Professor.professor_id,
            models.Professor.first_name,
            models.Professor.last_name,
            func.coalesce(subquery.c.pub_count, 0).label('publication_count')
        )
        .outerjoin(subquery, models.Professor.professor_id == subquery.c.professor_id)
        .order_by(func.coalesce(subquery.c.pub_count, 0).desc())
    )
    
    return query.all()

def create_professor(db: Session, professor_data: dict) -> models.Professor:
    db_professor = models.Professor(**professor_data)
    db.add(db_professor)
    try:
        db.commit()
        db.refresh(db_professor)
        return db_professor
    except Exception as e:
        db.rollback()
        raise e

def update_professor(db: Session, professor_id: int, professor_data: dict):
    db_professor = db.query(models.Professor).filter(
        models.Professor.professor_id == professor_id
    ).first()
    
    if db_professor:
        for key, value in professor_data.items():
            setattr(db_professor, key, value)
        db.commit()
        db.refresh(db_professor)
    return db_professor

def delete_professor(db: Session, professor_id: int) -> bool:
    db_professor = db.query(models.Professor).filter(
        models.Professor.professor_id == professor_id
    ).first()
    if db_professor:
        db.delete(db_professor)
        db.commit()
        return True
    return False

def create_project(db: Session, project_data: dict) -> models.Project:
    db_project = models.Project(**project_data)
    db.add(db_project)
    try:
        db.commit()
        db.refresh(db_project)
        return db_project
    except Exception as e:
        db.rollback()
        raise e

def update_project(db: Session, project_id: int, project_data: dict):
    db_project = db.query(models.Project).filter(
        models.Project.project_id == project_id
    ).first()
    
    if db_project:
        for key, value in project_data.items():
            setattr(db_project, key, value)
        db.commit()
        db.refresh(db_project)
    return db_project

def delete_project(db: Session, project_id: int) -> bool:
    db_project = db.query(models.Project).filter(
        models.Project.project_id == project_id
    ).first()
    if db_project:
        db.delete(db_project)
        db.commit()
        return True
    return False

def create_publication(db: Session, publication_data: dict) -> models.Publication:
    db_publication = models.Publication(**publication_data)
    db.add(db_publication)
    try:
        db.commit()
        db.refresh(db_publication)
        return db_publication
    except Exception as e:
        db.rollback()
        raise e

def update_publication(db: Session, publication_id: int, publication_data: dict):
    db_publication = db.query(models.Publication).filter(
        models.Publication.publication_id == publication_id
    ).first()
    
    if db_publication:
        for key, value in publication_data.items():
            setattr(db_publication, key, value)
        db.commit()
        db.refresh(db_publication)
    return db_publication

def delete_publication(db: Session, publication_id: int) -> bool:
    db_publication = db.query(models.Publication).filter(
        models.Publication.publication_id == publication_id
    ).first()
    if db_publication:
        db.delete(db_publication)
        db.commit()
        return True
    return False