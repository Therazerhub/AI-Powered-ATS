# TalentIQ — AI-Powered ATS Presentation Guide

> A beginner-friendly, code-accurate guide for presenting this Django college project.

## Quick facts to remember

- **Project name shown in the UI:** TalentIQ
- **ATS:** Applicant Tracking System
- **Backend:** Django 5.2
- **Database:** SQLite
- **Resume reader:** `pypdf`
- **AI gateway:** OpenRouter Chat Completions API
- **Default model:** `cohere/north-mini-code:free` (configurable)
- **Main idea:** organize recruitment and provide an **advisory** job-match analysis; a human recruiter makes the final decision.

---

# Part 1 — The 19 beginner-friendly explanation topics

## 1. What problem does this project solve?

Recruiters may receive many applications and need to compare each candidate's skills, experience, education, projects, and certifications with a job. Doing that manually is repetitive. TalentIQ keeps jobs, candidates, resumes, applications, statuses, interviews, and notes in one system. Its AI feature creates a first-pass qualification summary so the recruiter can review evidence more quickly.

It does **not** replace the recruiter and does **not** make the hiring decision.

## 2. What is an ATS?

ATS means **Applicant Tracking System**. Think of it as a digital recruitment register. Instead of keeping resumes and decisions in separate files, an ATS tracks a candidate from application to review, shortlist, interview, selection, or rejection.

This project's pipeline has these exact stages:

1. Applied
2. Under Review
3. Shortlisted
4. Interview
5. Selected
6. Rejected

## 3. Who uses the system?

There are two user roles:

- **Candidate:** creates an account, completes a profile, uploads a PDF resume, sees open jobs, applies, and tracks application status.
- **Recruiter:** creates and edits vacancies, adds or searches candidates, reviews applications, runs AI analysis, updates status and notes, and schedules interviews.

Django login protects private pages. The custom `candidate_required` and `recruiter_required` decorators prevent one role from opening the other role's pages. A staff user also counts as a recruiter.

## 4. What technologies are used?

- **Django:** handles URLs, login, forms, business logic, templates, and database access.
- **SQLite:** stores the application's structured data in `db.sqlite3`.
- **HTML, CSS, Bootstrap, and Bootstrap Icons:** build the interface.
- **JavaScript:** provides small browser-side interactions.
- **pypdf:** reads text from uploaded PDFs.
- **requests:** sends the server-to-server HTTP request to OpenRouter.
- **python-dotenv:** loads configuration from `.env`.
- **OpenRouter:** provides access to the selected language model.

## 5. How is the Django project organized?

A simple MVC-style explanation for Django is **Model–View–Template**:

- **Models** (`recruitment/models.py`) describe data and relationships.
- **Views** (`recruitment/views.py`) receive requests, perform actions, and choose responses.
- **Templates** (`templates/`) produce the HTML pages.
- **URLs** (`recruitment/urls.py`) connect a browser address to a view.
- **Forms** (`recruitment/forms.py`) validate user input.
- **Services** (`recruitment/services.py`) contain PDF extraction and the OpenRouter AI integration.

Example: opening `/hr/applications/2/` matches a URL, runs `application_detail`, reads application 2 from the database, and renders `application_detail.html`.

## 6. What data does the database store?

The main models are:

- `Skill` — one reusable skill name.
- `CandidateProfile` — phone, education, experience, projects, certifications, location, and skills.
- `RecruiterProfile` — recruiter's job title and department.
- `Resume` — PDF file, extracted text, active flag, and upload date.
- `Job` — role details, required/preferred skills, deadline, status, and creator.
- `Application` — connects one candidate, one job, and one resume; also stores status, AI score, AI JSON, and recruiter notes.
- `AIAnalysis` — a structured copy of the latest analysis, including provider and model name.
- `RecruiterNote` — note records supported by the data model.
- `Interview` — schedule, mode, location/link, notes, and updater.

A database constraint prevents the same candidate from applying to the same job twice.

## 7. What is the candidate workflow?

