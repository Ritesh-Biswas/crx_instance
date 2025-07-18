from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, UserExtraProfile
from django.contrib.auth.models import Group



class UserExtraProfileInline(admin.StackedInline):
    model = UserExtraProfile
    can_delete = False  # Prevent deletion of the profile from the User admin
    verbose_name_plural = _("Extra Profile")
    fields = ["manager","about", "joining_date","date_of_birth","designation", "employee_number","expertise","following_departments","following_users"]  # Add desired fields
    # Optionally, make some fields read-only for Tenant group
    def get_readonly_fields(self, request, obj=None):
        if request.user.groups.filter(name="Tenant").exists():
            return self.fields  # Make all fields read-only for Tenant group
        return super().get_readonly_fields(request, obj)

# -------------------- NEW: Custom GroupAdmin --------------------

class CustomGroupAdmin(GroupAdmin):
    def has_module_permission(self, request):
        if request.user.groups.filter(name="Tenant").exists():
            return False
        return super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        if request.user.groups.filter(name="Tenant").exists():
            return False
        return super().has_view_permission(request, obj)

# -------------------- Your Custom UserAdmin --------------------

class CustomUserAdmin(UserAdmin):
    """
    Override Django's default UserAdmin to use the email address
    as the identifier, instead of username.
    """

    list_display = ["email", "username", "first_name", "last_name", "is_staff"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering = ["email"]
    filter_horizontal = ["groups", "user_permissions"]

    inlines = [UserExtraProfileInline]
    
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (_("Permissions"), {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        }),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "password1", "password2"),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Check if the current user is in the "Tenant" group
        if request.user.groups.filter(name="Tenant").exists():
            if "is_superuser" in form.base_fields:
                form.base_fields["is_superuser"].disabled = True
                form.base_fields["is_superuser"].help_text = "You do not have permission to change this."

        return form
    
    def has_module_permission(self, request):
        if request.user.groups.filter(name="Tenant").exists():
            return False
        return super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        if request.user.groups.filter(name="Tenant").exists():
            return False
        return super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if request.user.groups.filter(name="Tenant").exists():
            return False
        return super().has_change_permission(request, obj)

# -------------------- Admin Registrations --------------------

# First unregister old Group admin
admin.site.unregister(Group)

# Register Group with the new CustomGroupAdmin
admin.site.register(Group, CustomGroupAdmin)

# Register your CustomUserAdmin
admin.site.register(User, CustomUserAdmin)
