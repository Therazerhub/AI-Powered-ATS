# AI-Powered ATS — Viva Cheat Sheet

> **Memorization tip:** Say the **SHORT ANSWER** first. Expand with the **DETAILED ANSWER** only when the examiner asks a follow-up.

## Project and Django Architecture

### 1. What problem does this project solve?

**SHORT ANSWER:** It is an Applicant Tracking System that lets candidates maintain profiles and apply for jobs while recruiters manage vacancies, applications, interviews, and AI-assisted matching.

**DETAILED ANSWER:** In this project, candidates can register, add education/experience/projects/certifications and skills, upload a PDF resume, browse open jobs, and submit one application per job. Recruiters can create jobs, browse candidates, review a status pipeline, schedule interviews, and ask OpenRouter for a job-related qualification analysis. The AI score is displayed as advisory rather than being used as an automatic hiring decision.

### 2. Why did you choose Django?

**SHORT ANSWER:** Django provides authentication, forms, ORM, templates, security middleware, and an admin site in one framework, so it fits a database-driven academic ATS well.

**DETAILED ANSWER:** The project uses Django 5.2.18. Built-in components reduce custom code: `User` handles accounts, ModelForms validate inputs, the ORM talks to SQLite, templates render the UI, middleware handles sessions and CSRF, and URL routing connects requests to views. That made a single-server MVT design simpler and more explainable than splitting the project into separate frontend and backend applications.

### 3. Explain Django's MVT pattern using this project.

**SHORT ANSWER:** Models store ATS data, views contain request-handling logic, and templates present the result; URLs route requests to the correct view.

**DETAILED ANSWER:** `recruitment/models.py` defines entities such as `Job`, `Application`, and `CandidateProfile`. `recruitment/views.py` queries or updates those models and creates context—for example, `job_list` filters open jobs—then templates such as `templates/recruitment/job_list.html` render HTML. `recruitment/urls.py` maps paths such as `jobs/<int:pk>/` to `job_detail`.

### 4. How is this project organized?

**SHORT ANSWER:** `ats_project` holds project-wide configuration, while the `recruitment` app holds the ATS models, forms, views, URLs, services, and tests.

**DETAILED ANSWER:** `ats_project/settings.py` configures installed apps, middleware, SQLite, templates, static/media paths, and OpenRouter settings. The root URL configuration includes authentication routes and `recruitment.urls`. Shared templates live under `templates/`, browser assets under `static/`, uploaded resumes under `media/`, and the AI/PDF integration is isolated in `recruitment/services.py`.

### 5. What happens from an HTTP request to the final HTML response?

**SHORT ANSWER:** Django matches the URL, runs middleware and the view, the view uses models/forms, and `render()` combines context with a template to return an HTTP response.

**DETAILED ANSWER:** For `/jobs/`, `ats_project/urls.py` delegates to `recruitment.urls`, which selects `job_list`. Middleware supplies sessions, authentication, messages, and CSRF processing. The view queries `Job`, sends `jobs` and `query` to `recruitment/job_list.html`, and Django returns rendered HTML to the browser.

## Models, ORM, and Relationships

### 6. What is a Django model?

**SHORT ANSWER:** A model is a Python class that describes persistent data and its database rules; Django maps it to a table.

**DETAILED ANSWER:** Each class in `recruitment/models.py` subclasses `models.Model`. Fields such as `Job.title`, `Application.status`, and `Resume.file` become database columns, while relationships become foreign keys or join tables. Model metadata also defines ordering and the unique application constraint.

### 7. What is an ORM, and how is it used here?

**SHORT ANSWER:** The ORM lets the project query SQLite with Python objects instead of writing raw SQL.

**DETAILED ANSWER:** Examples include `Job.objects.filter(status="open")`, `Application.objects.filter(job=job, candidate=candidate).exists()`, and `AIAnalysis.objects.update_or_create(...)`. Django translates these QuerySets into SQL, maps rows back to model instances, and supplies database-independent validation and relationship traversal.

### 8. What relationships exist in this database?

**SHORT ANSWER:** The project uses one-to-one, one-to-many, and many-to-many relationships.

**DETAILED ANSWER:** `User` has one `CandidateProfile` or `RecruiterProfile`; an `Application` has one `AIAnalysis` and at most one `Interview`. A candidate has many resumes and applications, while a job has many applications. Skills are many-to-many with candidates and with both required and preferred job skills.

