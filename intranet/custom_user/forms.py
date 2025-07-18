from django import forms
from django.utils.translation import gettext_lazy as _
from wagtail.users.forms import UserEditForm, UserCreationForm
from .models import UserExtraProfile
from taggit.forms import TagField
from django.contrib.auth.models import Group

class CustomUserEditForm(UserEditForm):
    # Existing fields
    
    # New fields from UserExtraProfile
    about = forms.CharField(widget=forms.Textarea, required=False, label=_("About"))
    designation = forms.CharField(max_length=255, required=False, label=_("Designation"))
    joining_date = forms.DateField(required=False, label=_("Joining Date"),widget=forms.DateInput(attrs={'type': 'date'}))
    date_of_birth = forms.DateField(required=False, label=_("Date of Birth"),widget=forms.DateInput(attrs={'type': 'date'}))
    expertise = TagField(required=False, label=_("Expertise"))
    employee_number = forms.CharField(max_length=20, required=False, label=_("Employee Number"))
    manager = forms.ModelChoiceField(
        queryset=UserExtraProfile.objects.all(),
        required=False,
        label=_("Manager")
    )
    is_staff = forms.BooleanField(
        label=_("Staff status"),
        required=False,
        help_text=_("Designates whether the user can log into this admin site.")
    )

    class Meta(UserEditForm.Meta):
        fields = UserEditForm.Meta.fields | {
            "about",
            "designation",
            "joining_date",
            "date_of_birth",
            "expertise",
            "employee_number",
            "manager",
            "is_staff"
        }

    def __init__(self, *args, **kwargs):
        editing_self = kwargs.get('editing_self', False)
        super().__init__(*args, **kwargs)

        # Restrict editing for superuser profiles
        if self.instance and self.instance.is_superuser and not editing_self:
            # Disable all fields to prevent editing by anyone other than the superuser themselves
            for field_name, field in self.fields.items():
                field.disabled = True

        # If this is an existing user, populate the extra profile fields
        if self.instance and hasattr(self.instance, 'userextraprofile'):
            profile = self.instance.userextraprofile
            self.fields['about'].initial = profile.about
            self.fields['designation'].initial = profile.designation
            self.fields['joining_date'].initial = profile.joining_date
            self.fields['date_of_birth'].initial = profile.date_of_birth
            self.fields['expertise'].initial = profile.expertise.all()
            self.fields['employee_number'].initial = profile.employee_number
            self.fields['manager'].initial = profile.manager

        if self.instance and self.instance.pk:
            self.fields['manager'].queryset = UserExtraProfile.objects.exclude(user=self.instance)
            self.fields['manager'].label_from_instance = lambda obj: obj.user.get_full_name() or obj.user.username

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Get or create the user's extra profile
        profile, created = UserExtraProfile.objects.get_or_create(user=user)
        
        # Update the profile fields
        profile.about = self.cleaned_data['about']
        profile.designation = self.cleaned_data['designation']
        profile.joining_date = self.cleaned_data['joining_date']
        profile.date_of_birth = self.cleaned_data['date_of_birth']
        profile.employee_number = self.cleaned_data['employee_number']
        profile.manager = self.cleaned_data['manager']
        
        if commit:
            user.save()
            profile.save()

            self.save_m2m() 
            # Handle the many-to-many field separately
            profile.expertise.set(self.cleaned_data['expertise'])
            
        return user
    



class CustomUserCreationForm(UserCreationForm):
    about = forms.CharField(widget=forms.Textarea, required=False, label=_("About"))
    designation = forms.CharField(max_length=255, required=False, label=_("Designation"))
    joining_date = forms.DateField(required=False, label=_("Joining Date"),widget=forms.DateInput(attrs={'type': 'date'}))
    date_of_birth = forms.DateField(required=False, label=_("Date of Birth"),widget=forms.DateInput(attrs={'type': 'date'}))
    expertise = TagField(required=False, label=_("Expertise"))
    employee_number = forms.CharField(max_length=20, required=False, label=_("Employee Number"))
    manager = forms.ModelChoiceField(
        queryset=UserExtraProfile.objects.all(),
        required=False,
        label=_("Manager")
    )
    is_staff = forms.BooleanField(
        label=_("Staff status"),
        required=False,
        help_text=_("Designates whether the user can log into this admin site.")
    )

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields | {
            "about",
            "designation",
            "joining_date",
            "date_of_birth",
            "expertise",
            "employee_number",
            "manager",
            "is_staff"
        }

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()
            self.save_m2m()
            # Add user to General group by default
            general_group, created = Group.objects.get_or_create(name='General User')
            user.groups.add(general_group)

        profile, created = UserExtraProfile.objects.get_or_create(user=user)

        if 'about' in self.cleaned_data:
            profile.about = self.cleaned_data['about']
            profile.save()
        
        return user