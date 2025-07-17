# components/blocks.py
from wagtail.blocks import (
    StructBlock,
    CharBlock,
    ListBlock,
)
from wagtail.snippets.blocks import SnippetChooserBlock
from .models import WorkspaceCardSnippet, BlogPostSnippet, ImageGallerySnippet, CarouselsSnippet, CalendarSnippet, OutlookCalendarSnippet, OneDriveSnippet, EventSnippet, WorkDaySnippet, FetchURLSnippet, FetchCalendarEventsSnippet
from datetime import timedelta
from django.utils import timezone
import requests
from django.template.loader import render_to_string

class MyWorkspace(StructBlock):
    cards = ListBlock(SnippetChooserBlock(WorkspaceCardSnippet))

    class Meta:
        template = "components/my_workspace_card_block.html"


class BlogPostBlock(StructBlock):
    blog_post = SnippetChooserBlock(
        target_model=BlogPostSnippet,
        required=False,
        help_text="Select a blog post snippet to display."
    )

    class Meta:
        template = "components/blog_post_block.html"
        icon = "doc-full"
        label = "Blog Post"


class BlogPostDisplayBlock(StructBlock):
    display_snippet = SnippetChooserBlock(
        target_model='components.BlogPostDisplaySnippet',
        required=False,
        help_text="Select a blog post display snippet to enable or disable the blog post listing feature."
    )

    class Meta:
        template = "components/blog_post_display_block.html"
        icon = "doc-full"
        label = "Blog Post Display"


class GoogleDriveBlock(StructBlock):
    display_snippet = SnippetChooserBlock(
        target_model='components.GoogleDriveSnippet',
        required=False,
        help_text="Select a Google Drive snippet to configure display settings."
    )

    class Meta:
        template = "components/google_drive_block.html"
        icon = "doc-full"
        label = "Google Drive"


class ImageGalleryBlock(StructBlock):
    galleries = ListBlock(
        StructBlock([
            ('gallery', SnippetChooserBlock(
                ImageGallerySnippet,
                required=True,
                help_text="Select an image gallery snippet."
            )),
            ('title', CharBlock(
                required=False,
                help_text="Optional section title for this gallery"
            ))
        ]),
        min_num=1,
        help_text="Add one or more image galleries to this section"
    )

    class Meta:
        template = "components/image_gallery_block.html"
        icon = "image"
        label = "Image Galleries"


class CarouselBlock(StructBlock):
    carousel_collection = SnippetChooserBlock(
        CarouselsSnippet,
        required=False,
        help_text="Select a carousel collection snippet to display."
    )

    class Meta:
        template = "components/carousel_block.html"
        icon = "image"
        label = "Carousel"

class CalendarBlock(StructBlock):
    calendar = SnippetChooserBlock(
        target_model=CalendarSnippet,
        required=False,
        help_text="Select a calendar snippet to enable or disable the calendar feature."
    )

    class Meta:
        template = "components/calendar_block.html"
        icon = "date"
        label = "Calendar"


class OneDriveBlock(StructBlock):
    onedrive = SnippetChooserBlock(
        target_model=OneDriveSnippet,
        required=False,
        help_text="Select a onedrive snippet to enable or disable the onedrive feature."
    )

    class Meta:
        template = "components/onedrive_block.html"
        icon = "fa-google-drive"
        label = "One Drive"


class OutlookCalendarBlock(StructBlock):
    display_snippet = SnippetChooserBlock(
        target_model=OutlookCalendarSnippet,
        required=False,
        help_text="To Enable or Disable Outlook Calendar Snippet."
    )

    class Meta:
        template = "components/outlook_calendar_block.html"
        icon = "date"
        label = "Outlook Calendar"


class EventBlock(StructBlock):
    events = ListBlock(
        SnippetChooserBlock(
            target_model=EventSnippet,
            required=True,
            help_text="Select an event to display."
        ),
        min_num=1,
        help_text="Add one or more events to display"
    )

    class Meta:
        template = "components/event_snippet.html"
        icon = "date"
        label = "Events"

class WorkdayBlock(StructBlock):
    workday = SnippetChooserBlock(
        target_model=WorkDaySnippet,
        required=False,
        help_text="Select an workday snippet to display."
    )
    class Meta:
        template = "components/workday_snippet_block.html"
        icon = "date"
        label = "Workday"

class FetchURLBlock(StructBlock):
    fetch_url = SnippetChooserBlock(
        target_model=FetchURLSnippet,
        required=False,
        help_text="Select a fetch URL snippet to display."
    )

    class Meta:
        template = "components/fetch_url_snippet_block.html"
        icon = "link"
        label = "Fetch URL"

class FetchCalendarEventsBlock(StructBlock):
    public_calendar_events = SnippetChooserBlock(
        target_model=FetchCalendarEventsSnippet,
        required=False,
        help_text="Select a fetch URL snippet to display."
    )

    class Meta:
        template = "components/public_calendar_events.html"
        icon = "link"
        label = "Fetch Calendar Events"

class RecentlyHiredBlock(StructBlock):
    title = CharBlock(
        required=True,
        default="Recently Hired",
        help_text="Title for the recently hired section"
    )
    
    class Meta:
        template = 'components/recently_hired_block.html'
        icon = 'user'
        label = 'Recently Hired'

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        context['title'] = value.get('title', 'Recently Hired')
        context['api_url'] = '/custom_user/api/recent-hires/'
        
        return context

class WorkAnniversaryBlock(StructBlock):
    title = CharBlock(
        required=True,
        default="Work Anniversaries",
        help_text="Title for the work anniversaries section"
    )
    
    class Meta:
        template = 'components/work_anniversary_block.html'
        icon = 'date'
        label = 'Work Anniversaries'

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        context['title'] = value.get('title', 'Work Anniversaries')
        context['api_url'] = '/custom_user/api/anniversaries/'
        return context