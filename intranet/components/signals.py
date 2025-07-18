from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.core.files.images import ImageFile
from django.conf import settings
import os

from wagtail.snippets.models import get_snippet_models
from allauth.socialaccount.models import SocialApp
from .models import AuthenticationSettings
from home.models import HomePage
from wagtail.models import Page, Site
from coderedcms.models import CoderedPage

@receiver(post_save, sender=AuthenticationSettings)
def create_or_update_social_apps(sender, instance, **kwargs):
    # Google
    if instance.google_client_id and instance.google_secret_key:
        google_app, created = SocialApp.objects.get_or_create(provider='google')
        google_app.client_id = instance.google_client_id
        google_app.secret = instance.google_secret_key
        google_app.name = 'Google'
        google_app.save()

    # Microsoft
    if instance.microsoft_client_id and instance.microsoft_secret_key:
        microsoft_app, created = SocialApp.objects.get_or_create(provider='microsoft')
        microsoft_app.client_id = instance.microsoft_client_id
        microsoft_app.secret = instance.microsoft_secret_key
        microsoft_app.name = 'Microsoft'
        microsoft_app.save()

    # Workday
    if instance.workday_client_id and instance.workday_secret_key:
        workday_app, created = SocialApp.objects.get_or_create(provider='workday')
        workday_app.client_id = instance.workday_client_id
        workday_app.secret = instance.workday_secret_key
        workday_app.name = 'Workday'
        workday_app.save()

@receiver(post_migrate)
def create_default_snippets(sender, **kwargs):
    # Import models lazily to avoid circular imports
    from .models import (
        CalendarSnippet,
        BlogPostSnippet,
        BlogPostDisplaySnippet,
        ImageGallerySnippet,
        CarouselsSnippet,
        GoogleDriveSnippet,
        OutlookCalendarSnippet,
        OneDriveSnippet
    )

    # Create default CalendarSnippet
    if not CalendarSnippet.objects.exists():
        CalendarSnippet.objects.create(add_calendar=True)
    
    # Create default GoogleDriveSnippet
    if not GoogleDriveSnippet.objects.exists():
        GoogleDriveSnippet.objects.create(enable_gdrive=True)

    # Create default BlogPostSnippet
    if not BlogPostSnippet.objects.exists():
        BlogPostSnippet.objects.create(add_post=True)

    # Create default BlogPostDisplaySnippet
    if not BlogPostDisplaySnippet.objects.exists():
        BlogPostDisplaySnippet.objects.create(show_blogpost=True)

    # Create default ImageGallerySnippet
    if not ImageGallerySnippet.objects.exists():
        gallery = ImageGallerySnippet.objects.create(title="Default Image Gallery")
        
        # Use images from the Carousel_static_image folder
        static_image_folder = os.path.join(settings.BASE_DIR, 'static', 'Carousel_static_image')
        if os.path.exists(static_image_folder):
            for idx, image_name in enumerate(os.listdir(static_image_folder)):
                image_path = os.path.join(static_image_folder, image_name)
                if os.path.isfile(image_path):
                    with open(image_path, 'rb') as img_file:
                        gallery.gallery_images.create(
                            image_title=f"image{idx + 1}",
                            image=ImageFile(img_file, name=image_name),
                            is_full=True
                        )

    # Create default CarouselsSnippet
    if not CarouselsSnippet.objects.exists():
        carousel_collection = CarouselsSnippet.objects.create(title="Default Carousel Collection")
        carousel = carousel_collection.carousels.create()

        # Add slides using the created gallery
        gallery = ImageGallerySnippet.objects.first()
        if gallery:
            for idx, gallery_image in enumerate(gallery.gallery_images.all()[:2]):  # Use the first two images
                carousel.slides.create(
                    image_gallery=gallery,
                    caption=f"Default Slide Caption {idx + 1}"
                )

    #Create default Outlook Snippet
    if not OutlookCalendarSnippet.objects.exists():
        OutlookCalendarSnippet.objects.create(enable_outlook_calendar=True)
    
    #Create default Onedrive
    if not OneDriveSnippet.objects.exists():
        OneDriveSnippet.objects.create(enable_onedrive=True)



@receiver(post_migrate)
def create_homepage(sender, **kwargs):
    """Create a HomePage as the root page and delete default CodeRed page"""
    
    # Only run this for our app
    if sender.name != "home":
        return

    print("Starting homepage creation process...")
    

    try:
        # Get the root page
        root = Page.objects.get(id=1)
        print("Found root page")

        # Check if there's already a HomePage
        if not HomePage.objects.exists():
            print("No HomePage exists - creating new one")
            
            # Delete the default CodeRed page if it exists
            default_home = CoderedPage.objects.first()
            if default_home:
                print(f"Deleting default CodeRed page (id: {default_home.id})")
                default_home.delete()

            # Create the new HomePage with proper hierarchy settings
            home_page = HomePage(
                title="Home",
                slug="home",
                show_in_menus=True,
                live=True,
                path='00010001',  # Proper path under root
                depth=2,  # One level below root
                numchild=0,
                url_path='/home/',
            )
            
            # Save the page first
            home_page.save()
            print(f"Created new HomePage with id: {home_page.id}")

            # Set as child of root
            home_page.move(root, pos='last-child')
            print("Set HomePage as child of root")

            root.numchild = root.get_children().count()
            root.save()
            print("Updated Root page child count")
            # Create or update site
            site = Site.objects.first()
            if not site:
                site = Site.objects.create(
                    hostname='localhost',
                    port=8000,
                    site_name='Default Site',
                    root_page=home_page,
                    is_default_site=True
                )
                print("Created new Site object")
            else:
                site.root_page = home_page
                site.save()
            print("Set HomePage as site root page")
        root.save()
        print("Updated Root page child count")
        

    except Exception as e:
        print(f"Error creating homepage: {str(e)}")