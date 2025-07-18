from django.urls import path #type: ignore
from .views import blog_post_create_view, upload_image, BlogPostDetailView, toggle_like_post, fetch_drive_files, CalendarEventsView, OneDriveFilesView, OutlookCalendarEventsView, AuthSettingsView, PublicCalendarEventsView
from . import views

app_name = 'components'

urlpatterns = [
    path('create/', blog_post_create_view, name='blog_post_create'),
    path('upload-image/', upload_image, name='upload_image'),
    path('blog-post/<int:pk>/', BlogPostDetailView.as_view(), name='blog_post_detail'),
    path('toggle-like-post/<int:post_id>/', toggle_like_post, name='toggle_like_post'),
    path('load-more-posts/', views.load_more_posts, name='load_more_posts'),
    path("fetch-drive-files/", fetch_drive_files, name="fetch_drive_files"),
    path('subdepartments/', views.subdepartment_list_view, name='subdepartment_list'),
    path('edit-post/<int:post_id>/', views.edit_post, name='edit_post'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    path('calendar-events/', CalendarEventsView.as_view(), name='calendar_events'),
    path('submit-poll-vote/<int:post_id>/', views.submit_poll_vote, name='submit_poll_vote'),
    path("onedrive-files/", OneDriveFilesView.as_view(), name="onedrive_files"),
    path("outlook-calendar-events/", OutlookCalendarEventsView.as_view(), name="outlook_calendar_events"),
    path('api/auth-settings/', AuthSettingsView.as_view(), name='auth_settings'),
    path('public-calendar-events/', PublicCalendarEventsView.as_view(), name='public_calendar_events'),
]