1. Register a candidate account.
2. Complete education, skills, experience, projects, certifications, and location.
3. Optionally upload a PDF resume of at most 5 MB.
4. Browse open, non-expired jobs.
5. Open a job and apply using one of the candidate's resumes.
6. Track status and, if available, the AI match percentage on the candidate dashboard.

Uploading a new resume marks older resumes inactive, although previous applications keep their selected resume because the application has its own resume link.

## 8. What is the recruiter workflow?

1. Log in to the recruiter dashboard.
2. View totals for open jobs, applications, reviews, shortlists, interviews, and selections.
3. Create a vacancy with required and preferred skills.
4. Open a vacancy and view its applicants.
5. Review a candidate's qualifications and resume.
6. Optionally click **AI Analyze Candidate**.
7. Read the AI score, matching skills, missing skills, strengths, concerns, and explanation.
8. Add notes and manually update status, or schedule an interview.
9. Use the Pipeline page to see every application by stage.

The candidate list for a job is ordered by AI score and then application date, but the page explicitly says scores are advisory.

## 9. How does resume upload and text extraction work?

The form accepts a filename ending in `.pdf` and rejects files above 5 MB. Django saves the file under `media/resumes/<year>/<month>/`. The service opens it with `PdfReader`, extracts text page by page, joins the pages, and stores at most 30,000 characters in `Resume.extracted_text`.

For an AI request, at most the first **18,000 characters** of stored resume text are included. If no text was extracted earlier, the AI service tries extraction again before making the request.

Important limitation: image-only/scanned PDFs may have little or no extractable text because this project has no OCR. Also, checking the extension is useful but is not full file-content verification.

## 10. What does “AI-powered” mean here?

It means the Django server sends job-related candidate data and job requirements to a language model, asks for a fixed analysis format, validates the returned fields, and displays the result. The AI does not control the whole application. Normal Django code still handles accounts, files, jobs, applications, statuses, interviews, and database storage.

The AI produces exactly these eight logical outputs:

- `match_score`
- `matching_skills`
- `missing_skills`
- `relevant_experience`
- `relevant_projects`
- `strengths`
- `concerns`
- `explanation`

## 11. What is an API? Use this simple analogy

An **API** is a defined way for two software systems to communicate.

**Restaurant analogy:**

- You are the Django application.
- The menu is the API documentation: it says what you may request.
- The waiter is the API endpoint: it carries a correctly formatted order.
- The kitchen is the AI service.
- Your order slip is the request body.
- The API key is like an authorized account card proving you may order.
- The prepared dish is the response.

Django does not enter OpenRouter's kitchen or run its model directly. It sends an HTTPS request in the expected format and receives a structured answer.

## 12. What are HTTP and an endpoint?

**HTTP** is the standard set of rules used to exchange web requests and responses. **HTTPS** is the encrypted version used here.

An **endpoint** is the specific API address. This project sends a `POST` request to:

```text
https://openrouter.ai/api/v1/chat/completions
```

`POST` means the client is sending data for the server to process. The request has a **90-second timeout**, so it does not wait forever. `response.raise_for_status()` turns HTTP failures such as 401 or 500 into errors handled by the Django view.

## 13. What is an API key and how is authentication done?

An **API key** is a secret credential identifying and authorizing the application to the provider. The code sends it in this HTTP header:

```http
Authorization: Bearer <OPENROUTER_API_KEY>
```

“Bearer” means possession of the key grants API access. The request also sends:

```http
Content-Type: application/json
HTTP-Referer: http://localhost:8000
X-Title: AI-Powered ATS College Project
```

The API key must never be placed in HTML, JavaScript, Git, screenshots, or presentation slides. It stays server-side. This API authentication is separate from the recruiter's Django login session.

## 14. What is a request body?

The **request body** is the information sent with a `POST` request. The real code sends a Python dictionary through `requests.post(..., json={...})`; `requests` serializes it as JSON. Its exact top-level shape is:

