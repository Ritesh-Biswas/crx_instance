from django.db import models
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.models import Orderable
from modelcluster.fields import ParentalKey
from wagtail.fields import RichTextField
from wagtail.models import Page
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from modelcluster.models import ClusterableModel
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.users.models import UserProfile
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth import get_user_model
from comment.models import Comment
from wagtail.images import get_image_model_string
from django.utils import timezone
import logging

from django.contrib.contenttypes.models import ContentType

from wagtail.contrib.settings.models import BaseGenericSetting, register_setting

from wagtail.admin.panels import HelpPanel


"""
    Workspace Card Snippet
"""
@register_snippet
class WorkspaceCardSnippet(models.Model):
    icon = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ("document", "Document"),
            ("folder", "Folder"),
            ("user", "User"),
            ("settings", "Settings"),
            ("plus", "Plus"),
        ],
        help_text="Select an SVG icon",
    )
    title = models.CharField(max_length=40)
    button_page = models.ForeignKey(
        Page, on_delete=models.SET_NULL, null=True, blank=False, related_name="+"
    )

    panels = [
        FieldPanel("icon"),
        FieldPanel("title"),
        FieldPanel("button_page"),
    ]

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Workspace Card"
        verbose_name_plural = "Custom_Workspace_Cards"

@register_snippet
class BlogPostSnippet(models.Model):
    add_post = models.BooleanField(
        default=False,
        help_text="Check this box to enable the blogpost feature."
    )

    panels = [
        FieldPanel("add_post"),
    ]

    def __str__(self):
        return "Blog Post Snippet" if self.add_post else "Blog Post Snippet (Disabled)"

    class Meta:
        verbose_name = "Blog Post Setting"
        verbose_name_plural = "Custom_Blog_Post_Settings"

@register_snippet
class GoogleDriveSnippet(models.Model):
    enable_gdrive = models.BooleanField(
        default=False,
        help_text="Check this box to enable the Google Drive functionality."
    )
    fetch_by_default = models.BooleanField(
        default=True,
        help_text="If enabled, drive data will be fetched automatically. If disabled, a fetch button will be shown."
    )

    panels = [
        FieldPanel("enable_gdrive"),
        FieldPanel("fetch_by_default"),
    ]

    def __str__(self):
        return "Google Drive Enabled" if self.enable_gdrive else "Google Drive Disabled"

    class Meta:
        verbose_name = "Google Drive Setting"
        verbose_name_plural = "Custom_Google_Drive_Settings"

@register_snippet
class OneDriveSnippet(models.Model):
    enable_onedrive = models.BooleanField(
        default=False,
        help_text="Check this box to enable the OneDrive functionality."
    )

    fetch_by_default = models.BooleanField(
        default=True,
        help_text="If enabled, drive data will be fetched automatically. If disabled, a fetch button will be shown."
    )

    panels = [
        FieldPanel("enable_onedrive"),
        FieldPanel("fetch_by_default"),
    ]

    def __str__(self):
        return "OneDrive Enabled" if self.enable_onedrive else "OneDrive Disabled"

    class Meta:
        verbose_name = "OneDrive Setting"
        verbose_name_plural = "Custom_OneDrive_Settings"


@register_snippet
class OutlookCalendarSnippet(models.Model):
    enable_outlook_calendar = models.BooleanField(
        default=False,
        help_text="Check this box to enable the Outlook Calendar functionality."
    )

    panels = [
        FieldPanel("enable_outlook_calendar"),
    ]

    def __str__(self):
        return "Outlook Calendar Enabled" if self.enable_outlook_calendar else "Outlook Calendar Disabled"

    class Meta:
        verbose_name = "Outlook Calendar Setting"
        verbose_name_plural = "Custom_Outlook_Calendar_Settings"

