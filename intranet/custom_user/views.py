from django.http import JsonResponse
from django.views import View
from .models import UserExtraProfile
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from .utils import punch_employee
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import UserExtraProfile, User
from home.models import SubDepartmentPage
from django.http import JsonResponse, HttpResponseBadRequest

class UserProfileListView(View):
    def get(self, request):
        profiles = UserExtraProfile.objects.select_related('user', 'manager__user').all().order_by('-joining_date')
        profiles_data = [
            {
                'username': profile.user.username,
                'email': profile.user.email,
                'about': profile.about,
                'designation': profile.designation,
                'expertise': [tag.name for tag in profile.expertise.all()],
                'joining_date': profile.joining_date.isoformat() if profile.joining_date else None,
                'manager': profile.manager.user.username if profile.manager else None,
            }
            for profile in profiles
        ]
        return JsonResponse({'profiles': profiles_data})

class UserProfileDetailView(View):
    def get(self, request, username):
        profile = get_object_or_404(
            UserExtraProfile.objects.select_related('user', 'manager__user'),
            user__username=username
        )
        wagtail_profile = getattr(profile.user, 'wagtail_userprofile', None)
        cover_photo_url = (
            profile.cover_photo.file.url
            if profile.cover_photo and profile.cover_photo.file and profile.cover_photo.file.url
            else None
        )
        profile_picture_url = (
            wagtail_profile.avatar.url
            if wagtail_profile and wagtail_profile.avatar
            else None
        )

        # Manager info
        manager_data = None
        if profile.manager:
            manager_wagtail_profile = getattr(profile.manager.user, 'wagtail_userprofile', None)
            manager_data = {
                'username': profile.manager.user.username,
                'full_name': f"{profile.manager.user.first_name} {profile.manager.user.last_name}".strip()
                             or profile.manager.user.username,
                'profile_picture': manager_wagtail_profile.avatar.url
                                   if manager_wagtail_profile and manager_wagtail_profile.avatar else None,
                'designation': profile.manager.designation or "No designation specified"
            }

        # Current user follow check
        current_user_profile = UserExtraProfile.objects.get(user=request.user)

        # Check if current user is following the profile
        is_following = current_user_profile.following_users.filter(pk=profile.pk).exists()

        # Followers of this profile (other users who follow this profile)
        followers_list = profile.user_followers.all()
        follower_count = followers_list.count()

        # Users this profile is following
        following_list = profile.following_users.all()
        following_count = following_list.count()

        context = {
            'full_name': f"{profile.user.first_name} {profile.user.last_name}".strip(),
            'username': profile.user.username,
            'email': profile.user.email,
            'profile_picture': profile_picture_url,
            'about': profile.about,
            'designation': profile.designation,
            'expertise': [tag.name for tag in profile.expertise.all()],
            'joining_date': profile.joining_date,
            'date_of_birth': profile.date_of_birth,
            'cover_photo': cover_photo_url,
            'manager': manager_data,
            'subordinates': [{
                'username': sub.user.username,
                'full_name': f"{sub.user.first_name} {sub.user.last_name}".strip() or sub.user.username,
                'designation': sub.designation or "No designation specified"
            } for sub in profile.subordinates.all()],
            'employee_number': profile.employee_number,

            # Follow context
            'is_following': is_following,
            'follower_count': follower_count,
            'followers_list': followers_list,
            'following_list': following_list, 
            'following_count': following_count,
        }

        return render(request, 'custom_user/profile_detail.html', context)

class RecentHiresView(View):
    def get(self, request):
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_hires = UserExtraProfile.objects.filter(
            joining_date__gte=thirty_days_ago
        ).select_related('user')

        profiles_data = []
        for profile in recent_hires:
            full_name = f"{profile.user.first_name} {profile.user.last_name}".strip()
            wagtail_profile = getattr(profile.user, 'wagtail_userprofile', None)
            profile_picture = wagtail_profile.avatar.url if wagtail_profile and wagtail_profile.avatar else None

            profiles_data.append({
                'username': profile.user.username,
                'full_name': full_name or profile.user.username,
                'profile_picture': profile_picture,
                'designation': profile.designation,
                'joining_date': profile.joining_date.strftime('%Y-%m-%d') if profile.joining_date else None,
            })

        return JsonResponse({'profiles': profiles_data})

