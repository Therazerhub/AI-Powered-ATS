# Database Diagram

This document reflects the models currently defined in `recruitment/models.py`. The project uses SQLite through Django's ORM and Django's built-in `auth.User` model.

## Entity-relationship diagram

```mermaid
erDiagram
    USER {
        int id PK
        string username UK
        string first_name
        string last_name
        string email
        string password
        boolean is_staff
        boolean is_active
    }

    CANDIDATE_PROFILE {
        int id PK
        int user_id FK_UK
        string phone
        text education
        text experience
        text projects
        text certifications
        string location
        datetime created_at
    }

    RECRUITER_PROFILE {
        int id PK
        int user_id FK_UK
        string job_title
        string department
    }

    SKILL {
        int id PK
        string name UK
    }

    RESUME {
        int id PK
        int candidate_id FK
        string file
        string original_name
        text extracted_text
        boolean is_active
        datetime uploaded_at
    }

    JOB {
        int id PK
        string title
        string department
        text description
        string required_experience
        string education_requirement
        string location
        string employment_type
        string salary_range
        date application_deadline
        string status
        int created_by_id FK
        datetime created_at
        datetime updated_at
    }

    APPLICATION {
        int id PK
        int candidate_id FK
        int job_id FK
        int resume_id FK
        text cover_letter
        string status
        smallint ai_match_score
        json ai_analysis
        text recruiter_notes
        datetime applied_at
        datetime updated_at
    }

    AI_ANALYSIS {
        int id PK
        int application_id FK_UK
        smallint match_score
        json matching_skills
        json missing_skills
        text relevant_experience
        json relevant_projects
        json strengths
        json concerns
        text explanation
        string provider
        string model_name
        datetime created_at
    }

    RECRUITER_NOTE {
        int id PK
        int application_id FK
        int author_id FK
        text text
        datetime created_at
    }

    INTERVIEW {
        int id PK
        int application_id FK_UK
        datetime scheduled_at
        string mode
        string location_or_link
        text notes
        int updated_by_id FK
        datetime updated_at
    }

    USER ||--o| CANDIDATE_PROFILE : "has candidate role"
    USER ||--o| RECRUITER_PROFILE : "has recruiter role"
    USER ||--o{ JOB : "creates"
    USER ||--o{ RECRUITER_NOTE : "authors"
    USER ||--o{ INTERVIEW : "updates"

    CANDIDATE_PROFILE }o--o{ SKILL : "has"
    JOB }o--o{ SKILL : "requires"
    JOB }o--o{ SKILL : "prefers"

    CANDIDATE_PROFILE ||--o{ RESUME : "uploads"
    CANDIDATE_PROFILE ||--o{ APPLICATION : "submits"
    JOB ||--o{ APPLICATION : "receives"
    RESUME ||--o{ APPLICATION : "is selected for"

    APPLICATION ||--o| AI_ANALYSIS : "has latest structured analysis"
    APPLICATION ||--o{ RECRUITER_NOTE : "has"
    APPLICATION ||--o| INTERVIEW : "has"
```

`FK_UK` indicates a foreign key that is also unique, which is how Django implements a `OneToOneField`.

## Relationship summary

| Parent | Child/related model | Relationship | Meaning |
|---|---|---|---|
| `User` | `CandidateProfile` | One-to-zero-or-one | A user may have one candidate profile. |
| `User` | `RecruiterProfile` | One-to-zero-or-one | A user may have one recruiter profile. Staff users are also treated as recruiters by the authorization code. |
| `CandidateProfile` | `Skill` | Many-to-many | A candidate may list many skills, and a skill may belong to many candidates. |
| `CandidateProfile` | `Resume` | One-to-many | A candidate may upload multiple resumes; `is_active` marks the current one. |
| `User` | `Job` | One-to-many | `Job.created_by` records the recruiter/staff user who created the job. |
| `Job` | `Skill` | Two many-to-many relations | Required and preferred skills are stored separately. |
| `CandidateProfile` | `Application` | One-to-many | A candidate can submit applications to different jobs. |
| `Job` | `Application` | One-to-many | A job can receive many applications. |
| `Resume` | `Application` | One-to-many | One uploaded resume may be selected for multiple applications. |
| `Application` | `AIAnalysis` | One-to-zero-or-one | Each application has at most one current structured analysis record. |
| `Application` | `RecruiterNote` | One-to-many | The schema supports multiple timestamped notes and authors. |
| `Application` | `Interview` | One-to-zero-or-one | Each application has at most one current interview schedule. |