class BlogPost(models.Model):
    post_type = models.CharField(max_length=20, choices=[('post', 'Post'), ('question', 'Question'), ('poll', 'Poll')],default='post')
    title = models.CharField(max_length=200, null=True, blank=True, help_text="Required for questions")
    body = RichTextField(null=True)
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    comments = GenericRelation(Comment, null=True)
    likes = models.ManyToManyField(get_user_model(), related_name='liked_posts')
    likes_count = models.IntegerField(default=0, null=True)
    subdepartment = models.ForeignKey(
        'home.SubDepartmentPage', on_delete=models.SET_NULL, null=True, blank=True, related_name='blog_posts',
        help_text="Select a subdepartment for this blog post or leave blank for a global post."
    )
    poll_end_time = models.DateTimeField(null=True, blank=True, help_text="Set when this poll should end")

    def __str__(self):
        subdepartment_str = f" - {self.subdepartment.name}" if self.subdepartment else " - Global"
        return f"{self.post_type.capitalize()} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}{subdepartment_str}"

    def get_comments(self):
        content_type = ContentType.objects.get_for_model(self)
        return Comment.objects.filter(content_type=content_type, object_id=self.id)
    
    def update_likes_count(self):
        self.likes_count = self.likes.count()
        self.save()
    
    @property
    def total_votes(self):
        return sum(option.votes_count for option in self.poll_options.all())
    
    @property
    def is_poll_active(self):
        if self.post_type != 'poll' or not self.poll_end_time:
            return False
        
        return self.poll_end_time >= timezone.now()

    def get_stats(self):
        """Return comprehensive stats for the blog post"""
        return {
            'total_likes': self.likes.count(),
            'total_comments': self.get_comments().count(),
            'total_votes': self.total_votes if self.post_type == 'poll' else 0,
            'created_at': self.created_at,
            'department': self.subdepartment.name if self.subdepartment else 'Global',
            'post_type': self.post_type,
            'is_active': self.is_poll_active if self.post_type == 'poll' else True,
        }

    @property
    def engagement_score(self):
        """Calculate engagement score based on likes, comments and votes"""
        likes_weight = 1
        comments_weight = 2
        votes_weight = 1.5
        
        score = (self.likes.count() * likes_weight + 
                self.get_comments().count() * comments_weight +
                (self.total_votes * votes_weight if self.post_type == 'poll' else 0))
        return round(score, 2)

    class Meta:
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"


# Add these models to your models.py file
class PollOption(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='poll_options')
    text = models.CharField(max_length=200)
    votes_count = models.IntegerField(default=0)
    
    @property
    def votes_percentage(self):
        total_votes = self.post.total_votes
        if total_votes > 0:
            return round((self.votes_count / total_votes) * 100)
        return 0

class PollVote(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE)
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']

# Add this property to your BlogPost model

@register_snippet
class BlogPostDisplaySnippet(models.Model):
    show_blogpost = models.BooleanField(
        default=False,
        help_text="Check this box to enable the blogpost listing feature."
    )
    panels = [
       FieldPanel("show_blogpost"),
    ]

    def __str__(self):
        return "Blog Post Display Snippet"

    class Meta:
        verbose_name = "Blog Post Display"
        verbose_name_plural = "Custom_Blog_Post_Display"


