from io import BytesIO
from datetime import timedelta
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from pypdf import PdfWriter
from recruitment.models import *

def pdf_bytes(title):
    stream=BytesIO(); writer=PdfWriter(); writer.add_blank_page(width=612,height=792); writer.add_metadata({"/Title":title}); writer.write(stream); return stream.getvalue()

class Command(BaseCommand):
    help="Create demo recruiter, candidates, jobs and applications"
    def handle(self,*args,**opts):
        hr,_=User.objects.get_or_create(username="recruiter",defaults={"first_name":"Priya","last_name":"Sharma","email":"hr@talentiq.demo","is_staff":True})
        hr.set_password("HR@123"); hr.is_staff=True; hr.save(); RecruiterProfile.objects.get_or_create(user=hr)
        skills={}
        for name in ["Python","Django","REST API","SQL","Git","HTML","CSS","JavaScript","Docker","PostgreSQL"]: skills[name],_=Skill.objects.get_or_create(name=name)
        job,_=Job.objects.get_or_create(title="Python Django Developer",defaults={"department":"Engineering","description":"Build and maintain secure Django web applications, REST APIs and database-backed internal systems. Collaborate using Git and write maintainable code.","required_experience":"1-2 years","education_requirement":"Computer Science / IT or equivalent","location":"Bengaluru / Hybrid","employment_type":"full_time","salary_range":"₹4.5–7 LPA","application_deadline":timezone.localdate()+timedelta(days=30),"status":"open","created_by":hr})
        job.required_skills.set([skills[x] for x in ["Python","Django","REST API","SQL","Git"]]); job.preferred_skills.set([skills["Docker"],skills["PostgreSQL"]])
        second,_=Job.objects.get_or_create(title="Frontend Developer Intern",defaults={"department":"Product Engineering","description":"Create responsive interfaces with HTML, CSS and JavaScript.","required_experience":"0-1 year","education_requirement":"Any technical degree","location":"Remote","employment_type":"internship","salary_range":"₹20,000/month","application_deadline":timezone.localdate()+timedelta(days=21),"status":"open","created_by":hr}); second.required_skills.set([skills["HTML"],skills["CSS"],skills["JavaScript"]])
        data=[("candidate","Arjun","Mehta","arjun@demo.com",["Python","Django","SQL","Git","HTML","CSS"],"1 year building Django applications and automation tools.","Django e-commerce website with authentication and payments. Telegram automation bot."),("candidate2","Neha","Iyer","neha@demo.com",["Python","SQL","JavaScript"],"Six months of Python scripting and web development.","Student attendance dashboard and portfolio website.")]
        for idx,(username,first,last,email,skill_list,experience,projects) in enumerate(data):
            user,_=User.objects.get_or_create(username=username,defaults={"first_name":first,"last_name":last,"email":email}); user.set_password("Candidate@123"); user.save()
            profile,_=CandidateProfile.objects.get_or_create(user=user,defaults={"phone":"9876543210","education":"B.Tech Computer Engineering","experience":experience,"projects":projects,"certifications":"Python Fundamentals","location":"Bengaluru"})
            profile.skills.set([skills[x] for x in skill_list])
            resume=profile.resumes.first()
            if not resume:
                resume=Resume(candidate=profile,original_name=f"{username}_resume.pdf",extracted_text=f"Skills: {', '.join(skill_list)}. Experience: {experience} Projects: {projects}")
                resume.file.save(f"{username}_resume.pdf",ContentFile(pdf_bytes(f"Resume - {first} {last}")),save=True)
            app,_=Application.objects.get_or_create(candidate=profile,job=job,defaults={"resume":resume,"cover_letter":"I am interested in this role and believe my project experience is relevant.","status":"under_review" if idx==0 else "applied"})
        self.stdout.write(self.style.SUCCESS("Demo data ready: recruiter / HR@123 and candidate / Candidate@123"))
