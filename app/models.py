from sqlalchemy import Column, Integer, String, ForeignKey, Date, Numeric, Enum, Text, Table
from sqlalchemy.orm import relationship, declarative_base
from .database import Base

# Junction tables
professor_research_areas = Table(
    'professor_research_areas',
    Base.metadata,
    Column('professor_id', Integer, ForeignKey('professor.professor_id'), primary_key=True),
    Column('area_id', Integer, ForeignKey('research_area.area_id'), primary_key=True)
)

student_research_areas = Table(
    'student_research_areas',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('gradstudent.student_id'), primary_key=True),
    Column('area_id', Integer, ForeignKey('research_area.area_id'), primary_key=True)
)

class Department(Base):
    __tablename__ = 'department'
    department_id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

class ResearchArea(Base):
    __tablename__ = 'research_area'
    area_id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

class Professor(Base):
    __tablename__ = 'professor'
    professor_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    title = Column(String(50))
    office = Column(String(50))
    image_url = Column(String(200))
    department_id = Column(Integer, ForeignKey('department.department_id'))
    department = relationship("Department")
    research_areas = relationship("ResearchArea", secondary=professor_research_areas)
    project_associations = relationship("ProfessorProject", back_populates="professor")

class GradStudent(Base):
    __tablename__ = 'gradstudent'
    student_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    enrollment_date = Column(Date, nullable=False)
    type = Column(String(20))
    image_url = Column(String(200))
    advisor_id = Column(Integer, ForeignKey('professor.professor_id'))
    advisor = relationship("Professor")
    department_id = Column(Integer, ForeignKey('department.department_id'))
    department = relationship("Department")
    research_areas = relationship("ResearchArea", secondary=student_research_areas)
    project_associations = relationship("StudentProject", back_populates="student")

class Project(Base):
    __tablename__ = 'project'
    project_id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    status = Column(Enum('Active', 'Completed', name='project_status'))
    funding_amount = Column(Numeric(10,2))
    funding_source = Column(String(100), nullable=False)
    description = Column(Text)
    lead_professor_id = Column(Integer, ForeignKey('professor.professor_id'))
    lead_professor = relationship("Professor")
    department_id = Column(Integer, ForeignKey('department.department_id'))
    department = relationship("Department")
    professor_associations = relationship("ProfessorProject", back_populates="project")
    student_associations = relationship("StudentProject", back_populates="project")
    professors = relationship("Professor", secondary="professor_project", viewonly=True)
    students = relationship("GradStudent", secondary="student_project", viewonly=True)

class Journal(Base):
    __tablename__ = 'journal'
    journal_id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

class Publication(Base):
    __tablename__ = 'publication'
    publication_id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    journal_id = Column(Integer, ForeignKey('journal.journal_id'))
    journal = relationship("Journal")
    year = Column(Integer, nullable=False)
    volume = Column(String(20))
    issue = Column(String(20))
    pages = Column(String(20))
    citations = Column(Integer, default=0)
    abstract = Column(Text)
    professor_authors = relationship("ProfessorAuthor", back_populates="publication")
    student_authors = relationship("StudentAuthor", back_populates="publication")

class ProfessorAuthor(Base):
    __tablename__ = 'professor_authors'
    publication_id = Column(Integer, ForeignKey('publication.publication_id'), primary_key=True)
    professor_id = Column(Integer, ForeignKey('professor.professor_id'), primary_key=True)
    author_order = Column(Integer, nullable=False)
    professor = relationship("Professor")
    publication = relationship("Publication", back_populates="professor_authors")

class StudentAuthor(Base):
    __tablename__ = 'student_authors'
    publication_id = Column(Integer, ForeignKey('publication.publication_id'), primary_key=True)
    student_id = Column(Integer, ForeignKey('gradstudent.student_id'), primary_key=True)
    author_order = Column(Integer, nullable=False)
    student = relationship("GradStudent")
    publication = relationship("Publication", back_populates="student_authors")

class ProfessorProject(Base):
    __tablename__ = 'professor_project'
    project_id = Column(Integer, ForeignKey('project.project_id'), primary_key=True)
    professor_id = Column(Integer, ForeignKey('professor.professor_id'), primary_key=True)
    role = Column(String(50))
    professor = relationship("Professor", back_populates="project_associations")
    project = relationship("Project", back_populates="professor_associations")

class StudentProject(Base):
    __tablename__ = 'student_project'
    project_id = Column(Integer, ForeignKey('project.project_id'), primary_key=True)
    student_id = Column(Integer, ForeignKey('gradstudent.student_id'), primary_key=True)
    role = Column(String(50))
    student = relationship("GradStudent", back_populates="project_associations")
    project = relationship("Project", back_populates="student_associations")