class QuillImage(models.Model):
    image = models.ImageField(upload_to='quill_uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.image.name



#-------------------------------------------------#

class ImageGallerySnippetForm(WagtailAdminModelForm):
    class Media:
        js = ['js/image_gallery_admin.js']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        
        if hasattr(self.instance, 'gallery_images') and self.instance.pk:
            total_width = sum(image.get_width_value() for image in self.instance.gallery_images.all())

            if total_width > 1.001:
                raise ValidationError("Total width of images cannot exceed 100%")
        
        gallery_images_formset = self.formsets.get('gallery_images')
        if (gallery_images_formset):
            total_width = 0
            for form in gallery_images_formset.forms:
                if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                    is_full = form.cleaned_data.get('is_full', False)
                    is_half = form.cleaned_data.get('is_half', False)
                    is_fourth = form.cleaned_data.get('is_fourth', False)
                    width = 1.0 if is_full else 0.5 if is_half else 0.25 if is_fourth else 0.0
                    total_width += width

            if total_width > 1.001:
                raise ValidationError("Total width of images cannot exceed 100%")
        
        return cleaned_data

@register_snippet
class ImageGallerySnippet(ClusterableModel):
    title = models.CharField(max_length=100)
    
    panels = [
        FieldPanel('title'),
        InlinePanel('gallery_images', max_num=4, min_num=1, label="Images")
    ]
    
    base_form_class = ImageGallerySnippetForm
    
    def validate_total_width(self):
        if not hasattr(self, 'gallery_images'):
            return
        total_width = sum(image.get_width_value() for image in self.gallery_images.all())
        if total_width > 1.001:
            raise ValidationError("Total width of images cannot exceed 100%")
    
    def get_available_slots(self):
        if not hasattr(self, 'gallery_images'):
            return 1.0
        return 1.0 - sum(image.get_width_value() for image in self.gallery_images.all())

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Image Gallery"
        verbose_name_plural = "Custom_Slides_For_Crousals"

class GalleryImage(Orderable):
    gallery = ParentalKey(
        'ImageGallerySnippet',
        null=True,
        on_delete=models.CASCADE,
        related_name='gallery_images',
    )
    image = models.ForeignKey(
        get_image_model_string(),
        on_delete=models.CASCADE,
        related_name='+',
    )
    image_title = models.CharField(max_length=100)
    is_full = models.BooleanField(default=False, verbose_name="Full Width (100%)")
    is_half = models.BooleanField(default=False, verbose_name="Half Width (50%)")
    is_fourth = models.BooleanField(default=False, verbose_name="One-Fourth (25%)")

    panels = [
        FieldPanel('image'),
        FieldPanel('image_title'),
        FieldPanel('is_full'),
        FieldPanel('is_half'),
        FieldPanel('is_fourth'),
    ]

    def clean(self):
        super().clean()
        selected_options = sum([self.is_full, self.is_half, self.is_fourth])
        if selected_options != 1:
            raise ValidationError(_("Please select exactly one width option"))
        if self.gallery_id and self.is_full and self.gallery.gallery_images.count() > 1:
            raise ValidationError(_("Full-width images must be the only image in the gallery"))

    def get_width_value(self):
        return 1.0 if self.is_full else 0.5 if self.is_half else 0.25 if self.is_fourth else 0.0

    def get_width_class(self):
        return 'w-full' if self.is_full else 'w-1/2' if self.is_half else 'w-1/4' if self.is_fourth else ''


# Custom form for validation
class CarouselSnippetForm(WagtailAdminModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

# First, the Carousel class needs to be defined outside of CarouselsSnippet
@register_snippet
class CarouselsSnippet(ClusterableModel):
    title = models.CharField(max_length=100, help_text="Title for the collection of carousels")
    
    panels = [
        FieldPanel('title'),
        InlinePanel('carousels', label="Carousels"),
    ]
    
    base_form_class = CarouselSnippetForm

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Carousel Collection"
        verbose_name_plural = "Custom_Carousal"

# Separate Carousel model
class Carousel(ClusterableModel, Orderable):
    parent = ParentalKey(
        'CarouselsSnippet',
        on_delete=models.CASCADE,
        related_name='carousels'
    )
    
    
    panels = [
        InlinePanel('slides', label="Slides"),

    ]

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Carousel"
        verbose_name_plural = "Carousels"

# Separate CarouselSlide model
class CarouselSlide(Orderable):
    carousel = ParentalKey(
        'Carousel',
        on_delete=models.CASCADE,
        related_name='slides'
    )
    image_gallery = models.ForeignKey(
        'ImageGallerySnippet',
        on_delete=models.CASCADE,
        related_name='carousel_slides',
        help_text="Select an image gallery for this slide",
        null=True,
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional caption for this slide"
    )

    panels = [
        FieldPanel('image_gallery'),
        FieldPanel('caption'),
    ]

    def clean(self):
        super().clean()
        if not self.image_gallery:
            raise ValidationError("An image gallery must be selected for each slide")

    def get_images(self):
        if self.image_gallery:
            return self.image_gallery.gallery_images.all()
        return []

    def __str__(self):
        gallery_title = self.image_gallery.title if self.image_gallery else "No Gallery"
        caption = f" - {self.caption}" if self.caption else ""
        return f"Slide with {gallery_title}{caption}"

    class Meta:
        verbose_name = "Carousel Slide"
        verbose_name_plural = "Carousel Slides"


@register_setting(icon='key')
class AuthenticationSettings(BaseGenericSetting):
    # Google Section
    google_client_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Google OAuth Client ID'
    )
    google_secret_key = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Google OAuth Secret Key'
    )

    # Microsoft Section
    microsoft_client_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Microsoft Azure Client ID'
    )
    microsoft_secret_key = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Microsoft Azure Secret Key'
    )

    # Workday Section
    workday_client_id = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Workday API Client ID'
    )
    workday_secret_key = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Workday API Secret Key'
    )

    panels = [
        MultiFieldPanel([
            FieldPanel('google_client_id'),
            FieldPanel('google_secret_key'),
        ], heading="Google Authentication"),
        
        MultiFieldPanel([
            FieldPanel('microsoft_client_id'),
            FieldPanel('microsoft_secret_key'),
        ], heading="Microsoft Authentication"),
        
        MultiFieldPanel([
            FieldPanel('workday_client_id'),
            FieldPanel('workday_secret_key'),
        ], heading="Workday Authentication"),
         HelpPanel(content="""
        <a href='/myadmin/socialaccount/socialaccount/' target='_blank' rel='noopener noreferrer' style='margin-right:10px;'>
            <button type='button' style='background:#43b1b0; color:white; padding:5px 10px; border:none; border-radius:3px;'>Social Accounts</button>
        </a>
        <a href='/myadmin/socialaccount/socialtoken/' target='_blank' rel='noopener noreferrer'>
            <button type='button' style='background:#43b1b0; color:white; padding:5px 10px; border:none; border-radius:3px;'>Social Application Tokens</button>
        </a>
    """, heading="Actions", classname="full"),
    ]

    class Meta:
        verbose_name = "Authentication Settings"

