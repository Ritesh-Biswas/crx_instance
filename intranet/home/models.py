from coderedcms.models import CoderedWebPage
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField, RichTextField
from wagtail import blocks
from modelcluster.fields import ParentalManyToManyField, ParentalKey
# from django.contrib.auth.models import User
from django.conf import settings
from django import forms

from components.blocks import (
     MyWorkspace,
     BlogPostBlock,
     BlogPostDisplayBlock,
     GoogleDriveBlock,
     CarouselBlock,
     CalendarBlock,
     OneDriveBlock,
     OutlookCalendarBlock,
     EventBlock,
     WorkdayBlock,
     FetchURLBlock,
     FetchCalendarEventsBlock,
     RecentlyHiredBlock,
     WorkAnniversaryBlock

)
from django.db import models

from components.models import (
    WorkspaceCardSnippet,
    BlogPostSnippet,
    BlogPostDisplaySnippet,
    GoogleDriveSnippet,
    CarouselsSnippet,
    CalendarSnippet,
    OutlookCalendarSnippet,
    OneDriveSnippet

)

PAGE_CONTENT_BLOCKS = [
    ("my_workspace_card", MyWorkspace()),
    ("blog_post", BlogPostBlock()),
    ("blog_post_display", BlogPostDisplayBlock()),
    ("google_drive", GoogleDriveBlock()),
    ("crousal", CarouselBlock()),
    ("calendar", CalendarBlock()),
    ("onedrive", OneDriveBlock()),
    ("outlook_calendar", OutlookCalendarBlock()),
    ("event",EventBlock()),
    ("workday", WorkdayBlock()),
    ("fetch_url_snippet", FetchURLBlock()),
    ("fetch_calendar_events_snippet", FetchCalendarEventsBlock()),
    ("recently_hired", RecentlyHiredBlock()),
    ("work_anniversary", WorkAnniversaryBlock()),
    ]

from wagtail.blocks import StreamValue

class HomePage(CoderedWebPage):
    """Home page model"""
    
    class Meta:
        verbose_name = "Home Page"

    # Add custom fields
    welcome_text = RichTextField(
        blank=True,
        help_text='Welcome text on the page'
    )
    
    featured_section = RichTextField(
        blank=True,
        help_text='Featured content section'
    )

    page_content = StreamField(
        PAGE_CONTENT_BLOCKS,
        blank=True,
        use_json_field=True,
    )

    # Add custom fields to content panels
    content_panels = CoderedWebPage.content_panels + [
        FieldPanel('welcome_text'),
        FieldPanel('featured_section'),
        FieldPanel("page_content"),
    ]

    # Set parent page types
    parent_page_types = ['wagtailcore.Page']
    
    # Set allowed subpage types
    subpage_types = [
        'website.ArticleIndexPage',
        'website.EventIndexPage',
        'website.WebPage',
        'home.AnnouncementPage',
        'home.FAQPage',
        'home.DepartmentPage',
    ]

    template = "home/home_page.html"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        # Get child pages by specific types
        # context['subdepartments'] = SubDepartmentPage.objects.child_of(self).live().specific()
        
        return context

    
    def save(self, *args, **kwargs):
        # Populate default snippets in page_content if it's empty
        if not self.page_content or len(self.page_content) == 0:
            blocks = []

            # Add BlogPostSnippet if it exists and add_post is True
            blog_post = BlogPostSnippet.objects.first()
            if blog_post and blog_post.add_post:
                blocks.append({
                    "type": "blog_post",
                    "value": {
                        "blog_post": blog_post.id
                    }
                })

            # Add BlogPostDisplaySnippet if it exists and show_blogpost is True
            blog_post_display = BlogPostDisplaySnippet.objects.first()
            if blog_post_display and blog_post_display.show_blogpost:
                blocks.append({
                    "type": "blog_post_display",
                    "value": {
                        "display_snippet": blog_post_display.id
                    }
                })

            # Add GoogleDriveSnippet if it exists and enable_gdrive is True
            # Add GoogleDriveSnippet if it exists and enable_gdrive is True
            google_drive = GoogleDriveSnippet.objects.first()
            if google_drive and google_drive.enable_gdrive:
                blocks.append({
                    "type": "google_drive",
                    "value": {
                        "display_snippet": google_drive.id
                    }
                })

            carousel = CarouselsSnippet.objects.first()
            if carousel:
                blocks.append({
                    "type": "crousal",
                    "value": {
                        "id": carousel.id,
                        "title": carousel.title,
                    }
                })

            calendar = CalendarSnippet.objects.first()
            if calendar and calendar.add_calendar:
                blocks.append({
                    "type": "calendar",
                    "value": {
                        "id": calendar.id,
                        "add_calendar": calendar.add_calendar,
                    }
                })
            
            #Add Outlook Calander
            outlook_calendar = OutlookCalendarSnippet.objects.first()
            if outlook_calendar and outlook_calendar.enable_outlook_calendar:
                blocks.append({
                    "type": "outlook_calendar",
                    "value": {
                        "display_snippet": outlook_calendar.id
                    }
                })
            
            #Add Onedrive
            one_drive = OneDriveSnippet.objects.first()
            if one_drive and one_drive.enable_onedrive:
                blocks.append({
                    "type": "onedrive",
                    "value": {
                        "onedrive": one_drive.id
                    }
                })
                


            # Use StreamValue to populate the StreamField
            self.page_content = StreamValue(self.page_content.stream_block, blocks, is_lazy=True)

        # Save the page
        super().save(*args, **kwargs)