```json
{
  "model": "value of OPENROUTER_MODEL",
  "messages": [
    {"role": "system", "content": "ethical rules and JSON-only instruction"},
    {"role": "user", "content": "required output shape plus candidate and job data"}
  ],
  "temperature": 0.1,
  "max_tokens": 2000,
  "response_format": {"type": "json_object"}
}
```

A low temperature of `0.1` asks for a more consistent, less creative answer. `max_tokens: 2000` limits the generated output. `response_format` requests a JSON object.

## 15. What is JSON?

**JSON**, or JavaScript Object Notation, is a text format for structured data. It uses named keys, values, lists, strings, and numbers. It is common in APIs because both humans and programs can read it.

A simplified expected AI result is:

```json
{
  "match_score": 85,
  "matching_skills": ["Python", "Django", "SQL"],
  "missing_skills": ["REST API"],
  "relevant_experience": "The candidate reports one year of Django work.",
  "relevant_projects": ["Django e-commerce website"],
  "strengths": ["Relevant backend stack"],
  "concerns": ["Docker experience is not shown"],
  "explanation": "The candidate matches several required skills, but some preferred experience is not demonstrated."
}
```

This is an example shape, not a guaranteed live score or wording.

## 16. What happens to the API response?

OpenRouter's outer response is parsed with `response.json()`. The project reads the model's message from this exact path:

```python
response.json()["choices"][0]["message"]["content"]
```

That content is itself expected to contain JSON. `_extract_json()` removes an optional Markdown code fence, tries `json.loads()`, and can recover the first `{ ... }` object if extra text is present. Then the service:

1. checks that all eight required keys exist;
2. converts `match_score` to an integer and clamps it to 0–100;
3. converts five expected list fields to lists if needed;
4. returns the cleaned dictionary.

The view saves the result in both `Application.ai_analysis`/`ai_match_score` and the one-to-one `AIAnalysis` record. If anything fails, it shows an error and does not pretend analysis succeeded.

## 17. What are environment variables and `.env`?

Environment variables are configuration values kept outside source code. `python-dotenv` loads the project's `.env` file when Django settings start. The relevant settings are:

```env
OPENROUTER_API_KEY=your-openrouter-api-key
OPENROUTER_MODEL=cohere/north-mini-code:free
```

The key has no safe default; without it, analysis stops with `OPENROUTER_API_KEY is not configured`. The model has the shown default and can be changed without editing application code. The repository's `.env.example` documents the variable names without containing a real key. Restart the Django server after changing `.env`.

## 18. What technical safety and security controls exist?

Current code controls include:

- login plus recruiter/candidate role checks;
- CSRF tokens on state-changing browser forms;
- server-side API call, keeping the OpenRouter key away from the browser;
- PDF extension and 5 MB checks on candidate uploads;
- unique candidate/job application constraint;
- required AI response-key validation;
- AI score clamped to 0–100;
- request timeout and HTTP error checking;
- recruiter-only AI, status, job, and interview actions;
- AI prompt asks the model to use job qualifications only.

Honest limitations to mention: development settings currently allow a fallback Django secret and have `DEBUG=True` by default; production should use a strong secret, `DEBUG=False`, strict hosts, HTTPS, stronger file-content validation/malware scanning, access/audit controls, retention rules, consent notices, and appropriate vendor/privacy agreements.

## 19. What are the ethical guardrails, and who decides?

The exact system-prompt policy says to compare only **skills, experience, education, projects, and certifications**. It tells the model never to infer or use age, gender, race, religion, caste, disability, health, political beliefs, marital status, or other protected traits. It also says the score is advisory, not a hiring decision.

The payload deliberately omits profile name, email, phone, and location. However, the prompt calls the candidate “anonymized” while also sending extracted resume text, and a resume may itself contain a name, contact details, photo-derived text, or sensitive information. Therefore, this is **data minimization, not guaranteed anonymization**. A production version should redact personal/sensitive data before sending it, obtain consent, limit retention, test for bias, provide explanations and appeal/review, and continuously audit outcomes.