@register_setting(icon='login')
class CustomLoginSettings(BaseGenericSetting):
    title = models.CharField(
        max_length=255,
        default='Welcome',
        help_text='Login page title'
    )
    
    background_color = models.CharField(
        max_length=50,
        default='#ff5733',
        help_text='Background color in hex format (e.g. #ffffff)'
    )

    text_color = models.CharField(
        max_length=50,
        default='#ffffff',
        help_text='Background color in hex format (e.g. #ffffff)'
    )
    
    logo = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='+',
    )

    panels = [
        MultiFieldPanel([
            FieldPanel('title'),
            FieldPanel('background_color'),
            FieldPanel('text_color'),
            FieldPanel('logo'),
        ], heading="Custom Login Settings"),
    ]

    class Meta:
        verbose_name = "Custom Login Settings"

@register_snippet
class CalendarSnippet(models.Model):
    add_calendar = models.BooleanField(
        default=False,
        help_text="Check this box to enable the calendar feature."
    )

    panels = [
        FieldPanel("add_calendar"),
    ]

    def __str__(self):
        return "Calendar Snippet" if self.add_calendar else "Calendar Snippet (Disabled)"

    class Meta:
        verbose_name = "Calendar Setting"
        verbose_name_plural = "Custom_Calendar_Settings"


@register_snippet
class EventSnippet(models.Model):
    EVENT_TYPES = [
        ('birthday', 'Birthday'),
        ('anniversary', 'Anniversary'),
        ('work_anniversary', 'Work Anniversary'),
        ('wedding', 'Wedding'),
    ]

    title = models.CharField(max_length=200)
    event_type = models.CharField(
        max_length=20, 
        choices=EVENT_TYPES,
        default='birthday'
    )
    description = models.TextField(blank=True)
    date = models.DateField()
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='events'
    )

    panels = [
        FieldPanel('title'),
        FieldPanel('event_type'),
        FieldPanel('description'),
        FieldPanel('date'),
        FieldPanel('user'),
    ]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.title} ({self.user.get_full_name()})"

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Custom_Events"
        ordering = ['date']

@register_snippet
class WorkDaySnippet(models.Model):
    add_workday = models.BooleanField(
        default=False,
        help_text="Check this box to enable the workday checkin/checkout feature."
    )

    panels = [
        FieldPanel("add_workday"),
    ]

    def __str__(self):
        return "Workday checkin/checkout Snippet" if self.add_workday else "Workday checkin/checkout Snippet (Disabled)"

    class Meta:
        verbose_name = "Workday Snippet"
        verbose_name_plural = "Custom Workday Snippets"

@register_snippet
class FetchURLSnippet(models.Model):
    fetch_data_url = models.URLField(
        max_length=500,
        help_text="Enter the URL from which data will be fetched."
    )
    
    panels = [
        FieldPanel("fetch_data_url"),
    ]
    
    def __str__(self):
        return f"Data Source: {self.fetch_data_url}"
    
    class Meta:
        verbose_name = "Fetch URL Snippet"
        verbose_name_plural = "Custom Fetch URL Snippets"


@register_snippet
class FetchCalendarEventsSnippet(models.Model):
    calendar_public_url = models.URLField(
        max_length=500,
        help_text="Enter the URL from which calendar events will be fetched."
    )
    
    panels = [
        FieldPanel("calendar_public_url"),
    ]
    
    def __str__(self):
        return f"Calendar Source: {self.calendar_public_url}"
    
    class Meta:
        verbose_name = "Fetch Calendar Events Snippet"
        verbose_name_plural = "Fetch Calendar Events Snippets"