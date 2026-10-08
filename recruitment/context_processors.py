def role_context(request):
    user=request.user
    return {"is_recruiter": bool(user.is_authenticated and (user.is_staff or hasattr(user,"recruiter_profile"))), "is_candidate": bool(user.is_authenticated and hasattr(user,"candidate_profile"))}