Most importantly, the application leaves status changes and selection to the recruiter. The interface says **“Human recruiter retains final decision authority.”** A recruiter should read the resume and evidence, question incorrect AI output, use consistent job-related criteria, and never reject or select someone only because of the score.

---

# Part 2 — Exact AI API flow in this code

## One-line flow

```text
Recruiter click → Django POST view → build qualification payload → OpenRouter HTTPS POST → parse and validate JSON → save analysis → show it for human review
```

## Exact step-by-step flow

1. A logged-in recruiter opens `/hr/applications/<id>/`.
2. The page shows a form whose action is `/hr/applications/<id>/analyze/` and whose button says **AI Analyze Candidate** or **Analyze again**.
3. Clicking it sends a browser `POST` with a Django CSRF token.
4. Django routes the request to `analyze_application` in `recruitment/views.py`.
5. `@require_POST` rejects other HTTP methods, and `@recruiter_required` checks login and recruiter/staff access.
6. The view loads the `Application` and calls `analyze_application_with_ai(app)`.
7. The service stops if `settings.OPENROUTER_API_KEY` is empty.
8. If stored resume text is empty and a file exists, `extract_pdf_text()` reads it and saves up to 30,000 characters.
9. `candidate_payload()` builds the data. Candidate fields are skills, education, experience, projects, certifications, and up to 18,000 resume-text characters. Job fields are title, description, required skills, preferred skills, required experience, and education requirement.
10. The user prompt embeds a requested eight-field schema and the payload. The system prompt adds qualification-only and protected-trait rules.
11. `requests.post()` sends HTTPS to OpenRouter with the Bearer key, JSON content type, referer/title metadata, model, two messages, temperature `0.1`, maximum `2000` tokens, JSON-object response format, and a `90`-second timeout.
12. `raise_for_status()` checks the HTTP result.
13. The code reads `choices[0].message.content` from the OpenRouter response.
14. `_extract_json()` parses that content into a Python dictionary.
15. The service checks all required fields, clamps the score to 0–100, and normalizes list fields.
16. The view writes the score and full dictionary to `Application`.
17. `AIAnalysis.objects.update_or_create()` creates or replaces the structured latest analysis and records the configured model name; its provider defaults to `OpenRouter`.
18. For the normal HTML form, Django shows **Live AI analysis completed.** and redirects back to the application page. The template displays the score and analysis. If an AJAX client were used, the same view can instead return a small `JsonResponse`.
19. The recruiter separately reviews the evidence and uses the **Recruiter decision** form. AI never calls `update_status`, schedules an interview, selects, or rejects a candidate.

## Exact candidate/job data sent

```json
{
  "candidate": {
    "skills": ["names from CandidateProfile.skills"],
    "education": "candidate education",
    "experience": "candidate experience",
    "projects": "candidate projects",
    "certifications": "candidate certifications",
    "resume_text": "first 18000 characters of extracted text"
  },
  "job": {
    "title": "job title",
    "description": "job description",
    "required_skills": ["required skill names"],
    "preferred_skills": ["preferred skill names"],
    "required_experience": "required experience",
    "education_requirement": "education requirement"
  }
}
```

Not directly added from the profile: candidate name, email, phone, location, application status, recruiter notes, and interview details. Remember that free-text resume content can still contain personal data.

## Two different authentications

- **Browser → Django:** the recruiter is authenticated by Django's login session; CSRF protects the POST form.
- **Django → OpenRouter:** the server is authenticated by the `Authorization: Bearer ...` API-key header.

This distinction is useful in a viva: the user's password is not sent to OpenRouter, and the OpenRouter key is not sent to the browser.

---

# Part 3 — Memorisable 30-second explanation

> “TalentIQ is a Django-based applicant tracking system for candidates and recruiters. Candidates create profiles, upload PDF resumes, and apply for jobs. Recruiters manage vacancies and move applications through the hiring pipeline. When a recruiter requests analysis, Django extracts resume text and sends only job-relevant profile and job data to OpenRouter. The AI returns a structured match score, skills, strengths, concerns, and explanation. The result is stored for review, but it is only advisory—the human recruiter reads the evidence and makes the final decision.”