class AnnouncementPage(CoderedWebPage):
    """
    Announcement Page
    """
    class Meta:
        verbose_name = "Announcement"
    
    parent_page_types = ['home.HomePage']
    subpage_types = [
        'home.subAnnouncments'
    ]
    template = "home/Announcements.html" 

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        # Add sub-announcements to context
        context['subannouncements'] = subAnnouncments.objects.child_of(self).live().specific()
        
        
        return context
    
    
    


class subAnnouncments(CoderedWebPage):
    """
    SubAnnouncement Page - Displays as Childpage of Announcements 
    """
    class Meta:
        verbose_name = "Sub Announcement"
    
    parent_page_types = ['home.AnnouncementPage']
    template = 'home/SubAnnouncements.html'

class FAQPage(CoderedWebPage):
    """
    FAQ Page
    """
    class Meta:
        verbose_name = "FAQ"

    # FAQ-specific fields
    faq_items = StreamField(
        [
            ('faq_item', blocks.StructBlock([
                ('question', blocks.CharBlock(required=True, max_length=255)),
                ('answer', blocks.RichTextBlock(
                    features=['bold', 'italic', 'link', 'ol', 'ul'],
                    required=True
                )),
            ])),
        ],
        use_json_field=True,
        blank=True,
        help_text="List of Frequently Asked Questions and Answers"
    )

    # Content panels for the admin interface
    content_panels = CoderedWebPage.content_panels + [
        FieldPanel('faq_items'),
    ]

    subpage_types = []  # No children allowed under FAQs
    
    template = "home/sub_faq.html"


class DepartmentPage(CoderedWebPage):
    """
    Department Page
    """
    class Meta:
        verbose_name = "Department Page"
    
    parent_page_types = ['home.HomePage']
    
    subpage_types = [
        'home.SubDepartmentPage',
    ]

    template = 'home/DepartmentPage.html'

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        # Get the current user
        user = request.user
        
        if user.is_authenticated:
            if user.is_superuser or  user.groups.filter(name='Tenant').exists():
                # Superusers get all subdepartments
                context['subdepartments'] = SubDepartmentPage.objects.child_of(self).live().specific()
            else:
                # Non-superusers only see subdepartments where they are site_admin or member
                context['subdepartments'] = SubDepartmentPage.objects.child_of(self).live().specific().filter(
                    models.Q(site_admins=user) | models.Q(members=user)
                )
        else:
            # If user is not authenticated, show no subdepartments
            context['subdepartments'] = SubDepartmentPage.objects.none()
        
        return context


