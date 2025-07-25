from django import template

from website.models import Footer
from website.models import Navbar
from wagtail.images.models import Image


register = template.Library()


@register.simple_tag
def get_website_navbars():
    # NOTE: For a multi-site, you may need to create SiteSettings to
    # choose a Navbar, then query those here. Or, add a Foreign Key to
    # the Site on the Navbar, and query those.
    return Navbar.objects.all()


@register.simple_tag
def get_website_footers():
    # NOTE: For a multi-site, you may need to create SiteSettings to
    # choose a Footer, then query those here. Or, add a Foreign Key to
    # the Site on the Footer, and query those.
    return Footer.objects.all()

@register.filter
def is_wagtail_image(value):
    return isinstance(value, Image)



@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()