Memory pattern: **Track → Compare → Explain → Human decides.**

---

# Part 4 — Natural five-minute college presentation script

> **Target pace:** about 130–135 words per minute. The spoken script is about 660 words, so it fits approximately five minutes. Speak naturally and rehearse once with a timer.

## 0:00–0:35 — Introduction

“Good morning. My project is TalentIQ, an AI-powered Applicant Tracking System built with Django. An Applicant Tracking System, or ATS, helps an organization manage jobs, candidates, applications, and recruitment stages in one place. The problem I focused on is that recruiters often spend a lot of time repeatedly comparing resumes with job requirements. TalentIQ organizes that work and gives the recruiter an AI-assisted qualification summary. The important point is that the AI supports a person; it does not make the hiring decision.”

## 0:35–1:15 — Users and features

“There are two main roles. A candidate can register, complete a profile, upload a PDF resume, browse available jobs, apply, and track the application status. A recruiter can create vacancies, review candidates for each role, run the AI analysis, add notes, update the application stage, and schedule an interview. The stages are Applied, Under Review, Shortlisted, Interview, Selected, and Rejected. Role checks protect private actions, and the database also prevents one candidate from applying to the same job twice.”

## 1:15–1:55 — Django architecture

“The backend uses Django, and the data is stored in SQLite. The models represent skills, candidate and recruiter profiles, resumes, jobs, applications, AI analyses, notes, and interviews. Django URLs connect browser addresses to views. Views perform the business logic, forms validate input, and templates generate the pages. For PDF resumes, the project uses pypdf to extract text. This separation makes the project easier to understand and maintain because database logic, web logic, presentation, and AI integration have clear places.”

## 1:55–3:10 — API and exact AI flow

“The AI model is reached through the OpenRouter API. An API is like a restaurant waiter: our Django application places a structured order, the endpoint carries it to the AI service, and a structured response comes back. The secret API key is like an authorization card. It stays in the server's environment file and is sent in a Bearer authorization header; it is never placed in the browser.

When a recruiter clicks AI Analyze Candidate, the browser sends a protected POST request to Django. Django checks that the user is a recruiter and loads the application. If necessary, it extracts the resume text. It then creates a JSON payload containing skills, education, experience, projects, certifications, resume text, and the job's requirements. It sends an HTTPS POST request to OpenRouter's chat-completions endpoint.

The prompt requests eight fields: a zero-to-one-hundred score, matching and missing skills, relevant experience and projects, strengths, concerns, and a short explanation. The response is parsed as JSON. The program verifies that every field exists, clamps the score into the valid range, and saves the result in the database. If the network, provider, or format fails, the page reports an error instead of creating a fake result.”

## 3:10–4:10 — Ethics and limitations

“Recruitment AI has serious ethical risks, so this project includes guardrails. The system prompt tells the model to use only job-related qualifications and never infer or use protected traits such as age, gender, race, religion, caste, disability, health, political beliefs, or marital status. The direct profile payload leaves out the candidate's name, email, phone, and location.

But I would not claim perfect anonymization, because resume text can still contain personal or sensitive details. For production, I would add redaction, consent, stronger file validation, audit logs, bias testing, retention rules, and privacy agreements with the AI provider. A score can also be wrong or reproduce bias, so it must never become an automatic rejection rule.”

## 4:10–4:45 — Human control and demonstration link

“The human recruiter keeps final authority. AI analysis does not change an application status. The recruiter can read the resume, compare the explanation with real evidence, write notes, and then choose the next stage. Scheduling an interview is also a separate human action. This makes the workflow explainable: the system offers a summary, but the accountable decision remains with a person.”

## 4:45–5:00 — Conclusion

“To conclude, TalentIQ combines a standard Django recruitment workflow with a controlled AI API integration. It tracks applications, compares job-related evidence, explains the comparison, and keeps the human in control. The four words I use to summarize it are: track, compare, explain, and human decides. Thank you.”