### 9. Why is `CandidateProfile.user` a `OneToOneField`?

**SHORT ANSWER:** It extends one Django user with exactly one candidate-specific profile without replacing the built-in user model.

**DETAILED ANSWER:** Login data remains in `django.contrib.auth.models.User`, while phone, education, experience, projects, location, and skills live in `CandidateProfile`. The `related_name="candidate_profile"` allows `request.user.candidate_profile`, which candidate views and role decorators use throughout the project.

### 10. Why are skills modeled with `ManyToManyField`?

**SHORT ANSWER:** A candidate or job can have many skills, and the same skill can belong to many candidates and jobs.

**DETAILED ANSWER:** `CandidateProfile.skills`, `Job.required_skills`, and `Job.preferred_skills` point to the shared `Skill` table. Django creates intermediate join tables automatically. The forms accept comma-separated text, use case-insensitive `get_or_create`, and call `.set(skills)` to update those relationships without duplicating common skill names.

### 11. What is the purpose of `ForeignKey` in `Application`?

**SHORT ANSWER:** Foreign keys connect each application to one candidate, one job, and one selected resume while allowing those parent records to have many applications.

**DETAILED ANSWER:** `Application.candidate` and `.job` use `CASCADE`, so deleting the candidate or job removes dependent applications. `Application.resume` uses `PROTECT`, preventing deletion of a resume that is evidence for an existing application. Reverse names such as `job.applications` and `candidate.applications` make navigation readable.

### 12. Explain `CASCADE` versus `PROTECT` in this project.

**SHORT ANSWER:** `CASCADE` removes dependent records with their parent; `PROTECT` blocks deletion when a referenced record must be preserved.

**DETAILED ANSWER:** Deleting an application also deletes its one-to-one `AIAnalysis` and `Interview`, because they use `CASCADE`. A used resume cannot be deleted because `Application.resume` is protected, and a user who created a job or updated an interview is also protected from deletion through the corresponding `PROTECT` relationships.

### 13. How does the project prevent duplicate applications?

**SHORT ANSWER:** It checks before saving and also enforces a database-level unique constraint on candidate plus job.

**DETAILED ANSWER:** `apply_job` first calls `.exists()` for a friendly warning. More importantly, `Application.Meta.constraints` defines `UniqueConstraint(fields=["candidate", "job"], ...)`, so even concurrent requests cannot insert the same pair twice. The view catches `IntegrityError` as a second line of defense.

### 14. Why use `JSONField` for AI results?

**SHORT ANSWER:** AI output contains structured lists and text that fit JSON, so it can be stored and rendered without making a table for every list item.

**DETAILED ANSWER:** `Application.ai_analysis` stores the complete response dictionary for convenient display, while `AIAnalysis` also stores typed analysis fields such as matching skills, missing skills, strengths, and concerns. SQLite supports Django's JSONField for this use case, and templates iterate fields such as `application.ai_analysis.matching_skills`.

### 15. What are migrations?

**SHORT ANSWER:** Migrations are version-controlled instructions that synchronize model definitions with the database schema.

**DETAILED ANSWER:** `recruitment/migrations/0001_initial.py` creates all ATS tables, relationships, indexes implied by fields, and the candidate-job unique constraint. After changing models, `python manage.py makemigrations` creates a migration and `python manage.py migrate` applies it to `db.sqlite3`.

### 16. Why use `select_related` and `prefetch_related`?

**SHORT ANSWER:** They reduce repeated database queries by loading related objects efficiently.

**DETAILED ANSWER:** `select_related` uses SQL joins for single-valued relations, as in applications loading `candidate__user`, `job`, and `resume`. `prefetch_related` performs a separate bulk query for multi-valued relations, as in candidate skills or job skills. This avoids the N+1 query problem when a page loops over many rows.

### 17. How do `Q`, `Count`, and `annotate` help in this project?

**SHORT ANSWER:** `Q` builds combined search conditions, while `annotate(Count(...))` adds calculated counts to query results.

**DETAILED ANSWER:** Job search ORs case-insensitive matches across title, department, and location. Candidate search similarly checks names, email, and skill names and then calls `distinct()` to remove join duplicates. Dashboards annotate jobs with applicant, shortlisted, and interview counts instead of calculating each one in Python.

## Forms, Authentication, and Authorization

### 18. Why use Django forms and ModelForms?

**SHORT ANSWER:** They centralize input parsing, validation, error messages, and safe conversion from submitted text to Python/model values.

