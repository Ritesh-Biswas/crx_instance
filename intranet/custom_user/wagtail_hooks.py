from wagtail import hooks
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.views.account import BaseSettingsPanel
from wagtail.admin.widgets import AdminDateInput
from wagtail.images.widgets import AdminImageChooser
from django import forms
from .models import UserExtraProfile
from wagtail.admin.widgets import AdminTagWidget


class CustomAccountSettingsForm(WagtailAdminModelForm):
    class Meta:
        model = UserExtraProfile
        fields = ['about', 'cover_photo', 'designation', 'joining_date', 'date_of_birth', 'manager', 'employee_number']
        widgets = {
            'cover_photo': AdminImageChooser(),
            'joining_date': AdminDateInput(),
            'date_of_birth': AdminDateInput(),
            'expertise': AdminTagWidget(),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # Extract request from kwargs
        super().__init__(*args, **kwargs)

        # Exclude current user from manager choices
        if self.instance and self.instance.user:
            self.fields['manager'].queryset = UserExtraProfile.objects.exclude(user=self.instance.user)

        # Define fields to restrict
        restricted_fields = ['designation', 'expertise', 'joining_date', 'manager','employee_number']

        # Check if user is superuser or in "Tenant Groups"
        if self.request and self.request.user:
            user = self.request.user
            is_authorized = user.is_superuser or user.groups.filter(name__in=['Tenant']).exists()

            if not is_authorized:
                # Disable restricted fields for non-authorized users
                for field_name in restricted_fields:
                    if field_name in self.fields:
                        self.fields[field_name].disabled = True
                        self.fields[field_name].required = False  # Prevent validation errors

    def save(self, commit=True):
        # Only save UserExtraProfile fields; skip User fields for non-authorized users
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class CustomAccountSettingsPanel(BaseSettingsPanel):
    name = 'custom'
    title = 'Additional Info'
    order = 500
    form_class = CustomAccountSettingsForm

    def get_form(self):
        instance, created = UserExtraProfile.objects.get_or_create(user=self.request.user)

        kwargs = {'instance': instance, 'request': self.request}
        if self.request.method == 'POST':
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })

        return self.form_class(**kwargs)

    def save_form(self, form):
        form.save()


@hooks.register('register_account_settings_panel')
def register_account_settings_panel(request, user, profile):
    return CustomAccountSettingsPanel(request, user, profile)
