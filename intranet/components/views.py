from django.shortcuts import render, HttpResponseRedirect, get_object_or_404, redirect #type: ignore
from django.contrib import messages #type: ignore
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import BlogPost, QuillImage, PollOption, PollVote, AuthenticationSettings
from django.views.decorators.csrf import csrf_exempt
from wagtail.users.models import UserProfile
from django.views.generic import DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from django.urls import reverse
from .utils import get_google_drive_files
from home.models import DepartmentPage, SubDepartmentPage
from django.db import models
from django.core.exceptions import PermissionDenied
from django.views import View
from allauth.socialaccount.models import SocialToken
from .utils import get_calendar_events
import requests
from django.utils import timezone
from datetime import datetime, timedelta
import pytz
import logging
from .utils import get_onedrive_files, get_outlook_calendar_events, fetch_calendar_events
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import csv
from django.contrib.auth import get_user_model
from wagtail.documents.models import Document
from django.core.files.base import ContentFile
import io
from django.contrib.auth.hashers import make_password
import string
import random
from wagtail.models import Collection
from custom_media.models import CustomDocument  # Add this import at the top with other imports
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseBadRequest

User = get_user_model()


@login_required
def blog_post_create_view(request):
    if request.method == 'POST':
        post_type = request.POST.get('post_type', 'post')
        title = request.POST.get('title', '')
        body = request.POST.get('body', '')
        subdepartment_id = request.POST.get('subdepartment')

        # Get the UserProfile instance for the current user
        user_profile = UserProfile.objects.get(user=request.user)

        # Create the blog post
        post = BlogPost.objects.create(
            author=user_profile,  # Use the UserProfile instance
            title=title,
            body=body,
            post_type=post_type,
            subdepartment_id=subdepartment_id if subdepartment_id != 'global' else None
        )

        # Handle poll-specific data if it's a poll
        if post_type == 'poll':
            poll_end_time = request.POST.get('poll_end_time')
            poll_options = request.POST.getlist('poll_options[]')
            
            if poll_end_time:
                post.poll_end_time = poll_end_time
                post.save()
            
            for option_text in poll_options:
                if option_text.strip():
                    PollOption.objects.create(post=post, text=option_text)

        # If it's an HTMX request, return just the new post HTML
        if request.headers.get('HX-Request'):
            return render(request, 'components/partials/post_list.html', {
                'posts': [post],
            })

        # For regular requests, return JSON response
        return JsonResponse({
            'status': 'success',
            'message': 'Post created successfully',
            'post_id': post.id
        })

    return HttpResponseBadRequest("Invalid request method")