**DETAILED ANSWER:** `CandidateProfileForm`, `ResumeForm`, `JobForm`, and others map allowed fields explicitly and only save after `form.is_valid()`. The project also customizes widgets for Bootstrap, limits application resume choices to the logged-in candidate, and adds upload checks in `ResumeForm.clean_file()`.

### 19. What does `commit=False` do?

**SHORT ANSWER:** It creates or updates a model object without saving it yet, so required fields not present in the form can be added first.

**DETAILED ANSWER:** In `apply_job`, the form provides only resume and cover letter; `commit=False` lets the view assign `job` and `candidate` before `app.save()`. Job creation similarly assigns `created_by`, resume upload assigns `candidate`, and interview scheduling assigns `application` and `updated_by`.

### 20. How does candidate registration work?

**SHORT ANSWER:** A customized `UserCreationForm` validates credentials, creates the Django user and candidate profile, then logs the new user in.

**DETAILED ANSWER:** `CandidateRegistrationForm` adds required first name, last name, and email to username/password fields. Its `save()` calls Django's parent implementation, which hashes the password, then creates a `CandidateProfile`. `register_candidate` calls `login(request, user)` and redirects to profile editing.

### 21. What is authentication versus authorization?

**SHORT ANSWER:** Authentication proves who the user is; authorization decides what that authenticated user may do.

**DETAILED ANSWER:** Django's login/logout views, password hashing, session cookie, and `AuthenticationMiddleware` implement authentication. Authorization is enforced by `candidate_required` and `recruiter_required`: candidates may edit profiles and apply, while staff or users with a `RecruiterProfile` may manage jobs, applications, AI analysis, statuses, and interviews.

### 22. How do role-based access controls work here?

**SHORT ANSWER:** Custom decorators check for a candidate profile or recruiter status before allowing a protected view to execute.

**DETAILED ANSWER:** Both decorators first apply `login_required`. `candidate_required` requires `request.user.candidate_profile`; `recruiter_required` accepts either `is_staff` or `recruiter_profile`. These are server-side checks, so hiding recruiter links in `base.html` is only a UI convenience, not the security boundary.

### 23. How does session authentication work in Django?

**SHORT ANSWER:** After login, Django stores authentication state in a server-side session and sends the browser a session ID cookie.

**DETAILED ANSWER:** `SessionMiddleware` reads the session and `AuthenticationMiddleware` exposes the corresponding user as `request.user`. Views then inspect `request.user.is_authenticated`, `is_staff`, or related profiles. The password itself is hashed in the auth database and is not stored in the session or sent on every request.

### 24. What role does the context processor play?

**SHORT ANSWER:** It adds `is_recruiter` and `is_candidate` to every template context so navigation can adapt to the logged-in role.

**DETAILED ANSWER:** `recruitment.context_processors.role_context` is registered in `TEMPLATES`. It derives booleans from authentication, staff status, and profile relationships. `base.html` uses them to show recruiter links such as Candidates and Pipeline or candidate links such as Jobs; views still enforce permissions independently.

## Uploads and Resume Processing

### 25. How are resume uploads handled?

**SHORT ANSWER:** A multipart form validates a PDF, Django stores it under `media/resumes/year/month/`, and pypdf extracts text for AI analysis.

**DETAILED ANSWER:** The profile template uses `enctype="multipart/form-data"`, and the view supplies both `request.POST` and `request.FILES`. `Resume.file` is a `FileField`; after save, `extract_pdf_text(resume.file.path)` reads every page, joins extracted text, and stores at most 30,000 characters in `extracted_text`.

### 26. How are uploaded files validated?

**SHORT ANSWER:** The model checks the `.pdf` extension and the form checks both that extension and a 5 MB maximum size.

**DETAILED ANSWER:** `FileExtensionValidator(["pdf"])` protects model-level saves, while `ResumeForm.clean_file()` rejects files larger than 5 MB or names without `.pdf`. The HTML `accept="application/pdf"` helps users choose a file but is not trusted as security. A production improvement would also inspect the MIME type and PDF signature, scan for malware, and avoid serving untrusted uploads directly.

### 27. Why save extracted resume text?

**SHORT ANSWER:** It avoids parsing the same PDF for every analysis and gives the AI text it can compare with the job.

