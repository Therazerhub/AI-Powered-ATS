import json
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .decorators import candidate_required, recruiter_required
from .forms import CandidateRegistrationForm, CandidateProfileForm, ResumeForm, JobForm, ApplicationForm, StatusUpdateForm, InterviewForm, RecruiterAddCandidateForm, save_skills
from .models import CandidateProfile, RecruiterProfile, Resume, Job, Application, AIAnalysis, Interview
from .services import extract_pdf_text, analyze_application_with_ai

def landing(request): return render(request,"recruitment/landing.html",{"open_jobs":Job.objects.filter(status="open")[:3]})

def register_candidate(request):
    if request.user.is_authenticated: return redirect("dashboard")
    form=CandidateRegistrationForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        user=form.save(); login(request,user); messages.success(request,"Account created. Complete your candidate profile."); return redirect("profile_edit")
    return render(request,"registration/register.html",{"form":form})

@login_required
def dashboard(request):
    if request.user.is_staff or hasattr(request.user,"recruiter_profile"): return redirect("recruiter_dashboard")
    return redirect("candidate_dashboard")

@candidate_required
def candidate_dashboard(request):
    profile=request.user.candidate_profile
    applications=profile.applications.select_related("job").all()
    jobs=Job.objects.filter(status="open",application_deadline__gte=timezone.localdate()).exclude(applications__candidate=profile)[:5]
    return render(request,"recruitment/candidate_dashboard.html",{"profile":profile,"applications":applications,"jobs":jobs})

@candidate_required
def profile_edit(request):
    profile=request.user.candidate_profile
    form=CandidateProfileForm(request.POST or None,instance=profile)
    resume_form=ResumeForm(request.POST or None,request.FILES or None)
    if request.method=="POST" and form.is_valid() and ("file" not in request.FILES or resume_form.is_valid()):
        form.save()
        if request.FILES.get("file"):
            profile.resumes.update(is_active=False)
            resume=resume_form.save(commit=False); resume.candidate=profile; resume.original_name=resume.file.name; resume.save()
            try: resume.extracted_text=extract_pdf_text(resume.file.path); resume.save(update_fields=["extracted_text"])
            except Exception as exc: messages.warning(request,f"Resume uploaded, but text extraction failed: {exc}")
        messages.success(request,"Profile updated."); return redirect("candidate_dashboard")
    return render(request,"recruitment/profile_form.html",{"form":form,"resume_form":resume_form,"profile":profile})

def job_list(request):
    jobs=Job.objects.filter(status="open",application_deadline__gte=timezone.localdate()).annotate(applicant_count=Count("applications"))
    query=request.GET.get("q","")
    if query: jobs=jobs.filter(Q(title__icontains=query)|Q(department__icontains=query)|Q(location__icontains=query))
    return render(request,"recruitment/job_list.html",{"jobs":jobs,"query":query})

def job_detail(request,pk):
    job=get_object_or_404(Job.objects.prefetch_related("required_skills","preferred_skills"),pk=pk)
    applied=False
    if request.user.is_authenticated and hasattr(request.user,"candidate_profile"): applied=Application.objects.filter(job=job,candidate=request.user.candidate_profile).exists()
    return render(request,"recruitment/job_detail.html",{"job":job,"applied":applied})

@candidate_required
def apply_job(request,pk):
    job=get_object_or_404(Job,pk=pk,status="open")
    candidate=request.user.candidate_profile
    if Application.objects.filter(job=job,candidate=candidate).exists(): messages.warning(request,"You already applied for this job."); return redirect("job_detail",pk=pk)
    form=ApplicationForm(request.POST or None,candidate=candidate,initial={"resume":candidate.active_resume})
    if request.method=="POST" and form.is_valid():
        app=form.save(commit=False); app.job=job; app.candidate=candidate
        try: app.save()
        except IntegrityError: messages.warning(request,"Duplicate application prevented."); return redirect("job_detail",pk=pk)
        messages.success(request,"Application submitted successfully."); return redirect("candidate_dashboard")
    return render(request,"recruitment/application_form.html",{"form":form,"job":job})

@recruiter_required
def recruiter_dashboard(request):
    applications=Application.objects.select_related("candidate__user","job")
    stats={"open_jobs":Job.objects.filter(status="open").count(),"applications":applications.count(),"under_review":applications.filter(status="under_review").count(),"shortlisted":applications.filter(status="shortlisted").count(),"interviews":applications.filter(status="interview").count(),"selected":applications.filter(status="selected").count()}
    jobs=Job.objects.annotate(applicant_count=Count("applications"),shortlisted_count=Count("applications",filter=Q(applications__status="shortlisted")),interview_count=Count("applications",filter=Q(applications__status="interview")))[:8]
    return render(request,"recruitment/recruiter_dashboard.html",{"stats":stats,"jobs":jobs,"recent":applications[:6]})

@recruiter_required
def job_manage(request,pk=None):
    job=get_object_or_404(Job,pk=pk) if pk else None
    form=JobForm(request.POST or None,instance=job)
    if request.method=="POST" and form.is_valid():
        obj=form.save(commit=False)
        if not obj.pk: obj.created_by=request.user
        obj.save(); form.instance=obj; form.save()
        messages.success(request,"Job saved."); return redirect("recruiter_dashboard")
    return render(request,"recruitment/job_form.html",{"form":form,"job":job})