# Add new views for poll voting
@login_required
@require_POST
def submit_poll_vote(request, post_id):
    try:
        post = BlogPost.objects.get(id=post_id) 

        if not post.is_poll_active:
            return JsonResponse({
                'status': 'error',
                'message': 'This poll has ended'
            }, status=400)


        option_id = request.POST.get('option_id')
        
        # First check if user has already voted

        if PollVote.objects.filter(user=request.user, post=post).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'You have already voted on this poll'
            }, status=400)
        
        
        option = PollOption.objects.get(id=option_id, post=post)
        
        # Create the vote
        PollVote.objects.create(
            user=request.user,
            post=post,
            option=option
        )
        
        # Increment the option's vote count
        option.votes_count += 1
        option.save()
        
        return JsonResponse({
            'status': 'success',
            'votes_count': option.votes_count,
            'percentage': option.votes_percentage
        })
        
    except (BlogPost.DoesNotExist, PollOption.DoesNotExist):
        return JsonResponse({
            'status': 'error',
            'message': 'Poll or option not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def toggle_like_post(request, post_id):
    try:
        post = BlogPost.objects.get(id=post_id)
        user = request.user
        
        # Check if user has already liked the post
        if user in post.likes.all():
            # Unlike the post
            post.likes.remove(user)
            liked = False
        else:
            # Like the post
            post.likes.add(user)
            liked = True
            
        # Update the likes count
        post.update_likes_count()
        
        return JsonResponse({
            'status': 'success',
            'likes_count': post.likes_count,
            'liked': liked
        })
    except BlogPost.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Post not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        uploaded_image = QuillImage.objects.create(image=image)
        return JsonResponse({
            'success': True,
            'url': uploaded_image.image.url
        })
    return JsonResponse({
        'success': False,
        'error': 'No image provided'
    }, status=400)


class BlogPostDetailView(LoginRequiredMixin, DetailView):
    model = BlogPost
    template_name = 'components/blog_post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context if needed
        post = self.get_object()
        
        if post.post_type == 'poll':
            # Add poll-specific context
            context['user_vote'] = PollVote.objects.filter(
                user=self.request.user,
                post=post
            ).first()

        return context

@login_required
def load_more_posts(request):
    page_number = request.GET.get('page', 1)
    user = request.user
    
    posts = BlogPost.objects.all().order_by('-created_at')
    
    if not user.is_superuser and not user.groups.filter(name='Tenant').exists():
        accessible_departments = SubDepartmentPage.objects.filter(
            models.Q(members=user) | models.Q(site_admins=user)
        ).distinct()
        
        posts = posts.filter(
            models.Q(subdepartment__in=accessible_departments) | 
            models.Q(subdepartment__isnull=True)
        )
    
    # Apply filters if request is from HTMX
    if request.headers.get('HX-Request'):
        post_type = request.GET.get('post_type_filter')
        department_id = request.GET.get('department_filter')
        
        if post_type and post_type != 'all':
            posts = posts.filter(post_type=post_type)
        
        if department_id and department_id != 'all':
            posts = posts.filter(subdepartment_id=department_id)
    
    paginator = Paginator(posts, 10)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        if request.headers.get('HX-Request'):
            return HttpResponse('')  # Return empty response for HTMX infinite scroll
        page_obj = paginator.page(paginator.num_pages)
    
    posts_data = []
    for post in page_obj:
        dept_url = ''
        if post.subdepartment:
            dept_url = post.subdepartment.url
        
        total_votes = 0
        is_poll_active = True  # Default value
        if post.post_type.lower() == 'poll':
            total_votes = PollVote.objects.filter(post=post).count()
            # Check if poll is still active
            if post.poll_end_time:
                is_poll_active = post.poll_end_time > timezone.now()
        
        is_liked = user.is_authenticated and post.likes.filter(id=user.id).exists()

        posts_data.append({
            'id': post.id,
            'author': post.author.user.id,
            'author_name': post.author.user.get_full_name(),
            'author_profile_url': reverse('custom_user:profile-detail', kwargs={'username': post.author.user.username}),
            'title': post.title,
            'type': post.post_type,
            'body': post.body,
            'created_at': post.created_at.strftime('%B %d, %Y, %I:%M %p'),
            'likes_count': post.likes_count,
            'comments_count': post.get_comments().count(),
            'sub_department': post.subdepartment.name if post.subdepartment else 'Global',
            'dept_url': dept_url,
            'department_id': post.subdepartment.id if post.subdepartment else 'global',
            'url': reverse('components:blog_post_detail', kwargs={'pk': post.pk}),
            'total_votes': total_votes,
            'is_poll_active': is_poll_active,
            'is_like_by_user': is_liked,  
        })
    
    # Return HTML for HTMX requests
    if request.headers.get('HX-Request'):
        return render(request, 'components/partials/post_list.html', {
            'posts': posts_data
        })
    
    return JsonResponse({'posts': posts_data})


@login_required
def fetch_drive_files(request):
    """Fetch files from Google Drive and return as JSON."""
    files = get_google_drive_files(request)  # Call the function from utils
    return JsonResponse({"files": files})


@login_required
def subdepartment_list_view(request):
    user = request.user
    current_page_id = request.GET.get('page_id')

    if current_page_id:
        try:
            current_page = SubDepartmentPage.objects.get(id=current_page_id)
            subdepartments = [current_page] if current_page.live else []
        except SubDepartmentPage.DoesNotExist:
            subdepartments = SubDepartmentPage.objects.live().specific()
    else:
        subdepartments = SubDepartmentPage.objects.live().specific()
       
    if not user.is_superuser and not user.groups.filter(name="Tenant").exists() and len(subdepartments) > 0:
        user_sub_departments = []
        for sub_department in subdepartments:
            if (
                user in sub_department.members.all()
                or user in sub_department.site_admins.all()
            ):
                user_sub_departments.append(sub_department)
        subdepartments = user_sub_departments

    subdepartments_data = []
    for subdept in subdepartments:
        subdepartments_data.append({
            'id': subdept.id,
            'name': subdept.name,
        })

    return JsonResponse({'subdepartments': subdepartments_data})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    
    # Check permissions
    if not (request.user.is_superuser or post.author.user == request.user or request.user.groups.filter(name="Tenant").exists()):
        raise PermissionDenied
    
    if request.method == "POST":
        # Update title for all post types
        post.title = request.POST.get('title', '')
            
        if post.post_type != 'poll':
            post.body = request.POST.get('body', '')
            
        if post.post_type == 'poll':
            poll_end_time = request.POST.get('poll_end_time')
            if poll_end_time:
                try:
                    # Convert ISO format string to datetime object
                    utc_dt = datetime.fromisoformat(poll_end_time.replace('Z', '+00:00'))
                    post.poll_end_time = utc_dt
                except ValueError as e:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Invalid datetime format: {str(e)}'
                    }, status=400)
                
                # Update poll options
                existing_options = post.poll_options.all()
                new_options = request.POST.getlist('poll_options[]')
                
                # Delete removed options
                existing_options.exclude(text__in=new_options).delete()
                
                # Update or create options
                for option_text in new_options:
                    if option_text.strip():
                        PollOption.objects.update_or_create(
                            post=post,
                            text=option_text.strip()
                        )

        if request.POST.get('subdepartment') != 'global':
            subdepartment = SubDepartmentPage.objects.filter(id=request.POST.get('subdepartment')).first()
            post.subdepartment = subdepartment
        else:
            post.subdepartment = None
            
        post.save()
        return JsonResponse({'status': 'success'})
    
    # For GET requests, filter subdepartments based on user permissions
    user = request.user
    subdepartments = SubDepartmentPage.objects.live().specific()
    
    if not user.is_superuser and not user.groups.filter(name="Tenant").exists():
        subdepartments = subdepartments.filter(
            models.Q(members=user) | models.Q(site_admins=user)
        ).distinct()
    
    response_data = {
        'id': post.id,
        'type': post.post_type,
        'title': post.title,
        'body': post.body or '',
        'subdepartment': post.subdepartment.id if post.subdepartment else 'global',
        'subdepartments': [{'id': dept.id, 'name': dept.name} for dept in subdepartments]
    }
    
    if post.post_type == 'poll':
        response_data.update({
                # Convert to ISO format for consistent handling
                'poll_end_time': post.poll_end_time.isoformat() if post.poll_end_time else None,
                'poll_options': list(post.poll_options.values_list('text', flat=True))
            })
        
    return JsonResponse(response_data)

