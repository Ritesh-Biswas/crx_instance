from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

EXCLUDED_CODENAMES = [
    "add_analyticssettings", "change_analyticssettings", "delete_analyticssettings", "view_analyticssettings",
    "add_site", "change_site", "delete_site", "view_site",
    "add_task", "change_task", "delete_task", "view_task",
    "add_taskstate", "change_taskstate", "delete_taskstate", "view_taskstate",
    "add_workflow", "change_workflow", "delete_workflow", "view_workflow",
    "add_workflowcontenttype", "change_workflowcontenttype", "delete_workflowcontenttype", "view_workflowcontenttype",
    "add_workflowpage", "change_workflowpage", "delete_workflowpage", "view_workflowpage",
    "add_workflowstate", "change_workflowstate", "delete_workflowstate", "view_workflowstate",
    "add_workflowtask", "change_workflowtask", "delete_workflowtask", "view_workflowtask",
    "add_redirect", "change_redirect", "delete_redirect", "view_redirect",
    "add_seosettings", "change_seosettings", "delete_seosettings", "view_seosettings"
]

# These must always be included for django-comments-dab
INCLUDED_CODENAMES = [
    "add_blockeduser", "change_blockeduser", "delete_blockeduser", "view_blockeduser",
    "add_blockeduserhistory", "change_blockeduserhistory", "delete_blockeduserhistory", "view_blockeduserhistory",
    "add_comment", "change_comment", "delete_comment", "view_comment",
    "add_flag", "change_flag", "delete_flag", "view_flag",
    "add_flaginstance", "change_flaginstance", "delete_flaginstance", "view_flaginstance",
    "add_follower", "change_follower", "delete_follower", "view_follower",
    "add_reaction", "change_reaction", "delete_reaction", "view_reaction",
    "add_reactioninstance", "change_reactioninstance", "delete_reactioninstance", "view_reactioninstance",
]

class Command(BaseCommand):
    help = 'Assign all allowed permissions to the Tenant group, including comments-dab ones.'

    def handle(self, *args, **kwargs):
        tenant_group, created = Group.objects.get_or_create(name="Tenant")

        if created:
            self.stdout.write("✅ Tenant Group created.")
        else:
            self.stdout.write("ℹ️ Tenant Group already exists. Updating permissions...")

        # Assign all permissions except excluded ones
        allowed_permissions = Permission.objects.exclude(codename__in=EXCLUDED_CODENAMES)
        tenant_group.permissions.clear()
        tenant_group.permissions.add(*allowed_permissions)

        # Assign access_admin if present
        try:
            access_admin = Permission.objects.get(codename="access_admin")
            tenant_group.permissions.add(access_admin)
            self.stdout.write("✅ access_admin added.")
        except Permission.DoesNotExist:
            self.stdout.write("⚠️ access_admin not found.")

        # Assign all required comment permissions
        comment_perms = Permission.objects.filter(content_type__app_label="comment")
        comment_dict = {perm.codename: perm for perm in comment_perms}
        missing = []

        for codename in INCLUDED_CODENAMES:
            perm = comment_dict.get(codename)
            if perm:
                tenant_group.permissions.add(perm)
                # self.stdout.write(f"✅ {codename} added.")
            else:
                missing.append(codename)

        if missing:
            self.stdout.write(f"⚠️ Missing comment permissions: {missing}")
        else:
            self.stdout.write("✅ All comment permissions successfully added.")

        self.stdout.write("🎉 Tenant group permission assignment complete.")
