import json, re
from pathlib import Path
import requests
from django.conf import settings
from pypdf import PdfReader

SYSTEM_PROMPT = """You are a recruitment analysis assistant. Compare only job-related qualifications: skills, experience, education, projects, and certifications. Never infer or use age, gender, race, religion, caste, disability, health, political beliefs, marital status, or other protected traits. Your score is advisory, not a hiring decision. Return only valid JSON."""

def extract_pdf_text(file_path):
    reader=PdfReader(str(file_path))
    text="\n".join(page.extract_text() or "" for page in reader.pages)
    return text.strip()[:30000]

def candidate_payload(application):
    c=application.candidate; j=application.job
    return {
        "candidate":{"skills":list(c.skills.values_list("name",flat=True)),"education":c.education,"experience":c.experience,"projects":c.projects,"certifications":c.certifications,"resume_text":application.resume.extracted_text[:18000]},
        "job":{"title":j.title,"description":j.description,"required_skills":list(j.required_skills.values_list("name",flat=True)),"preferred_skills":list(j.preferred_skills.values_list("name",flat=True)),"required_experience":j.required_experience,"education_requirement":j.education_requirement},
    }

def _extract_json(text):
    text=text.strip()
    text=re.sub(r"^```(?:json)?\s*|\s*```$","",text,flags=re.I)
    try:return json.loads(text)
    except json.JSONDecodeError:
        match=re.search(r"\{[\s\S]*\}",text)
        if not match: raise ValueError("AI response did not contain valid JSON")
        return json.loads(match.group(0))

def analyze_application_with_ai(application):
    if not settings.OPENROUTER_API_KEY: raise RuntimeError("OPENROUTER_API_KEY is not configured")
    if not application.resume.extracted_text and application.resume.file:
        application.resume.extracted_text=extract_pdf_text(application.resume.file.path)
        application.resume.save(update_fields=["extracted_text"])
    schema={"match_score":"integer 0-100","matching_skills":["skill"],"missing_skills":["skill"],"relevant_experience":"short text","relevant_projects":["project"],"strengths":["strength"],"concerns":["job-related concern"],"explanation":"2-4 sentences"}
    prompt=f"Compare this anonymized candidate with this job. Return exactly this JSON shape: {json.dumps(schema)}\n\nDATA:\n{json.dumps(candidate_payload(application),ensure_ascii=False)}"
    response=requests.post("https://openrouter.ai/api/v1/chat/completions",headers={"Authorization":f"Bearer {settings.OPENROUTER_API_KEY}","Content-Type":"application/json","HTTP-Referer":"http://localhost:8000","X-Title":"AI-Powered ATS College Project"},json={"model":settings.OPENROUTER_MODEL,"messages":[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}],"temperature":0.1,"max_tokens":2000,"response_format":{"type":"json_object"}},timeout=90)
    response.raise_for_status()
    content=response.json()["choices"][0]["message"]["content"]
    data=_extract_json(content)
    required=["match_score","matching_skills","missing_skills","relevant_experience","relevant_projects","strengths","concerns","explanation"]
    if any(k not in data for k in required): raise ValueError("AI returned incomplete analysis")
    data["match_score"]=max(0,min(100,int(data["match_score"])))
    for key in ["matching_skills","missing_skills","relevant_projects","strengths","concerns"]:
        if not isinstance(data[key],list): data[key]=[str(data[key])]
    return data
