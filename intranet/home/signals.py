from django.db.models.signals import post_save, post_delete, post_migrate, m2m_changed

from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth import get_user_model 
from .models import SubDepartmentPage
from custom_user.models import UserExtraProfile

User = get_user_model() 

@receiver(post_save, sender=SubDepartmentPage)
def create_rbac_groups(sender, instance, created, **kwargs):
    if instance:
        # Create RBAC groups based on SubDepartmentPage instance name
        general_user_group, _ = Group.objects.get_or_create(name=f"{instance.name}_general_user")
        editors_group, _ = Group.objects.get_or_create(name=f"{instance.name}_editors")
        moderators_group, _ = Group.objects.get_or_create(name=f"{instance.name}_moderators")

        # Assign site admins to the created groups
        for admin in instance.site_admins.all():
            admin.groups.add(general_user_group, editors_group, moderators_group)
        for member in instance.members.all():
            member.groups.add(general_user_group)

        # Add Wagtail Admin access permission
        try:
            wagtail_admin_permission = Permission.objects.get(codename="access_admin")
            if not wagtail_admin_permission in editors_group.permissions.all():
                editors_group.permissions.add(wagtail_admin_permission)
            if not wagtail_admin_permission in moderators_group.permissions.all():
                moderators_group.permissions.add(wagtail_admin_permission)
            if not wagtail_admin_permission in general_user_group.permissions.all():
                general_user_group.permissions.add(wagtail_admin_permission)
        except Permission.DoesNotExist:
            print("⚠️ Warning: 'access_admin' permission not found!")

        print(f"✅ RBAC groups and permissions assigned for '{instance.name}' successfully!")

@receiver(post_delete, sender=SubDepartmentPage)
def delete_rbac_groups(sender, instance, **kwargs):
    # Delete RBAC groups based on SubDepartmentPage instance name
    Group.objects.filter(name=f"{instance.name}_general_user").delete()
    Group.objects.filter(name=f"{instance.name}_editors").delete()
    Group.objects.filter(name=f"{instance.name}_moderators").delete()

    print(f"🗑️ RBAC groups for '{instance.name}' deleted successfully!")

@receiver(post_migrate)
def create_default_group(sender, **kwargs):
    # Create default group
    general_user_group, created = Group.objects.get_or_create(name="General User")
    if created:
        print("✅ Default group 'General User' created successfully!")

    try:
        wagtail_admin_permission = Permission.objects.get(codename="access_admin")
        if not wagtail_admin_permission in general_user_group.permissions.all():
            general_user_group.permissions.add(wagtail_admin_permission)
    except Permission.DoesNotExist:
        print("⚠️ Warning: 'access_admin' permission not found!")

    # Assign all users except superusers to the default group
    for user in User.objects.filter(is_superuser=False):
        user.groups.add(general_user_group)
    # print("✅ All non-superuser users assigned to the 'General User' group successfully!")


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


@receiver(post_migrate)
def create_tenant_group_with_all_permissions(sender, **kwargs):
    tenant_group, created = Group.objects.get_or_create(name="Tenant")
    if created:
        print("✅ Tenant Group created successfully!")
    else:
        print("ℹ️ Tenant Group already exists, updating permissions...")

    try:
        # Assign all non-excluded permissions
        allowed_permissions = Permission.objects.exclude(codename__in=EXCLUDED_CODENAMES)
        tenant_group.permissions.clear()
        tenant_group.permissions.add(*allowed_permissions)

        # Add access_admin explicitly
        try:
            wagtail_admin_permission = Permission.objects.get(codename="access_admin")
            tenant_group.permissions.add(wagtail_admin_permission)
            print("✅ 'access_admin' permission added to Tenant group.")
        except Permission.DoesNotExist:
            print("⚠️ Warning: 'access_admin' permission not found!")

        print("✅ Tenant group permissions assigned (excluding special comment ones).")
    except Exception as e:
        print(f"⚠️ Error assigning permissions to Tenant group: {e}")



#This signal is triggered when a user is added to the Tenant group
# and automatically adds them to the Moderators group.
@receiver(m2m_changed, sender=User.groups.through)
def add_moderators_when_tenant_added(sender, instance, action, reverse, pk_set, **kwargs):
    if action == "post_add":
        try:
            tenant_group = Group.objects.get(name="Tenant")
            moderators_group, _ = Group.objects.get_or_create(name="Moderators")

            # Check if the user is added to Tenant group
            if tenant_group.pk in pk_set:
                # Add user to Moderators group
                if moderators_group not in instance.groups.all():
                    instance.groups.add(moderators_group)
                # Set is_staff to True
                if not instance.is_staff:
                    instance.is_staff = True
                    instance.save()
                print(f"✅ User '{instance.username}' was added to 'Tenant' and 'Moderators' groups, is_staff set to True.")

        except Group.DoesNotExist:
            print("⚠️ Tenant group does not exist!")



@receiver(post_migrate)
def create_superuser(sender, **kwargs):
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin@123'
        )
        print("✅ Superuser 'admin' created successfully!")

@receiver(post_save, sender=User)
def assign_general_user_group(sender, instance, created, **kwargs):
    if created and not instance.is_superuser:
        general_user_group, _ = Group.objects.get_or_create(name="General User")
        instance.groups.add(general_user_group)
        print(f"✅ User '{instance.username}' assigned to 'General User' group successfully!")



# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         UserExtraProfile.objects.create(user=instance)

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     if not hasattr(instance, 'userextraprofile'):
#         UserExtraProfile.objects.create(user=instance)
#     instance.userextraprofile.save()

