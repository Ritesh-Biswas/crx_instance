from wagtail import hooks
from wagtail.admin.menu import MenuItem
from django.urls import reverse, path
from django.utils.translation import gettext_lazy as _
from . import admin_views
from . import views

@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        path('blog-stats/', admin_views.blog_stats_view, name='blog_stats'),
        path('import-users/', views.import_users_view, name='import_users'),
        path('download-sample-csv/', views.download_sample_csv, name='download_sample_csv'),
    ]

@hooks.register('construct_main_menu')
def show_blog_stats_menu_item(request, menu_items):
    if request.user.is_superuser or request.user.groups.filter(name="Tenant").exists():
        menu_items.append(
            MenuItem(
                _('Blog Statistics'),
                reverse('blog_stats'),
                icon_name='form',
                order=10000
            )
        )

@hooks.register('construct_main_menu')
def register_import_users_menu_item(request, menu_items):
    if request.user.is_superuser or request.user.groups.filter(name="Tenant").exists():
        menu_items.append(
            MenuItem(
                _('Import Users'),
                reverse('import_users'),
                icon_name='user',
                order=10000
            )
        )
