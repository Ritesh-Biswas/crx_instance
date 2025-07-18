from django.urls import path
from .views import UserProfileListView, UserProfileDetailView, WorkAnniversariesView, RecentHiresView, OrgChartView, WorkdayAdminPunchView, follow_toggle, department_follow_toggle

app_name = 'custom_user'

urlpatterns = [
    path('api/profiles/', UserProfileListView.as_view(), name='profile-list'),
    path('api/profiles/<str:username>/', UserProfileDetailView.as_view(), name='profile-detail'),
    path('api/recent-hires/', RecentHiresView.as_view(), name='recent-hires'),
    path('api/work-anniversaries/', WorkAnniversariesView.as_view(), name='work-anniversaries'),
    path('org-chart/<str:username>/', OrgChartView.as_view(), name='org_chart'),
    path("workday/punch/", WorkdayAdminPunchView.as_view(), name="workday-punch"),
    path('follow-toggle/<str:username>/', follow_toggle, name='follow_toggle'),
    path('follow-department-toggle/<slug:slug>/', department_follow_toggle, name='department_follow_toggle'),
]
