from io import BytesIO
from unittest.mock import patch,Mock
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase,override_settings
from django.urls import reverse
from django.utils import timezone
from pypdf import PdfWriter
from .models import *
from .services import analyze_application_with_ai

def sample_pdf():
    bio=BytesIO(); w=PdfWriter(); w.add_blank_page(width=100,height=100); w.write(bio); return SimpleUploadedFile("resume.pdf",bio.getvalue(),"application/pdf")

class ATSFlowTests(TestCase):
    def setUp(self):
        self.hr=User.objects.create_user("hr",password="pass",is_staff=True); RecruiterProfile.objects.create(user=self.hr)
        self.user=User.objects.create_user("cand",password="pass",email="c@test.com"); self.profile=CandidateProfile.objects.create(user=self.user,experience="1 year Django",education="B.Tech",projects="ATS")
        self.python=Skill.objects.create(name="Python"); self.django=Skill.objects.create(name="Django"); self.profile.skills.set([self.python,self.django])
        self.resume=Resume.objects.create(candidate=self.profile,file=sample_pdf(),extracted_text="Python Django SQL project")
        self.job=Job.objects.create(title="Django Developer",department="Engineering",description="Build APIs",required_experience="1 year",education_requirement="B.Tech",location="Remote",application_deadline=timezone.localdate(),created_by=self.hr); self.job.required_skills.set([self.python,self.django])
    def test_authentication_and_dashboards(self):
        self.assertTrue(self.client.login(username="cand",password="pass")); self.assertRedirects(self.client.get(reverse("dashboard")),reverse("candidate_dashboard"))
        self.client.logout(); self.assertTrue(self.client.login(username="hr",password="pass")); self.assertRedirects(self.client.get(reverse("dashboard")),reverse("recruiter_dashboard"))
    def test_candidate_registration(self):
        response=self.client.post(reverse("register_candidate"),{"username":"new","first_name":"New","last_name":"User","email":"n@t.com","password1":"StrongPass123!","password2":"StrongPass123!"})
        self.assertRedirects(response,reverse("profile_edit")); self.assertTrue(CandidateProfile.objects.filter(user__username="new").exists())
    def test_job_creation_recruiter_only(self):
        self.client.login(username="cand",password="pass"); self.assertRedirects(self.client.get(reverse("job_create")),reverse("dashboard"),fetch_redirect_response=False)
        self.client.logout(); self.client.login(username="hr",password="pass")
        data={"title":"API Developer","department":"IT","description":"Build API","required_skill_text":"Python, REST API","preferred_skill_text":"Git","required_experience":"1 year","education_requirement":"Degree","location":"Pune","employment_type":"full_time","salary_range":"4 LPA","application_deadline":"2030-01-01","status":"open"}
        self.client.post(reverse("job_create"),data); self.assertTrue(Job.objects.filter(title="API Developer").exists())
    def test_resume_upload_and_duplicate_application_prevention(self):
        self.client.login(username="cand",password="pass")
        app=Application.objects.create(candidate=self.profile,job=self.job,resume=self.resume)
        self.assertContains(self.client.get(reverse("job_detail",args=[self.job.pk])),"Already applied")
        with self.assertRaises(Exception): Application.objects.create(candidate=self.profile,job=self.job,resume=self.resume)
    def test_recruiter_status_update(self):
        app=Application.objects.create(candidate=self.profile,job=self.job,resume=self.resume)
        self.client.login(username="hr",password="pass")
        response=self.client.post(reverse("update_status",args=[app.pk]),{"status":"shortlisted"})
        self.assertJSONEqual(response.content,{"ok":True,"label":"Shortlisted"}); app.refresh_from_db(); self.assertEqual(app.status,"shortlisted")
    @override_settings(OPENROUTER_API_KEY="test",OPENROUTER_MODEL="test/model")
    @patch("recruitment.services.requests.post")
    def test_ai_response_parsing_and_storage_shape(self,mock_post):
        app=Application.objects.create(candidate=self.profile,job=self.job,resume=self.resume)
        payload={"match_score":88,"matching_skills":["Python","Django"],"missing_skills":["Git"],"relevant_experience":"Relevant","relevant_projects":["ATS"],"strengths":["Backend"],"concerns":["Limited scale"],"explanation":"Strong job-related match."}
        response=Mock(); response.raise_for_status.return_value=None; response.json.return_value={"choices":[{"message":{"content":__import__("json").dumps(payload)}}]}; mock_post.return_value=response
        result=analyze_application_with_ai(app); self.assertEqual(result["match_score"],88); self.assertEqual(result["missing_skills"],["Git"])