@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    print(f"USer is moderator: {request.user.groups.filter(name='Tenant').exists()}")
    
    # Check permissions
    if not (request.user.is_superuser or post.author.user == request.user or request.user.groups.filter(name="Tenant").exists()):
        return JsonResponse({
            'status': 'error',
            'message': 'Permission denied'
        }, status=403)
    
    post.delete()
    return JsonResponse({'status': 'success'})


class CalendarEventsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            token = SocialToken.objects.get(
                account__user=request.user,
                account__provider="google"
            )
        except SocialToken.DoesNotExist:
            return JsonResponse({
                'error': 'Google account not linked or token missing. Please authenticate with Google.'
            }, status=403)

        try:
            # Call the utility function with the request
            calendar_data = get_calendar_events(request)

            # Return the calendar data as JSON
            return JsonResponse(calendar_data)
        except requests.exceptions.RequestException as e:
            return JsonResponse({
                'error': f'Failed to fetch Google Calendar events: {str(e)}'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'error': f'An unexpected error occurred: {str(e)}'
            }, status=500)


class OneDriveFilesView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            files = get_onedrive_files(request)  # Fetch OneDrive files using the utility function
            return JsonResponse({"files": files})  # Return the files as JSON
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)  # Handle exceptions and return an error response

class OutlookCalendarEventsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            # First check if Microsoft account is linked
            try:
                SocialToken.objects.get(
                    account__user=request.user,
                    account__provider="microsoft"
                )
            except SocialToken.DoesNotExist:
                return JsonResponse({
                    'error': 'Microsoft account not linked or token missing. Please authenticate with Microsoft.'
                }, status=403)

            # Get calendar events
            calendar_data = get_outlook_calendar_events(request)
            
            # Return the calendar data directly since it's already formatted
            return JsonResponse(calendar_data)
            
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class AuthSettingsView(View):
    def get(self, request):
        settings = AuthenticationSettings.objects.first()
        if settings:
            return JsonResponse({
                'google_client_id': bool(settings.google_client_id),
                'microsoft_client_id': bool(settings.microsoft_client_id),
                'workday_client_id': bool(settings.workday_client_id)
            })
        return JsonResponse({
            'google_client_id': False,
            'microsoft_client_id': False,
            'workday_client_id': False
        })