DEPT_PAGE_CONTENT_BLOCKS = [
    ("blog_post", BlogPostBlock()),
    ("blog_post_display", BlogPostDisplayBlock()),
    ("google_drive", GoogleDriveBlock()),
    ]

class SubDepartmentPage(CoderedWebPage):
    """
    Sub Department Page
    """

    name = models.CharField(max_length=100, null=True, blank=True)

    site_admins = ParentalManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="administered_subdepartments",
        blank=True,
        limit_choices_to={"is_superuser": False},
    )
    members = ParentalManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="department_members",
        blank=True,
        limit_choices_to={"is_superuser": False},
    )

    page_content = StreamField(
        DEPT_PAGE_CONTENT_BLOCKS,
        blank=True,
        use_json_field=True,
    )

    content_panels = CoderedWebPage.content_panels + [
        FieldPanel("name"),
        FieldPanel("page_content"),
        FieldPanel("site_admins", widget=forms.CheckboxSelectMultiple),
        FieldPanel("members", widget=forms.CheckboxSelectMultiple),
    ]

    @property
    def is_subdepartment_page(self):
        return True

    class Meta:
        verbose_name = "Sub Depratment Page"
    
    parent_page_types = ['home.DepartmentPage']
    subpage_types = [
        'home.SubDepartmentAnnouncementPage',
        'home.SubDepartmentFAQPage',
        ]
    
    template = "home/SubDepartment.html"
    
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        # Get child pages by specific types
        context['subdepartmentannouncements'] = SubDepartmentAnnouncementPage.objects.child_of(self).live().specific()
        context['subfaq'] = SubDepartmentFAQPage.objects.child_of(self).live().specific()

        # Followers data
        followers = self.department_followers.all()
        context['followers'] = followers
        context['followers_count'] = followers.count()

        # Check if user follows this department
        if request.user.is_authenticated:
            context['is_following'] = followers.filter(id=request.user.id).exists()
        else:
            context['is_following'] = False

        return context

class SubDepartmentAnnouncementPage(CoderedWebPage):
    """
    Sub Department Announcement Page
    """

    class Meta:
        verbose_name = "Sub Department Announcement Page"
    
    parent_page_types = ['home.SubDepartmentPage']
    subpage_types = [
        'home.SubDepartmentSubAnnouncementPage',
        ]
    template = "home/SubDepartmentAnnouncement.html"
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        
        # Add sub-announcements to context
        context['subannouncements'] = SubDepartmentSubAnnouncementPage.objects.child_of(self).live().specific()
        
        
        return context

class SubDepartmentSubAnnouncementPage(CoderedWebPage):
    """
    Sub Announcement Page - Displays as Childpage of Announcements 
    """
    class Meta:
        verbose_name = "Sub Announcement"
    
    parent_page_types = ['home.SubDepartmentAnnouncementPage']
    template = 'home/SubDepartmentSubAnnouncementPage.html'

class SubDepartmentFAQPage(CoderedWebPage):
    """
    FAQ Page
    """
    class Meta:
        verbose_name = "FAQ"

    # FAQ-specific fields
    faq_items = StreamField(
        [
            ('faq_item', blocks.StructBlock([
                ('question', blocks.CharBlock(required=True, max_length=255)),
                ('answer', blocks.RichTextBlock(
                    features=['bold', 'italic', 'link', 'ol', 'ul'],
                    required=True
                )),
            ])),
        ],
        use_json_field=True,
        blank=True,
        help_text="List of Frequently Asked Questions and Answers"
    )

    # Content panels for the admin interface
    content_panels = CoderedWebPage.content_panels + [
        FieldPanel('faq_items'),

    ]

    parent_page_types = ['home.SubDepartmentPage']

    subpage_types = []  # No children allowed under FAQs
    
    template = "home/SubDepartmentFAQPage.html"
