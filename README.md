# AI-Powered Applicant Tracking System (ATS)

A beginner-friendly Django web application for managing jobs, candidate profiles, resumes, applications, interviews, and an AI-assisted candidate-to-job comparison. The application uses the real OpenRouter Chat Completions API from Django's server side and stores structured analysis results for recruiter review.

> **Important:** The AI score is advisory. It is not an automatic hiring decision and should always be reviewed by a person.

## Documentation

- [Database diagram](DATABASE_DIAGRAM.md)
- [Architecture and data-flow diagrams](ARCHITECTURE_DIAGRAM.md)

## Problem statement

Recruiters often receive many applications and need one place to publish jobs, track each applicant, review qualifications, and move candidates through a hiring pipeline. Manual comparison is repetitive, while unreviewed automated ranking can be opaque or unfair.

This project addresses that problem with a simple role-based ATS. It keeps the recruitment workflow in Django and uses AI only to summarize job-related evidence such as skills, education, experience, projects, certifications, and resume text.

## Objectives

1. Give candidates a clear workflow to create a profile, upload a PDF resume, browse jobs, and apply.
2. Give recruiters tools to create jobs, view candidates, update application statuses, and schedule interviews.
3. Compare an application against a job through a real server-side OpenRouter request.
4. Require the AI to return structured JSON that the application can validate and display consistently.
5. Keep the model output explainable by showing matching skills, missing skills, strengths, concerns, relevant experience, projects, and a short explanation.
6. Protect recruiter actions with authentication, role checks, CSRF protection, and POST-only state-changing endpoints.
7. Demonstrate responsible use of AI: protected traits are excluded from the prompt, and final decisions remain with human recruiters.

## Main features

### Candidate features

- Register and sign in with Django authentication.
- Edit contact and professional profile information.
- Add comma-separated skills.
- Upload PDF resumes up to 5 MB.
- Extract resume text with `pypdf` and retain one active resume at a time.
- Browse and search currently open jobs by title, department, or location.
- Apply with a selected resume and optional cover letter.
- View submitted applications and their current statuses.
- Prevent duplicate applications to the same job at both view and database levels.

### Recruiter features

- Role-protected recruiter dashboard with application and pipeline statistics.
- Create, edit, and delete job postings.
- Define required and preferred skills.
- Search candidates by name, email, or skill.
- Add a candidate and optional resume from the recruiter interface.
- View candidates for each job ordered by AI score and application date.
- Review an application, maintain recruiter notes, and change its status.
- Schedule or update online, on-site, or phone interviews.
- View the full pipeline from Applied through Selected or Rejected.
- Trigger live AI analysis for an application.

### AI analysis output

The analysis returns and stores:

- Match score from 0 to 100
- Matching skills
- Missing skills
- Relevant experience
- Relevant projects
- Strengths
- Job-related concerns
- A short explanation
- Provider and model metadata in the dedicated `AIAnalysis` record

## Tech stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python, Django 5.2 | URL routing, views, forms, authentication, ORM, templates |
| Database | SQLite | Local relational data storage |
| Frontend | Django templates, Bootstrap 5.3, Bootstrap Icons, custom CSS | Server-rendered user interface |
| AI provider | OpenRouter Chat Completions API | Candidate-to-job analysis |
| HTTP client | Requests | Server-side OpenRouter request |
| Resume processing | pypdf | PDF text extraction |
| Configuration | python-dotenv | Loading local `.env` settings |
| Tests | Django `TestCase`, `unittest.mock` | Workflow and AI response tests |
| Optional presentation dependency | python-pptx, Pillow | Included in project requirements |

## How the system works

1. A candidate registers. `CandidateRegistrationForm` creates both a Django `User` and a `CandidateProfile`.
2. The candidate enters structured profile data and uploads a PDF. The file is stored under `media/resumes/<year>/<month>/`, and extracted text is saved in `Resume.extracted_text`.
3. A recruiter creates a job with required and preferred skills.
4. The candidate applies using one of their resumes. An `Application` links the candidate, job, and selected resume.
5. A recruiter clicks the AI analysis action on the application page.
6. Django builds an anonymized, job-related payload and sends it to OpenRouter from `recruitment/services.py`.
7. The model returns structured JSON. Django validates the required keys, clamps the score to 0–100, and normalizes list fields.
8. The result is stored both as summary fields on `Application` and as a structured `AIAnalysis` record.
9. The recruiter reviews the evidence and makes the human decision to update status or schedule an interview.

See [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) for the complete request and AI flows.

## Project structure and important files

