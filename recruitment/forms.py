from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import CandidateProfile, Job, Application, Resume, Skill, Interview

def skill_names(qs): return ", ".join(qs.values_list("name", flat=True))
def save_skills(instance, text, field_name):
    skills=[]
    for name in [x.strip() for x in text.split(",") if x.strip()]:
        skill,_=Skill.objects.get_or_create(name__iexact=name, defaults={"name": name.title()})
        skills.append(skill)
    getattr(instance, field_name).set(skills)

class StyledFormMixin:
    def style_fields(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput): field.widget.attrs["class"]="form-check-input"
            else: field.widget.attrs["class"]="form-control" if not isinstance(field.widget, forms.Select) else "form-select"

class CandidateRegistrationForm(UserCreationForm, StyledFormMixin):
    email=forms.EmailField(required=True)
    first_name=forms.CharField(max_length=50)
    last_name=forms.CharField(max_length=50)
    class Meta(UserCreationForm.Meta): fields=("username","first_name","last_name","email","password1","password2")
    def __init__(self,*a,**kw): super().__init__(*a,**kw); self.style_fields()
    def save(self,commit=True):
        user=super().save(commit=False); user.email=self.cleaned_data["email"]; user.first_name=self.cleaned_data["first_name"]; user.last_name=self.cleaned_data["last_name"]
        if commit: user.save(); CandidateProfile.objects.get_or_create(user=user)
        return user

class CandidateProfileForm(forms.ModelForm, StyledFormMixin):
    skill_text=forms.CharField(label="Skills (comma-separated)", required=False, widget=forms.TextInput(attrs={"placeholder":"Python, Django, SQL, Git"}))
    class Meta:
        model=CandidateProfile
        fields=("phone","education","skill_text","experience","projects","certifications","location")
        widgets={k:forms.Textarea(attrs={"rows":3}) for k in ["education","experience","projects","certifications"]}
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw); self.style_fields()
        if self.instance.pk: self.fields["skill_text"].initial=skill_names(self.instance.skills)
    def save(self,commit=True):
        obj=super().save(commit)
        if obj.pk: save_skills(obj,self.cleaned_data["skill_text"],"skills")
        return obj

class ResumeForm(forms.ModelForm, StyledFormMixin):
    class Meta: model=Resume; fields=("file",)
    def __init__(self,*a,**kw): super().__init__(*a,**kw); self.style_fields(); self.fields["file"].widget.attrs["accept"]="application/pdf"
    def clean_file(self):
        f=self.cleaned_data["file"]
        if f.size>5*1024*1024: raise forms.ValidationError("PDF must be 5 MB or smaller.")
        if not f.name.lower().endswith(".pdf"): raise forms.ValidationError("Only PDF resumes are supported.")
        return f

class JobForm(forms.ModelForm, StyledFormMixin):
    required_skill_text=forms.CharField(label="Required skills", widget=forms.TextInput(attrs={"placeholder":"Python, Django, REST API, SQL, Git"}))
    preferred_skill_text=forms.CharField(label="Preferred skills", required=False)
    class Meta:
        model=Job
        fields=("title","department","description","required_skill_text","preferred_skill_text","required_experience","education_requirement","location","employment_type","salary_range","application_deadline","status")
        widgets={"description":forms.Textarea(attrs={"rows":5}),"application_deadline":forms.DateInput(attrs={"type":"date"})}
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw); self.style_fields()
        if self.instance.pk:
            self.fields["required_skill_text"].initial=skill_names(self.instance.required_skills)
            self.fields["preferred_skill_text"].initial=skill_names(self.instance.preferred_skills)
    def save(self,commit=True):
        obj=super().save(commit)
        if obj.pk:
            save_skills(obj,self.cleaned_data["required_skill_text"],"required_skills")
            save_skills(obj,self.cleaned_data["preferred_skill_text"],"preferred_skills")
        return obj

class ApplicationForm(forms.ModelForm, StyledFormMixin):
    class Meta: model=Application; fields=("resume","cover_letter"); widgets={"cover_letter":forms.Textarea(attrs={"rows":5})}
    def __init__(self,*a,candidate=None,**kw):
        super().__init__(*a,**kw); self.style_fields()
        if candidate: self.fields["resume"].queryset=candidate.resumes.all()

class StatusUpdateForm(forms.ModelForm, StyledFormMixin):
    class Meta: model=Application; fields=("status","recruiter_notes")
    def __init__(self,*a,**kw): super().__init__(*a,**kw); self.style_fields(); self.fields["recruiter_notes"].widget=forms.Textarea(attrs={"class":"form-control","rows":4})

class InterviewForm(forms.ModelForm, StyledFormMixin):
    class Meta: model=Interview; fields=("scheduled_at","mode","location_or_link","notes"); widgets={"scheduled_at":forms.DateTimeInput(attrs={"type":"datetime-local"}),"notes":forms.Textarea(attrs={"rows":3})}
    def __init__(self,*a,**kw): super().__init__(*a,**kw); self.style_fields()

class RecruiterAddCandidateForm(forms.Form, StyledFormMixin):
    first_name=forms.CharField(max_length=50); last_name=forms.CharField(max_length=50); email=forms.EmailField(); phone=forms.CharField(max_length=20,required=False); skills=forms.CharField(required=False); resume=forms.FileField(required=False)
    def __init__(self,*a,**kw): super().__init__(*a,**kw); self.style_fields()
