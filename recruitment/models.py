from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse

class Skill(models.Model):
    name = models.CharField(max_length=80, unique=True)
    def __str__(self): return self.name

class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="candidate_profile")
    phone = models.CharField(max_length=20, blank=True)
    education = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    projects = models.TextField(blank=True)
    certifications = models.TextField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    skills = models.ManyToManyField(Skill, blank=True, related_name="candidates")
    created_at = models.DateTimeField(auto_now_add=True)
    @property
    def full_name(self): return self.user.get_full_name() or self.user.username
    @property
    def active_resume(self): return self.resumes.filter(is_active=True).first()
    def __str__(self): return self.full_name

class RecruiterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="recruiter_profile")
    job_title = models.CharField(max_length=100, default="HR Recruiter")
    department = models.CharField(max_length=100, default="Human Resources")
    def __str__(self): return f"{self.user.get_full_name() or self.user.username} - Recruiter"

class Resume(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="resumes")
    file = models.FileField(upload_to="resumes/%Y/%m/", validators=[FileExtensionValidator(["pdf"])])
    original_name = models.CharField(max_length=255, blank=True)
    extracted_text = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Resume - {self.candidate.full_name}"

class Job(models.Model):
    STATUS = [("draft","Draft"),("open","Open"),("closed","Closed")]
    EMPLOYMENT = [("full_time","Full-time"),("part_time","Part-time"),("contract","Contract"),("internship","Internship")]
    title = models.CharField(max_length=150)
    department = models.CharField(max_length=100)
    description = models.TextField()
    required_skills = models.ManyToManyField(Skill, related_name="required_for_jobs")
    preferred_skills = models.ManyToManyField(Skill, blank=True, related_name="preferred_for_jobs")
    required_experience = models.CharField(max_length=100)
    education_requirement = models.CharField(max_length=200)
    location = models.CharField(max_length=120)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT, default="full_time")
    salary_range = models.CharField(max_length=100, blank=True)
    application_deadline = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS, default="open")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_jobs")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return self.title
    def get_absolute_url(self): return reverse("job_detail", args=[self.pk])

class Application(models.Model):
    STATUS = [("applied","Applied"),("under_review","Under Review"),("shortlisted","Shortlisted"),("interview","Interview"),("selected","Selected"),("rejected","Rejected")]
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="applications")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    resume = models.ForeignKey(Resume, on_delete=models.PROTECT, related_name="applications")
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="applied")
    ai_match_score = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    ai_analysis = models.JSONField(default=dict, blank=True)
    recruiter_notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-ai_match_score", "-applied_at"]
        constraints = [models.UniqueConstraint(fields=["candidate","job"], name="unique_candidate_job_application")]
    def __str__(self): return f"{self.candidate.full_name} → {self.job.title}"

class AIAnalysis(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="analysis_record")
    match_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    matching_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    relevant_experience = models.TextField(blank=True)
    relevant_projects = models.JSONField(default=list)
    strengths = models.JSONField(default=list)
    concerns = models.JSONField(default=list)
    explanation = models.TextField()
    provider = models.CharField(max_length=50, default="OpenRouter")
    model_name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f"AI analysis: {self.application} ({self.match_score}%)"

class RecruiterNote(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]

class Interview(models.Model):
    MODE = [("online","Online"),("onsite","On-site"),("phone","Phone")]
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name="interview_details")
    scheduled_at = models.DateTimeField()
    mode = models.CharField(max_length=10, choices=MODE, default="online")
    location_or_link = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)