```text
ai-powered-ats/
├── manage.py                         # Django command entry point
├── requirements.txt                 # Pinned Python dependencies
├── .env.example                     # Safe configuration template
├── ats_project/
│   ├── settings.py                  # Database, templates, media, auth, OpenRouter settings
│   ├── urls.py                      # Admin, login/logout, and app URL entry points
│   ├── asgi.py                      # ASGI entry point
│   └── wsgi.py                      # WSGI entry point
├── recruitment/
│   ├── models.py                    # ATS database models and relationships
│   ├── forms.py                     # Registration, profile, job, application, and interview forms
│   ├── views.py                     # Candidate/recruiter workflows and AI action
│   ├── urls.py                      # Application routes
│   ├── services.py                  # PDF extraction and OpenRouter integration
│   ├── decorators.py                # Candidate/recruiter authorization checks
│   ├── context_processors.py        # Role flags for templates
│   ├── tests.py                     # Automated workflow and AI parsing tests
│   ├── admin.py                     # Django admin registrations
│   ├── migrations/                  # Database schema migrations
│   └── management/commands/
│       └── seed_demo.py             # Repeatable demo-data command
├── templates/                       # Django HTML templates
│   ├── base.html
│   ├── registration/
│   └── recruitment/
├── static/
│   ├── css/app.css                  # Application styling
│   └── js/app.js                    # Frontend behavior
├── media/                           # Uploaded resumes at runtime; ignored by Git
├── DATABASE_DIAGRAM.md              # Entity relationship documentation
└── ARCHITECTURE_DIAGRAM.md          # System and AI data-flow documentation
```

## Local setup

### Prerequisites

- Python 3.11 or newer
- `pip`
- An OpenRouter API key if you want to run live AI analysis

SQLite is included with Python, so a separate database server is not required.

### 1. Enter the project directory

```bash
cd /home/ubuntu/ai-powered-ats
```

If the project is copied elsewhere, use that path instead.

### 2. Create and activate a virtual environment

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create local environment configuration

Linux/macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Open `.env`, replace the development secret, and add an OpenRouter API key for live AI analysis. Never commit `.env`.

A random Django secret can be generated with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Create the database tables

```bash
python manage.py migrate
```

### 6. Load the demo accounts and sample data

```bash
python manage.py seed_demo
```

The command is safe to run again: it reuses existing demo users, skills, and jobs where possible, and resets the demo passwords to the documented values.

### 7. Start the development server

```bash
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. Django admin is available at <http://127.0.0.1:8000/admin/> for a suitable staff/superuser account.

## Environment variables

Settings are loaded from `.env` by `python-dotenv`. Real process environment variables can also supply these values.

| Variable | Required? | Default | Description |
|---|---:|---|---|
| `DJANGO_SECRET_KEY` | Required for secure deployment | Insecure development-only fallback | Signs sessions and other Django security data. Use a long random value. |
| `DEBUG` | No | `True` | Enables Django debug mode. Set to `False` outside local development. |
| `ALLOWED_HOSTS` | Required outside localhost | `127.0.0.1,localhost` | Comma-separated hostnames accepted by Django. |
| `CSRF_TRUSTED_ORIGINS` | Only for relevant HTTPS/proxy deployments | Empty | Comma-separated origins including scheme, for example `https://ats.example.com`. |
| `OPENROUTER_API_KEY` | Required for live AI analysis | Empty | Secret OpenRouter token used only by the Django server. |
| `OPENROUTER_MODEL` | No | `cohere/north-mini-code:free` | OpenRouter model identifier used for analysis. Availability can change on OpenRouter. |

Example local `.env`:

```dotenv
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=
OPENROUTER_API_KEY=replace-with-your-openrouter-key
OPENROUTER_MODEL=cohere/north-mini-code:free
```

## Demo credentials

Run `python manage.py seed_demo` before using these accounts.

| Role | Username | Password |
|---|---|---|
| Recruiter | `recruiter` | `HR@123` |
| Candidate | `candidate` | `Candidate@123` |

A second sample candidate, `candidate2`, is also seeded with password `Candidate@123`.

These credentials are for local demonstration only. Change or remove them before any shared or public deployment.

## Real OpenRouter API integration

The integration is implemented in `recruitment/services.py`; it is not a simulated score.

### Request path

- A recruiter submits `POST /hr/applications/<id>/analyze/`.
- The view is protected by `@recruiter_required` and `@require_POST`.
- `analyze_application_with_ai()` loads resume text if necessary.
- Django sends `POST https://openrouter.ai/api/v1/chat/completions` with:
  - Bearer authentication from `OPENROUTER_API_KEY`
  - The configured `OPENROUTER_MODEL`
  - A low temperature of `0.1`
  - A 90-second timeout
  - `response_format: {"type": "json_object"}`
  - A system instruction that limits analysis to job-related qualifications
- Candidate name, email, phone, location, and other identity details are not included in the AI payload. The payload contains skills, education, experience, projects, certifications, resume text, and job requirements.
- Django parses the response, verifies all required fields, clamps the score to 0–100, normalizes list fields, and stores the result.

### Failure behavior

