from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

def recruiter_required(view):
    @login_required
    @wraps(view)
    def wrapper(request,*args,**kwargs):
        if request.user.is_staff or hasattr(request.user,"recruiter_profile"): return view(request,*args,**kwargs)
        messages.error(request,"Recruiter access required."); return redirect("dashboard")
    return wrapper

def candidate_required(view):
    @login_required
    @wraps(view)
    def wrapper(request,*args,**kwargs):
        if hasattr(request.user,"candidate_profile"): return view(request,*args,**kwargs)
        messages.error(request,"Candidate access required."); return redirect("dashboard")
    return wrapper