**DETAILED ANSWER:** The upload flow extracts text once and stores it on `Resume`. If it is missing, `analyze_application_with_ai` attempts extraction before calling OpenRouter. The candidate payload limits resume text to 18,000 characters, reducing prompt size and cost while keeping the stored extraction capped at 30,000 characters.

### 28. What happens when PDF extraction fails?

**SHORT ANSWER:** The resume remains uploaded, and the user receives a warning instead of the whole profile update failing.

**DETAILED ANSWER:** In `profile_edit`, extraction is wrapped in `try/except`; failures create a Django warning message. In the recruiter add-candidate path, the exception is currently silently ignored. The AI service retries extraction if needed, but image-only/scanned PDFs would require OCR, which this project does not implement.

## HTTP, APIs, REST, and JSON

### 29. What HTTP methods does the project use, and why?

**SHORT ANSWER:** GET reads pages or search results, while POST performs state-changing actions such as registration, applying, deleting, status updates, interviews, and AI analysis.

**DETAILED ANSWER:** Views inspect `request.GET` for search terms and `request.POST` for submitted forms. Sensitive actions such as `job_delete`, `analyze_application`, `update_status`, and `schedule_interview` use `@require_POST`, preventing accidental changes through a normal link or crawler-generated GET request.

### 30. Is this project a REST API?

**SHORT ANSWER:** No; it is mainly a server-rendered Django application, though a few endpoints return JSON in an API-like style.

**DETAILED ANSWER:** Most routes render HTML or redirect after form submission rather than exposing CRUD resources through Django REST Framework. `update_status` returns `JsonResponse`, and `analyze_application` can return JSON for an `XMLHttpRequest`, but there is no versioned API, serializer layer, token authentication, or full REST resource design.

### 31. What makes an API RESTful?

**SHORT ANSWER:** A RESTful API treats data as resources, uses standard HTTP methods and status codes, and keeps requests stateless.

**DETAILED ANSWER:** A fuller REST version might expose `/api/jobs/` and `/api/applications/<id>/`, use GET/POST/PATCH/DELETE, and return consistent JSON representations. This project instead uses purpose-specific actions like `/hr/applications/<pk>/status/`, which is suitable for its server-rendered UI but not a complete REST architecture.

### 32. Where is JSON used?

**SHORT ANSWER:** JSON is used for OpenRouter requests/responses, AJAX-style responses, and persisted AI analysis fields.

**DETAILED ANSWER:** `requests.post(..., json=...)` serializes the OpenRouter payload with model, messages, temperature, token limit, and response format. `_extract_json` parses model text using `json.loads`; `JsonResponse` returns status/analysis outcomes to the browser; and Django `JSONField` stores lists and the complete analysis dictionary in SQLite.

### 33. How are HTTP errors handled in the OpenRouter call?

**SHORT ANSWER:** The request has a 90-second timeout and `raise_for_status()` converts non-success responses into exceptions handled by the view.

**DETAILED ANSWER:** `analyze_application_with_ai` posts to `https://openrouter.ai/api/v1/chat/completions`. Network errors, timeouts, bad HTTP statuses, malformed JSON, or incomplete analysis all raise exceptions. The view shows a Django error message for normal form requests or returns JSON with HTTP 502 for an XMLHttpRequest, making the external provider failure distinct from a bad client request.

### 34. Which HTTP status codes appear in project behavior?

**SHORT ANSWER:** Successful pages use 200, redirects commonly use 302, invalid status input returns 400, missing objects return 404, and AI-provider failures can return 502.

**DETAILED ANSWER:** `render()` and successful `JsonResponse` default to 200. `redirect()` returns a redirect response; `get_object_or_404()` produces 404 when a database object is absent. `update_status` explicitly returns 400 for an unsupported workflow status, and `analyze_application` returns 502 to AJAX clients when the upstream AI operation fails.

## AI, Environment Variables, and Matching

### 35. How is OpenRouter integrated?

**SHORT ANSWER:** The service sends a chat-completions POST request to OpenRouter with an anonymized job/candidate payload and asks for a strict JSON qualification analysis.

**DETAILED ANSWER:** `recruitment/services.py` reads `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` from Django settings. It sends a system instruction plus a user prompt to OpenRouter with low temperature `0.1`, `max_tokens=2000`, and JSON response format. The result is validated, clamped to 0–100, stored on `Application`, and upserted into `AIAnalysis` with provider/model metadata.

### 36. Why are the API key and model configured through environment variables?

**SHORT ANSWER:** Environment variables keep secrets out of source code and allow configuration to change without editing the application.

