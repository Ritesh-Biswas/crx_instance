from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.images import get_image_model_string
from django.utils.timezone import now
from django.urls import reverse
from taggit.managers import TaggableManager
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserManager(BaseUserManager):
    """
    Model manager for our custom User object, which uses email
    addresses instead of usernames.
    """

    use_in_migrations = True

    def _create_user(self, email, username, password, **extra_fields):
        if not email:
            raise ValueError("Email address must be provided.")
        if not username:
            raise ValueError("Username must be provided.")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, username, password, **extra_fields)

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, username, password, **extra_fields)


class User(AbstractUser):  # type: ignore
    """
    A custom user model, which uses email instead of username as
    the identifier.
    """

    username = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    email = models.EmailField(
        _("email address"),
        unique=True,
        error_messages={
            "unique": _("A user with that email already exists."),
        },
    )

    objects = UserManager()  # type: ignore

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        identifiers = [
            self.get_full_name(),
            self.username,
            self.email,
            f"User_{self.pk}"
        ]
        return next((id for id in identifiers if id), "Unnamed User")


class UserExtraProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    about = models.TextField(blank=True, help_text="Tell us about yourself")
    cover_photo = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name='Cover Photo'
    )
    designation = models.CharField(max_length=255, blank=True, help_text='Your current role or position')
    joining_date = models.DateField(default=now, help_text='Select your joining date')
    date_of_birth = models.DateField(null=True, blank=True, help_text='Select your date of birth')
    expertise = TaggableManager(blank=True)
    employee_number = models.CharField(max_length=20, blank=True, help_text='Your employee number')
    following_users = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='user_followers',
        blank=True
    )

    following_departments = models.ManyToManyField(
        'home.SubDepartmentPage',
        related_name='department_followers',
        blank=True
    )

    def __str__(self):
        if not self.user:
            return f"Unassigned Profile {self.pk}"
        return f"{self.user.get_full_name() or self.user.username or self.user.email or f'User {self.user.pk}'}'s Profile"

    # Helper methods
    def follow_user(self, profile):
        self.following_users.add(profile)

    def unfollow_user(self, profile):
        self.following_users.remove(profile)

    def is_following_user(self, profile):
        return self.following_users.filter(pk=profile.pk).exists()

    def follow_department(self, dept):
        self.following_departments.add(dept)

    def unfollow_department(self, dept):
        self.following_departments.remove(dept)

    def is_following_department(self, dept):
        return self.following_departments.filter(pk=dept.pk).exists()

    def get_absolute_url(self):
        """
        Returns the URL to access a particular user profile instance.
        Uses the username from the associated User model for the URL.
        """
        return reverse('custom_user:profile-detail', args=[self.user.username])

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserExtraProfile for every new user"""
    if created:
        UserExtraProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Ensure the UserExtraProfile is saved when the user is saved"""
    try:
        instance.userextraprofile.save()
    except UserExtraProfile.DoesNotExist:
        # Create profile if it doesn't exist
        UserExtraProfile.objects.create(user=instance)