class WorkAnniversariesView(View):
    def get(self, request):
        today = timezone.now().date()
        profiles = UserExtraProfile.objects.filter(
            joining_date__isnull=False
        ).select_related('user')

        anniversary_profiles = []
        for profile in profiles:
            if not profile.joining_date:
                continue

            try:
                this_year_anniversary = profile.joining_date.replace(year=today.year)
            except ValueError:
                continue

            if this_year_anniversary < today:
                this_year_anniversary = profile.joining_date.replace(year=today.year + 1)

            years_of_service = relativedelta(this_year_anniversary, profile.joining_date).years

            if years_of_service > 0 and this_year_anniversary.month == today.month and this_year_anniversary.day >= today.day:
                wagtail_profile = getattr(profile.user, 'wagtail_userprofile', None)
                profile_picture = wagtail_profile.avatar.url if wagtail_profile and wagtail_profile.avatar else None

                anniversary_profiles.append({
                    'username': profile.user.username,
                    'full_name': f"{profile.user.first_name} {profile.user.last_name}".strip(),
                    'profile_picture': profile_picture,
                    'hire_date': profile.joining_date.strftime('%Y-%m-%d'),
                    'years_of_service': years_of_service,
                    'anniversary_date': this_year_anniversary.strftime('%Y-%m-%d')
                })

        return JsonResponse(anniversary_profiles, safe=False)

class OrgChartView(View):
    def get(self, request, username):
        profile = get_object_or_404(UserExtraProfile.objects.select_related('user', 'manager__user'), user__username=username)
        
        def get_subordinates_data(profile):
            wagtail_profile = getattr(profile.user, 'wagtail_userprofile', None)
            return {
                'username': profile.user.username,
                'name': f"{profile.user.first_name} {profile.user.last_name}".strip() or profile.user.username,
                'designation': profile.designation or "No designation specified",
                'profile_picture': wagtail_profile.avatar.url if wagtail_profile and wagtail_profile.avatar else '/static/img/default.png',
                'children': [get_subordinates_data(sub) for sub in profile.subordinates.all()]
            }

        def get_managers_chain(profile):
            chain = []
            current = profile
            while current.manager:
                wagtail_profile = getattr(current.manager.user, 'wagtail_userprofile', None)
                manager_data = {
                    'username': current.manager.user.username,
                    'name': f"{current.manager.user.first_name} {current.manager.user.last_name}".strip() or current.manager.user.username,
                    'designation': current.manager.designation or "No designation specified",
                    'profile_picture': wagtail_profile.avatar.url if wagtail_profile and wagtail_profile.avatar else '/static/img/default.png',
                }
                chain.append(manager_data)
                current = current.manager
            return chain

        # Get initial profile data
        wagtail_profile = getattr(profile.user, 'wagtail_userprofile', None)
        profile_data = {
            'username': profile.user.username,
            'name': f"{profile.user.first_name} {profile.user.last_name}".strip() or profile.user.username,
            'designation': profile.designation or "No designation specified",
            'profile_picture': wagtail_profile.avatar.url if wagtail_profile and wagtail_profile.avatar else '/static/img/default.png',
            'children': [get_subordinates_data(sub) for sub in profile.subordinates.all()]
        }

        context = {
            'profile': profile_data,
            'managers_chain': get_managers_chain(profile),
            'selected_user': username
        }
        return render(request, 'custom_user/org_chart.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class WorkdayAdminPunchView(View):
    def post(self, request):
        try:
            print("Request body:", request.body)  # Debugging line
            print("Request method:", request.method)  # Debugging line
            print("Request headers:", request.headers)  # Debugging line
            data = json.loads(request.body)
            employee_number = data.get("employee_number")
            action = data.get("action", "").lower()

            if not employee_number or not action:
                return JsonResponse({"success": False, "message": "Missing employee_number or action"}, status=400)

            if action not in ["checkin", "checkout"]:
                return JsonResponse({"success": False, "message": "Invalid action"}, status=400)

            event_type = "IN" if action == "checkin" else "OUT"

            success, message = punch_employee(employee_number, event_type)

            return JsonResponse({"success": success, "message": message})

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

@login_required
def follow_toggle(request, username):
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        current_profile = request.user.userextraprofile
        target_user = get_object_or_404(User, username=username)
        target_profile = get_object_or_404(UserExtraProfile, user=target_user)

        if target_profile in current_profile.following_users.all():
            current_profile.unfollow_user(target_profile)
            return JsonResponse({"status": "unfollowed"})
        else:
            current_profile.follow_user(target_profile)
            return JsonResponse({"status": "followed"})
    return HttpResponseBadRequest("Invalid request")

@login_required
def department_follow_toggle(request, slug):
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        user_profile = request.user.userextraprofile
        department = get_object_or_404(SubDepartmentPage, slug=slug)

        if user_profile.is_following_department(department):
            user_profile.unfollow_department(department)
            return JsonResponse({"status": "unfollowed"})
        else:
            user_profile.follow_department(department)
            return JsonResponse({"status": "followed"})

    return HttpResponseBadRequest("Invalid request")