**DETAILED ANSWER:** `load_dotenv(BASE_DIR / ".env")` loads local development values, and settings read `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` with `os.getenv`. `.env.example` documents required names without containing a real key, while `.gitignore` should keep `.env` private. If no key is configured, the service raises a clear runtime error before making a request.

### 37. How is the AI prompt designed?

**SHORT ANSWER:** It restricts analysis to job-related evidence, excludes protected traits, declares the score advisory, and demands a fixed JSON shape.

**DETAILED ANSWER:** `SYSTEM_PROMPT` permits only skills, experience, education, projects, and certifications, and explicitly forbids inferring or using age, gender, race, religion, caste, disability, health, political beliefs, marital status, or similar traits. The user prompt includes an anonymized candidate/job payload and specifies fields such as `match_score`, matching/missing skills, strengths, concerns, and explanation.

### 38. How does candidate matching work?

**SHORT ANSWER:** OpenRouter compares the selected resume and candidate qualifications with the job description and required/preferred skills, then returns a structured advisory score and explanation.

**DETAILED ANSWER:** `candidate_payload()` includes skills, education, experience, projects, certifications, and extracted resume text, plus the job title, description, skills, experience, and education requirements. It deliberately excludes the candidate's name, email, phone, location, account data, and protected characteristics. The returned score ranks candidates on the recruiter page, but recruiters still review the underlying evidence and make the decision.

### 39. How do you validate AI output?

**SHORT ANSWER:** The code parses JSON, requires every expected key, clamps the score to 0–100, and normalizes list fields.

**DETAILED ANSWER:** `_extract_json()` first removes optional Markdown code fences, tries direct `json.loads`, and otherwise extracts a JSON object from surrounding text. The service rejects missing keys, converts the score to an integer within 0–100, and wraps non-list values for matching skills, missing skills, projects, strengths, and concerns. Database validators add another 0–100 rule when persisted through model validation paths.

### 40. Why is AI analysis advisory instead of automatic?

**SHORT ANSWER:** LLM output can be incomplete, inconsistent, or biased, so it should support a human recruiter rather than decide a person's employment.

**DETAILED ANSWER:** The interface explicitly labels scores as advisory, and status changes remain recruiter-controlled. The prompt excludes protected traits and the payload omits direct identity data, but prompt rules cannot guarantee fairness or truth. Human review, auditable evidence, candidate appeal/correction, periodic bias testing, and avoiding automatic rejection are necessary safeguards.

## SQLite, JavaScript, Security, and Quality

### 41. Why is SQLite used, and what are its limits?

**SHORT ANSWER:** SQLite is zero-configuration and ideal for a college demo, but it is not the best choice for heavy concurrent production traffic.

**DETAILED ANSWER:** `settings.py` points Django's default database to `BASE_DIR / "db.sqlite3"`, so setup needs no separate database server. It supports this project's relational tables, constraints, and JSONField use. For production with many recruiters and simultaneous writes, PostgreSQL would offer stronger concurrency, operations, indexing options, and scaling.

### 42. What does JavaScript do in this project?

**SHORT ANSWER:** JavaScript provides small progressive enhancements: file-name feedback, delete confirmation, and a loading state during AI analysis.

**DETAILED ANSWER:** `static/js/app.js` runs after `DOMContentLoaded`. It shows the selected resume filename, calls `confirm()` for forms marked `data-confirm`, and disables the Analyze button while showing a spinner. Core submission and authorization remain server-side, so these convenience behaviors are not trusted for validation or security.

### 43. What is CSRF, and how does Django prevent it here?

**SHORT ANSWER:** CSRF tricks a logged-in browser into submitting an unwanted request; Django blocks it by checking a secret token on unsafe requests.

**DETAILED ANSWER:** `CsrfViewMiddleware` is enabled, and POST forms include `{% csrf_token %}`, including login, logout, profile, job, application, interview, deletion, and AI analysis forms. Django compares the submitted token with the user's CSRF cookie/session context. `CSRF_TRUSTED_ORIGINS` is configurable for legitimate deployed origins.

### 44. What security features are already present?

**SHORT ANSWER:** The project uses password hashing, sessions, server-side role checks, CSRF protection, ORM queries, POST-only mutations, upload limits, and controlled template escaping.