- If no API key is configured, analysis fails with a clear configuration error.
- HTTP errors, timeouts, malformed JSON, or incomplete responses are caught by the view and shown as an error instead of inventing a score.
- Existing application data remains available even if OpenRouter is unavailable.
- The API key stays in server-side configuration and is never sent to browser JavaScript or rendered into templates.

OpenRouter usage may have model availability, rate, privacy, and billing implications. Review the provider's current terms before sending real candidate data.

## Database overview

The app uses Django's built-in `User` model plus eight recruitment models:

- `CandidateProfile`
- `RecruiterProfile`
- `Skill`
- `Resume`
- `Job`
- `Application`
- `AIAnalysis`
- `RecruiterNote`
- `Interview`

Many-to-many skill relations use Django-generated join tables. An application is unique for each candidate/job pair. Its chosen resume is protected from deletion while referenced. See [DATABASE_DIAGRAM.md](DATABASE_DIAGRAM.md) for fields, cardinalities, and delete behavior.

## Security and ethics

### Security controls present in the project

- Passwords are hashed and sessions are handled by Django authentication.
- Candidate and recruiter views use role-checking decorators.
- State-changing recruiter actions use POST; Django CSRF middleware is enabled.
- Django ORM and forms reduce SQL-injection risk and validate inputs.
- Duplicate applications are blocked by a database `UniqueConstraint`.
- Resume uploads are limited to `.pdf` filenames and 5 MB in `ResumeForm`.
- The OpenRouter key is read from `.env`; `.env`, the SQLite database, uploaded media, and collected static files are ignored by Git.
- OpenRouter calls have an explicit timeout and reject incomplete analysis output.

### Known limitations and production checklist

This is a college/demo project, not a production hiring platform. Before production use:

- Set `DEBUG=False`, use a unique `DJANGO_SECRET_KEY`, configure hosts/origins, and serve through HTTPS.
- Enable Django password validators; this project currently sets `AUTH_PASSWORD_VALIDATORS = []` for demo simplicity.
- Replace SQLite with a managed production database and use production-grade WSGI/ASGI hosting.
- Store uploaded files in protected object storage and add access controls, malware scanning, retention limits, and backup policies.
- Validate actual file content/MIME type in addition to the current extension and size checks.
- Do not assign the shared temporary password used by the recruiter-created-candidate demo flow; use a one-time activation/reset link.
- Limit login and AI endpoints with rate limiting, logging, monitoring, and cost controls.
- Avoid displaying raw provider errors to end users; log them securely and show a generic message.
- Define data retention/deletion procedures and obtain candidate consent before sending resume-derived data to an external AI provider.

### Responsible AI rules

- AI is used as decision support, not an autonomous decision maker.
- The system prompt prohibits inference or use of age, gender, race, religion, caste, disability, health, political beliefs, marital status, and other protected traits.
- The payload intentionally omits direct identity/contact fields, but free-form resume text can still contain personal or sensitive information.
- Scores can be wrong, incomplete, inconsistent, or biased. Recruiters must inspect the underlying evidence and provide human oversight.
- Do not reject or select a candidate solely from `ai_match_score`.
- Audit model changes, prompt changes, and outcomes before using this approach with real applicants.

## Testing

Run all automated tests:

```bash
python manage.py test
```

Run Django's configuration checks:

```bash
python manage.py check
```

The current test suite covers:

- Candidate and recruiter dashboard routing
- Candidate registration and profile creation
- Recruiter-only job creation
- Duplicate-application prevention
- Recruiter status updates
- Structured AI response parsing and output shape

The AI test mocks `requests.post`; it does not consume credits or call OpenRouter. For a manual live integration test, configure a valid key, sign in as the recruiter, open an application, and trigger analysis. Do not place real secrets in tests or source control.

## Useful development commands

```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Recreate/update demo data
python manage.py seed_demo

# Create a separate Django administrator
python manage.py createsuperuser

# Run checks and tests
python manage.py check
python manage.py test

# Start local server
python manage.py runserver
```

## Limitations

- SQLite and Django's development server are intended for local/demo use.
- Resume text extraction works only for PDFs that contain extractable text; image-only/scanned PDFs require OCR, which is not implemented.
- Model quality and availability depend on the configured OpenRouter model.
- Analysis runs synchronously during the web request and can take up to the configured 90-second HTTP timeout.
- There is no email notification, password-reset workflow, background job queue, virus scanner, or production deployment configuration.
- `RecruiterNote` exists in the data model, while the current application review form primarily edits the `Application.recruiter_notes` text field.

## Suggested demo flow

1. Run migrations and `seed_demo`.
2. Sign in as `candidate` and show the profile, jobs, and existing application.
3. Sign out and sign in as `recruiter`.
4. Show dashboard statistics, job candidates, and the pipeline.
5. Open an application and run AI analysis with a configured OpenRouter key.
6. Explain that the structured evidence supports—not replaces—the recruiter's decision.
7. Update the status and schedule an interview.

## License

No license file is currently included. Treat the code as an academic project unless the project owner adds explicit licensing terms.
