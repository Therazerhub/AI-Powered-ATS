from django.contrib import admin
from .models import Skill,CandidateProfile,RecruiterProfile,Resume,Job,Application,AIAnalysis,RecruiterNote,Interview
for model in [Skill,CandidateProfile,RecruiterProfile,Resume,Job,Application,AIAnalysis,RecruiterNote,Interview]: admin.site.register(model)
admin.site.site_header="AI-Powered ATS Administration"