---

# Part 5 — Exact five-minute click-by-click live demo

## Before presenting

1. From the project directory, run:

   ```bash
   source .venv/bin/activate
   python manage.py migrate
   python manage.py seed_demo
   python manage.py runserver
   ```

2. Confirm `.env` contains a valid `OPENROUTER_API_KEY`. Do **not** display `.env`.
3. Open `http://127.0.0.1:8000/accounts/login/`.
4. The seed command creates the demo recruiter username `recruiter`. Its demo password is printed by the seed command. Enter credentials privately before screen sharing if possible.
5. Keep `/hr/` ready in one tab. Use the seeded **Python Django Developer** vacancy and preferably the candidate that still shows **Not analyzed**, so the audience sees a fresh live result.
6. Have a fallback ready: the other seeded candidate may already have a stored score. If the API/network fails, explain the visible error honestly and open the previously analyzed record; never claim the fallback was a new response.

> The steps below total exactly 5:00. The quoted line is what to say while performing that step.

## 0:00–0:25 — Show recruiter dashboard

**Click/action:** If needed, click **Sign in**. On the recruiter dashboard, point to the six statistic cards.

**Say:** “I am logged in as a recruiter. This dashboard summarizes open jobs and each stage of the hiring process. These figures come from Django database queries, not from the AI.”

## 0:25–0:50 — Open a vacancy

**Click/action:** In **Active vacancies**, find **Python Django Developer** and click **View**.

**Say:** “Each vacancy has its own candidate list. This role has required and preferred skills, experience, education, location, and a deadline stored in the Job model.”

## 0:50–1:15 — Explain ranking carefully

**Click/action:** Point to the table headings **AI-Assisted Match Score** and **Status**. Find a row marked **Not analyzed** and click **Review**.

**Say:** “The table can order analyzed candidates by score, but the page clearly labels that score as advisory. An application without analysis remains ‘Not analyzed’; the system does not invent a score.”

## 1:15–1:50 — Review human-readable evidence first

**Click/action:** On the application page, point to the candidate name, **Candidate qualifications**, skill tags, experience, and projects. Optionally point to **Open resume PDF** without opening it.

**Say:** “Before using AI, the recruiter can inspect the candidate's actual qualifications and resume. The system stores structured profile fields and text extracted from the selected PDF. This evidence remains available for human checking.”

## 1:50–2:15 — Explain what will be sent

**Click/action:** Point to the empty AI card and then the **AI Analyze Candidate** button; do not click until the end of this segment.

**Say:** “This action sends job-related qualifications and job requirements from Django to OpenRouter. The direct profile payload excludes name, email, phone, and location, although resume text may still contain personal details, so production redaction is important.”

## 2:15–2:35 — Trigger the real API request

**Click/action:** Click **AI Analyze Candidate** once and wait. Do not double-click or refresh.

**Say:** “The browser sends a CSRF-protected POST to Django. Django checks recruiter access, creates the JSON request body, and makes a server-to-server HTTPS POST with the API key in a Bearer header.”

## 2:35–3:15 — Explain the returned analysis

**Click/action:** When the page reloads, point in order to the percentage, explanation, **Matching skills**, **Missing skills**, **Strengths**, and **Potential concerns**.

**Say:** “The model returns structured JSON. Django checks all required fields and keeps the score between zero and one hundred before saving it. We can now see the match, missing skills, strengths, concerns, and explanation. These are claims to verify against the resume, not facts to accept blindly.”

**If an error appears, say instead:** “The live provider request failed, and the application reports that failure instead of generating a fake result. I will use the stored analysis from the other demo record to show the output format.” Then go back, open the analyzed candidate, and continue.

## 3:15–3:50 — Show that AI does not decide

**Click/action:** Point to **Human recruiter retains final decision authority**, then point to the separate **Application status** and **Recruiter notes** fields. Do not choose Selected or Rejected just to demonstrate.