@require_POST
@recruiter_required
def job_delete(request,pk):
    job=get_object_or_404(Job,pk=pk); job.delete(); messages.success(request,"Job deleted."); return redirect("recruiter_dashboard")

@recruiter_required
def candidate_list(request):
    candidates=CandidateProfile.objects.select_related("user").prefetch_related("skills").annotate(application_count=Count("applications"))
    q=request.GET.get("q","")
    if q: candidates=candidates.filter(Q(user__first_name__icontains=q)|Q(user__last_name__icontains=q)|Q(user__email__icontains=q)|Q(skills__name__icontains=q)).distinct()
    return render(request,"recruitment/candidate_list.html",{"candidates":candidates,"query":q})

@recruiter_required
def add_candidate(request):
    form=RecruiterAddCandidateForm(request.POST or None,request.FILES or None)
    if request.method=="POST" and form.is_valid():
        base=form.cleaned_data["email"].split("@")[0]; username=base; i=1
        while User.objects.filter(username=username).exists(): username=f"{base}{i}"; i+=1
        user=User.objects.create_user(username=username,email=form.cleaned_data["email"],first_name=form.cleaned_data["first_name"],last_name=form.cleaned_data["last_name"],password="Candidate@123")
        profile=CandidateProfile.objects.create(user=user,phone=form.cleaned_data["phone"]); save_skills(profile,form.cleaned_data["skills"],"skills")
        if form.cleaned_data.get("resume"):
            resume=Resume.objects.create(candidate=profile,file=form.cleaned_data["resume"],original_name=form.cleaned_data["resume"].name)
            try: resume.extracted_text=extract_pdf_text(resume.file.path); resume.save(update_fields=["extracted_text"])
            except Exception: pass
        messages.success(request,"Candidate added. Temporary password: Candidate@123"); return redirect("candidate_detail",pk=profile.pk)
    return render(request,"recruitment/add_candidate.html",{"form":form})

@recruiter_required
def candidate_detail(request,pk):
    candidate=get_object_or_404(CandidateProfile.objects.select_related("user").prefetch_related("skills"),pk=pk)
    return render(request,"recruitment/candidate_detail.html",{"candidate":candidate,"applications":candidate.applications.select_related("job")})

@recruiter_required
def job_candidates(request,pk):
    job=get_object_or_404(Job,pk=pk)
    applications=job.applications.select_related("candidate__user","resume").order_by("-ai_match_score","-applied_at")
    return render(request,"recruitment/job_candidates.html",{"job":job,"applications":applications})

@recruiter_required
def application_detail(request,pk):
    app=get_object_or_404(Application.objects.select_related("candidate__user","job","resume"),pk=pk)
    form=StatusUpdateForm(request.POST or None,instance=app)
    interview=getattr(app,"interview_details",None); interview_form=InterviewForm(prefix="interview",instance=interview)
    if request.method=="POST" and form.is_valid(): form.save(); messages.success(request,"Application updated."); return redirect("application_detail",pk=pk)
    return render(request,"recruitment/application_detail.html",{"application":app,"form":form,"interview_form":interview_form})

@require_POST
@recruiter_required
def analyze_application(request,pk):
    app=get_object_or_404(Application,pk=pk)
    try:
        data=analyze_application_with_ai(app)
        app.ai_match_score=data["match_score"]; app.ai_analysis=data; app.save(update_fields=["ai_match_score","ai_analysis","updated_at"])
        AIAnalysis.objects.update_or_create(application=app,defaults={"match_score":data["match_score"],"matching_skills":data["matching_skills"],"missing_skills":data["missing_skills"],"relevant_experience":data["relevant_experience"],"relevant_projects":data["relevant_projects"],"strengths":data["strengths"],"concerns":data["concerns"],"explanation":data["explanation"],"model_name":__import__("django.conf").conf.settings.OPENROUTER_MODEL})
        if request.headers.get("x-requested-with")=="XMLHttpRequest": return JsonResponse({"ok":True,"score":data["match_score"]})
        messages.success(request,"Live AI analysis completed.")
    except Exception as exc:
        if request.headers.get("x-requested-with")=="XMLHttpRequest": return JsonResponse({"ok":False,"error":str(exc)},status=502)
        messages.error(request,f"AI analysis failed: {exc}")
    return redirect("application_detail",pk=pk)

@require_POST
@recruiter_required
def update_status(request,pk):
    app=get_object_or_404(Application,pk=pk); status=request.POST.get("status")
    if status not in dict(Application.STATUS): return JsonResponse({"ok":False,"error":"Invalid status"},status=400)
    app.status=status; app.save(update_fields=["status","updated_at"])
    return JsonResponse({"ok":True,"label":app.get_status_display()})

@require_POST
@recruiter_required
def schedule_interview(request,pk):
    app=get_object_or_404(Application,pk=pk); existing=getattr(app,"interview_details",None)
    form=InterviewForm(request.POST,prefix="interview",instance=existing)
    if form.is_valid():
        obj=form.save(commit=False); obj.application=app; obj.updated_by=request.user; obj.save(); app.status="interview"; app.save(update_fields=["status","updated_at"]); messages.success(request,"Interview scheduled.")
    else: messages.error(request,"Please correct the interview details.")
    return redirect("application_detail",pk=pk)

@recruiter_required
def pipeline(request):
    columns=[(key,label,Application.objects.filter(status=key).select_related("candidate__user","job")) for key,label in Application.STATUS]
    return render(request,"recruitment/pipeline.html",{"columns":columns})
