from django.contrib import admin
from .models import CustomDocument, CustomImage


class CustomDocumentAdmin(admin.ModelAdmin):
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


class CustomImageAdmin(admin.ModelAdmin):
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


admin.site.register(CustomDocument, CustomDocumentAdmin)
admin.site.register(CustomImage, CustomImageAdmin)