class PublicCalendarEventsView(View):
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        try:
            calendar_url = request.POST.get('calendar_url')
            if not calendar_url:
                return JsonResponse({"error": "Calendar URL is required."}, status=400)
            
            events = fetch_calendar_events(calendar_url)
            return JsonResponse({"events": events})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)



# Set up logging
logger = logging.getLogger(__name__)

User = get_user_model()

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

@staff_member_required
def import_users_view(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        print(f"Processing file: {csv_file.name}")
        
        # CSV File Storing Process Starts from here------------------------------------------------>
        try:
            root_collection = Collection.objects.get(name='Root')
            if root_collection.depth != 0:
                print(f"Root collection has incorrect depth: {root_collection.depth}. Setting to 0.")
                root_collection.depth = 0
                root_collection.save()
        except Collection.DoesNotExist:
            print("Root collection not found, creating one")
            root_collection = Collection.objects.create(
                name='Root',
                path='0001',
                depth=0,
                numchild=0
            )
        except Exception as e:
            print(f"Error accessing root collection: {str(e)}")
            messages.error(request, f"Error accessing root collection: {str(e)}")
            return redirect('import_users')
        
        # Get or create the User Imports collection under the root
        try:
            collection, created = Collection.objects.get_or_create(
                name='User Imports',
                defaults={
                    'path': root_collection.path + '0001',  # Ensure unique path
                    'depth': root_collection.depth + 1,     # Child of root
                    'numchild': 0
                }
            )
            if created:
                print("Created 'User Imports' collection")
                root_collection.numchild += 1
                root_collection.save()
        except Exception as e:
            print(f"Failed to get or create collection 'User Imports': {str(e)}")
            messages.error(request, f"Error setting up document collection: {str(e)}")
            return redirect('import_users')
        
        # Save the uploaded file as a Custom Wagtail Document
        document = None
        try:
            document = CustomDocument(
                title=f'User Import - {csv_file.name}',
                file=csv_file,
                collection=collection
            )
            document.save()
            print(f"File saved as Custom Wagtail Document: {document.title}")
        except Exception as e:
            logger.error(f"Failed to save document '{csv_file.name}': {str(e)}")
            messages.error(request, f"Error saving document: {str(e)}")
            return redirect('import_users')
        
        #CSV File Storing Process End Here------------------------------------------------>
        
        # Read the CSV file
        try:
            # Reset file pointer to the beginning
            csv_file.seek(0)
            # Read and decode the file
            try:
                decoded_file = csv_file.read().decode('utf-8')
            except UnicodeDecodeError as e:
                logger.error(f"Failed to decode CSV file '{csv_file.name}': {str(e)}")
                messages.error(request, "Invalid file encoding. Please upload a UTF-8 encoded CSV file.")
                document.delete()
                return redirect('import_users')

            # Check if the file is empty
            if not decoded_file.strip():
                logger.error(f"CSV file '{csv_file.name}' is empty")
                messages.error(request, "The uploaded CSV file is empty.")
                document.delete()
                return redirect('import_users')

            # Parse the CSV
            csv_data = csv.DictReader(io.StringIO(decoded_file))
            
            # Check for valid headers
            if csv_data.fieldnames is None:
                logger.error(f"CSV file '{csv_file.name}' has no valid headers")
                messages.error(request, "The CSV file has no valid headers.")
                document.delete()
                return redirect('import_users')

            # Validate required fields
            required_fields = {'username', 'email'}
            if not all(field in csv_data.fieldnames for field in required_fields):
                logger.error(f"CSV file '{csv_file.name}' missing required fields: {required_fields}")
                messages.error(request, "CSV file must contain 'username' and 'email' columns.")
                document.delete()
                return redirect('import_users')

            success_count = 0
            error_count = 0
            created_users = []

            for row in csv_data:
                try:
                    # print(f"Processing user: {row['username']}")
                    # print(f"User data: {row}")

                    random_password = generate_random_password()
                    # print(f"Generated password for {row['username']}")

                    user, created = User.objects.get_or_create(
                        username=row['username'],
                        defaults={
                            'email': row['email'],
                            'first_name': row.get('first_name', ''),
                            'last_name': row.get('last_name', ''),
                            'password': make_password(random_password)
                        }
                    )

                    if created:
                        logger.info(f"Successfully created user: {user.username}")
                        success_count += 1
                        created_users.append({
                            'username': user.username,
                            'password': random_password
                        })
                    else:
                        logger.warning(f"User {user.username} already exists")

                except Exception as e:
                    logger.error(f"Error creating user {row.get('username', 'unknown')}: {str(e)}")
                    error_count += 1

            logger.info(f"Import Summary: Success: {success_count}, Errors: {error_count}")

            request.session['created_users'] = created_users
            messages.success(request, f"Successfully imported {success_count} users. Errors: {error_count}")

        except Exception as e:
            logger.error(f"Error processing CSV file '{csv_file.name}': {str(e)}")
            messages.error(request, f"Error processing CSV file: {str(e)}")
            if document:
                try:
                    document.delete()
                    logger.info(f"Deleted document '{document.title}' due to CSV processing error")
                except Exception as delete_error:
                    logger.error(f"Failed to delete document '{document.title}': {str(delete_error)}")
            return redirect('import_users')

        return redirect('import_users')
    # Display created users from session if they exist
    created_users = request.session.pop('created_users', None)
    return render(request, 'wagtailadmin/import_users.html', {'created_users': created_users})

def download_sample_csv(request):
    """Generate and serve a sample CSV file for user import."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_users_import.csv"'
    
    writer = csv.writer(response)
    # Write headers
    writer.writerow(['username', 'email', 'first_name', 'last_name'])
    # Write sample data
    writer.writerow(['john.doe', 'john.doe@example.com', 'John', 'Doe'])
    writer.writerow(['jane.smith', 'jane.smith@example.com', 'Jane', 'Smith'])
    
    return response