## Django-generated many-to-many tables

The Mermaid diagram shows many-to-many links directly for readability. Django creates intermediate tables for these fields:

- `CandidateProfile.skills`
- `Job.required_skills`
- `Job.preferred_skills`

Each intermediate row stores the IDs of the two related records. These tables are managed automatically by the Django ORM because the project does not define custom `through` models.

## Key constraints and validation

### Application uniqueness

`Application` defines this database constraint:

```python
models.UniqueConstraint(
    fields=["candidate", "job"],
    name="unique_candidate_job_application",
)
```

A candidate therefore cannot apply to the same job twice, even if two requests reach the server at nearly the same time.

### Score range

Both `Application.ai_match_score` and `AIAnalysis.match_score` use validators for a range of 0–100. The service also clamps an OpenRouter score into that range before saving it.

### Skill uniqueness

`Skill.name` is unique. Form code uses a case-insensitive lookup before creating a skill, then normalizes newly created names with title case.

### Resume validation

- `Resume.file` has a model-level PDF extension validator.
- `ResumeForm` also checks for a `.pdf` filename and a maximum size of 5 MB.
- Extracted text is stored in the database; the physical PDF path is stored by the `FileField`.

### Choice fields

- Job status: `draft`, `open`, `closed`
- Employment type: `full_time`, `part_time`, `contract`, `internship`
- Application status: `applied`, `under_review`, `shortlisted`, `interview`, `selected`, `rejected`
- Interview mode: `online`, `onsite`, `phone`

## Delete behavior

| Foreign key | Django behavior | Effect |
|---|---|---|
| Profile → `User` | `CASCADE` | Deleting a user deletes their candidate/recruiter profile. |
| Resume → `CandidateProfile` | `CASCADE` | Deleting a candidate profile deletes its resume database rows. |
| Application → candidate/job | `CASCADE` | Deleting the candidate or job deletes related applications. |
| Application → `Resume` | `PROTECT` | A resume cannot be deleted while an application references it. |
| Job → creator | `PROTECT` | A user cannot be deleted while they are recorded as a job creator. |
| AI analysis → application | `CASCADE` | Deleting an application deletes its structured analysis. |
| Recruiter note → application | `CASCADE` | Deleting an application deletes its notes. |
| Recruiter note → author | `PROTECT` | A note author cannot be deleted while their note remains. |
| Interview → application | `CASCADE` | Deleting an application deletes its interview. |
| Interview → updater | `PROTECT` | The updating user cannot be deleted while the interview remains. |

## Important implementation notes

- `Application.ai_analysis` stores the complete latest response as JSON for convenient display, while `AIAnalysis` stores the same analysis in typed/structured fields plus provider and model metadata.
- `AIAnalysis.created_at` uses `auto_now=True`; it represents the most recent update time when analysis is regenerated.
- `Resume.is_active` is maintained by the profile-edit workflow: previous resumes are marked inactive before a newly uploaded resume is saved. There is no database constraint limiting a candidate to one active resume.
- `RecruiterNote` supports separate note records, but the current application review form primarily edits `Application.recruiter_notes`.
- Django also creates framework tables for users, groups, permissions, sessions, migrations, and admin logs. They are omitted from the diagram except for `USER`, which directly participates in application relationships.