**Say:** “Notice that the AI result did not change the status. The recruiter has a separate decision form, can record notes, and remains accountable. The protected-trait rule also tells the model not to use age, gender, race, religion, caste, disability, health, politics, marital status, or similar traits.”

## 3:50–4:20 — Make a safe human workflow update

**Click/action:** Choose **Under Review**, enter a short note such as `AI summary reviewed; verify experience and missing skills manually.`, and click **Update application**.

**Say:** “For the demo, I am moving the record only to Under Review—not making a final decision. My note records that the AI output still needs manual verification. This status change comes from the recruiter, not the model.”

## 4:20–4:45 — Show the pipeline

**Click/action:** Click **Pipeline** in the top navigation. Point to the six columns and the application card under **Under Review**.

**Say:** “The pipeline groups applications into Applied, Under Review, Shortlisted, Interview, Selected, and Rejected. This view is ordinary ATS functionality backed by the database. Clicking a card returns to the full evidence and decision page.”

## 4:45–5:00 — Close with the key message

**Click/action:** Keep the pipeline visible; do not make another change.

**Say:** “So the complete flow is: track the application, compare job evidence, explain the result, and let a human decide. AI assists the workflow; it does not replace responsibility. That is TalentIQ.”

---

# Part 6 — Likely viva questions and short answers

### Why use OpenRouter?
“It gives one chat-completions API for a configurable model. In this code, the model name is an environment variable, so it can be changed without changing the service logic.”

### Does this project train its own AI model?
“No. It calls an externally hosted language model through OpenRouter and supplies the candidate/job context in the request.”

### Is the result deterministic?
“Not perfectly. The low temperature of 0.1 encourages consistency, but language-model responses can still vary. That is another reason the score is advisory.”

### Is the resume permanently sent to the browser or AI?
“The PDF is stored by Django. The AI request includes extracted resume text, not the PDF file itself. The provider receives that request data, so privacy and retention terms still matter.”

### What if the API key is missing?
“The service raises `OPENROUTER_API_KEY is not configured`, and the view displays an analysis failure instead of a result.”

### What if OpenRouter returns invalid data?
“The code checks the HTTP status, parses JSON, verifies all eight required keys, and reports an error when validation fails. It also clamps the numeric score to 0–100.”

### Does a high score automatically shortlist a candidate?
“No. AI analysis and status update are separate actions. Only the recruiter updates the status.”

### Is the candidate really anonymous?
“Direct profile identifiers are omitted, but resume text can contain identifiers. I describe it as data minimization, not guaranteed anonymization, and would add redaction in production.”

### What would you improve next?
“PII redaction, OCR for scanned resumes, MIME/content validation and malware scanning, provider privacy controls, audit logs, consent and deletion workflows, bias testing, rate limiting, retry/caching strategy, stronger production settings, and richer tests.”

---

# Part 7 — Code map for answering technical questions

| Question | Main file/code |
|---|---|
| AI endpoint, headers, body, parsing | `recruitment/services.py` |
| AI button handler and database save | `recruitment/views.py` → `analyze_application` |
| Candidate/job data sent to AI | `recruitment/services.py` → `candidate_payload` |
| Ethical system prompt | `recruitment/services.py` → `SYSTEM_PROMPT` |
| API key and model configuration | `ats_project/settings.py` and `.env.example` |
| Database fields and relationships | `recruitment/models.py` |
| Upload validation and forms | `recruitment/forms.py` |
| Role authorization | `recruitment/decorators.py` |
| Routes | `recruitment/urls.py`, `ats_project/urls.py` |
| AI result and human-decision UI | `templates/recruitment/application_detail.html` |
| Candidate ranking page | `templates/recruitment/job_candidates.html` |
| Automated flow tests | `recruitment/tests.py` |

## Final accuracy rule for the presentation

Say **“AI-assisted qualification analysis”**, not “the AI chooses the best employee.” Say **“data-minimized payload”**, not “fully anonymous resume.” Say **“advisory score”**, not “selection probability.” The code and interface support the first wording, not the second.
