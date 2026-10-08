from django.urls import path
from . import views
urlpatterns=[
 path("",views.landing,name="landing"), path("register/",views.register_candidate,name="register_candidate"), path("dashboard/",views.dashboard,name="dashboard"),
 path("candidate/",views.candidate_dashboard,name="candidate_dashboard"), path("candidate/profile/",views.profile_edit,name="profile_edit"),
 path("jobs/",views.job_list,name="job_list"), path("jobs/<int:pk>/",views.job_detail,name="job_detail"), path("jobs/<int:pk>/apply/",views.apply_job,name="apply_job"),
 path("hr/",views.recruiter_dashboard,name="recruiter_dashboard"), path("hr/jobs/new/",views.job_manage,name="job_create"), path("hr/jobs/<int:pk>/edit/",views.job_manage,name="job_edit"), path("hr/jobs/<int:pk>/delete/",views.job_delete,name="job_delete"), path("hr/jobs/<int:pk>/candidates/",views.job_candidates,name="job_candidates"),
 path("hr/candidates/",views.candidate_list,name="candidate_list"), path("hr/candidates/add/",views.add_candidate,name="add_candidate"), path("hr/candidates/<int:pk>/",views.candidate_detail,name="candidate_detail"),
 path("hr/applications/<int:pk>/",views.application_detail,name="application_detail"), path("hr/applications/<int:pk>/analyze/",views.analyze_application,name="analyze_application"), path("hr/applications/<int:pk>/status/",views.update_status,name="update_status"), path("hr/applications/<int:pk>/interview/",views.schedule_interview,name="schedule_interview"), path("hr/pipeline/",views.pipeline,name="pipeline"),
]