**DETAILED ANSWER:** Django's auth system hashes passwords, middleware protects sessions/CSRF/clickjacking, and custom decorators enforce candidate/recruiter access. ORM filters avoid hand-built SQL injection risks, templates auto-escape normal variable output, and `get_object_or_404` handles invalid IDs. Environment variables separate secrets, and the AI payload excludes identity and protected traits.

### 45. What security improvements are still needed before production?

**SHORT ANSWER:** Disable debug, use strong secrets and validators, harden uploads/cookies/HTTPS, remove shared temporary passwords, and tighten recruiter permissions.

**DETAILED ANSWER:** The development fallback secret and `DEBUG=True` default must not be used in production, and `AUTH_PASSWORD_VALIDATORS` is currently empty. Recruiter-created accounts use the shared `Candidate@123` password and should instead use an expiring invitation/reset flow. Uploads need signature/MIME and malware checks, private authorized download handling, and safer storage; HTTPS, secure cookies, strict hosts/origins, rate limiting, audit logs, least-privilege recruiter scoping, and API secret rotation should also be added.

### 46. How does Django reduce SQL injection and XSS risk here?

**SHORT ANSWER:** ORM queries parameterize database values, and Django templates escape variable output by default.

**DETAILED ANSWER:** Searches use expressions such as `title__icontains=query` and `Q(...)` instead of concatenating raw SQL. Candidate data and AI text rendered with `{{ ... }}` are escaped unless explicitly marked safe, and this project does not use `safe` for them. These defaults help, but untrusted file handling, third-party data, headers, and any future raw HTML/SQL still require review.

### 47. How is business integrity protected beyond form validation?

**SHORT ANSWER:** Database constraints and restricted workflow choices protect rules even if a request bypasses the browser form.

**DETAILED ANSWER:** The candidate-job unique constraint prevents duplicates at the database layer; 0–100 validators bound match scores; model `choices` define known statuses, job types, and interview modes. `update_status` additionally checks the submitted value against `Application.STATUS`, while foreign-key deletion policies protect referenced resumes and audit-related users.

### 48. What tests exist in this project?

**SHORT ANSWER:** Django tests cover role-based dashboard routing, registration, recruiter-only job creation, duplicate applications, status updates, and mocked AI response parsing.

**DETAILED ANSWER:** `recruitment/tests.py` creates users, profiles, skills, a PDF resume, and a job in `setUp`. It uses Django's test client for pages and JSON endpoints, verifies the database unique rule, and patches `requests.post` so the AI test is deterministic and does not spend credits or depend on the network.

### 49. Why mock OpenRouter in automated tests?

**SHORT ANSWER:** Mocking makes tests fast, repeatable, private, and independent of API availability or cost.

**DETAILED ANSWER:** The test replaces `recruitment.services.requests.post` with a controlled response containing the expected chat-completion shape. `override_settings` supplies fake key/model values, and assertions verify parsing of the score and missing skills. A separate opt-in integration test could test the real service, but it should not be the normal unit test.

### 50. What are the main ethical risks and mitigations?

**SHORT ANSWER:** The main risks are bias, hallucinated conclusions, privacy leakage, and over-reliance on a score; mitigations are data minimization, protected-trait exclusion, transparency, human review, and auditing.

**DETAILED ANSWER:** This project sends only job-related profile/resume evidence and omits direct identity fields from `candidate_payload`; the prompt explicitly bans protected-trait inference, and the UI calls the score advisory. However, resumes can indirectly reveal identity or protected traits, and a third-party model can still behave unfairly. A real deployment needs candidate consent and retention rules, vendor/privacy assessment, encryption/access logs, bias and accuracy evaluation across groups, explanations tied to job criteria, human override, and a correction/appeal process.

## Rapid-Fire Closing Answers

- **Framework:** Django 5.2.18, server-rendered MVT.
- **Database:** SQLite for the demo; PostgreSQL is the likely production upgrade.
- **Authentication:** Django `User`, session authentication, login/logout views.
- **Authorization:** `candidate_required` and `recruiter_required` decorators.
- **AI provider:** OpenRouter chat-completions API.
- **AI model:** Configurable with `OPENROUTER_MODEL`; current default is `cohere/north-mini-code:free`.
- **Resume parser:** `pypdf.PdfReader`.
- **AI output:** Validated JSON with a clamped 0–100 advisory score.
- **Duplicate prevention:** Both an `.exists()` check and a database `UniqueConstraint`.
- **Core ethical rule:** AI assists qualification review; it does not make the hiring decision.
