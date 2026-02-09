# ResearchHub Backend 


## Overview
Backend service for a research directory platform that manages professors, graduate students, projects, publications, and department analytics. It models faculty, students, research areas, authorship, and projects, and exposes analytics endpoints for funding, publication trends, and staffing insights.

---

## Domain Model
Core entities:
- **Departments**
- **Professors**
- **Graduate Students**
- **Research Areas**
- **Projects**
- **Journals**
- **Publications**

Relationships:
- Professors ↔ Research Areas (many‑to‑many)
- Students ↔ Research Areas (many‑to‑many)
- Publications ↔ Authors (ordered, professor + student)
- Projects ↔ Participants (professors + students with roles)

---

## API Capabilities

### Professors
- Create, update, delete, list
- Department validation
- Enriched responses with research areas and department name

### Students
- Create, update, delete, list
- Advisor and department validation
- Enriched responses with advisor + research areas

### Projects
- Full CRUD
- Participant roles included in responses

### Publications
- Full CRUD
- Ordered mixed author list (professor + student)
- Journal validation

---

## Analytics Endpoints

- **Average funding per department**
- **Departments above average funding**
- **Average publications per professor**
- **Inactive professors** (no active projects)
- **Small departments** (< 3 professors)
- **Unified email directory** (professors + students)
- **Unassigned students** (no advisor and no project)
- **Yearly trends** (completed projects vs publications)
- **Department publication counts**
- **Department total funding**
- **Professors without publications**
- **Professor publication leaderboard**

---

## Query Patterns Used
- Aggregations (`AVG`, `SUM`, `COUNT`)
- Subqueries and CTEs
- Outer joins for inclusive counts
- Union queries for directory views

---

## Project Structure
```
app/
  main.py        # FastAPI routes + response shaping
  crud.py        # SQLAlchemy queries & analytics
  models.py      # ORM models + junction tables
  database.py    # DB engine + session
  schemas.py     # Pydantic response models
```

---

## Tech Stack
- **FastAPI**
- **SQLAlchemy**
- **PostgreSQL**
- **Pydantic**
- **Python 3.x**
